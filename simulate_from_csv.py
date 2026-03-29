#!/usr/bin/env python3
"""
simulate_from_csv.py – GameWith データCSVを使ったデッキ対戦シミュレーター

GameWith から取得した data/gamewith_decks.csv を読み込み、
各デッキの能力値（HP・ダメージ・エネルギーコスト等）を元に
20枚デッキを自動生成して総当たり対戦シミュレーションを実行します。

使い方:
    python simulate_from_csv.py [オプション]

オプション:
    --csv PATH       デッキCSVパス (デフォルト: data/gamewith_decks.csv)
    -n, --games      試合数 (デフォルト: 1000)
    --seed           乱数シード (省略時はランダム)
    --tier TIER      指定ティアのみ対象 (例: S, A, B)
    --top N          上位N件のデッキのみ対象 (使用率順)
    --output PATH    結果CSVの出力先 (省略時は標準出力のみ)

例:
    # Sランクデッキ同士を10000回対戦
    python simulate_from_csv.py --tier S -n 10000

    # 全デッキの総当たり（上位5件）
    python simulate_from_csv.py --top 5 -n 2000

    # 結果をCSVに保存
    python simulate_from_csv.py -n 1000 --output results/simulation_results.csv
"""

from __future__ import annotations

import argparse
import csv
import random
import sys
from copy import deepcopy
from dataclasses import dataclass, field
from itertools import combinations
from pathlib import Path

from simulator import (
    ActivePokemon,
    Attack,
    Card,
    Game,
    Player,
    SimulationResult,
)

DEFAULT_CSV = Path("data/gamewith_decks.csv")
DECK_SIZE = 20


# ---------------------------------------------------------------------------
# CSV row → deck builder
# ---------------------------------------------------------------------------

@dataclass
class DeckSpec:
    """Parsed row from gamewith_decks.csv, used to build a simulated 20-card deck."""
    deck_name: str
    tier: str
    usage_rate: float
    win_rate: float
    main_pokemon: str
    energy_type: str
    hp: int
    damage: int
    energy_cost: int
    is_ex: bool
    has_evolution: bool
    deck_style: str
    description: str

    def to_card_list(self) -> list[Card]:
        """
        Generate a representative 20-card deck from the deck spec.

        Layout (20 cards total, max 2 copies each):
          2 × メインアタッカー (たね or 進化先)
          2 × たねポケモン (進化ある場合は進化元)
          2 × サブアタッカー
          2 × たねポケモン (サブ)
          2 × はかせのてがみ (draw_5 supporter)
          2 × モンスターボール (search_basic item)
          2 × スーパーボール (search_any item)
          2 × きずぐすり (heal_30 item)
          2 × まけんきハチマキ (boost_damage_30 item)
          2 × サポーターカード (draw_3 supporter)
        """
        cards: list[Card] = []

        # --- Main attacker ---
        main_name = self.main_pokemon
        main_stage = 1 if self.has_evolution else 0

        if self.has_evolution:
            base_name = main_name.replace("ex", "").replace("メガ", "").strip()
            main_evolves_from: str | None = f"{base_name}（たね）"
        else:
            main_evolves_from = None

        main_attack = Attack(
            name="メインわざ",
            energy_cost=self.energy_cost,
            damage=self.damage,
            effect="sleep" if self.deck_style == "コントロール" else "",
        )

        main_card = Card(
            name=main_name,
            card_type="Pokemon",
            stage=main_stage,
            hp=self.hp,
            pokemon_type=self.energy_type,
            evolves_from=main_evolves_from,
            attacks=[main_attack],
        )
        cards.extend([deepcopy(main_card), deepcopy(main_card)])

        # --- Basic Pokémon (always 4 basic slots to ensure ≥6 basics total) ---
        basic_name = main_evolves_from if self.has_evolution else f"{main_name}B"
        basic_hp = max(50, self.hp // 2)
        basic_dmg = max(10, self.damage // 4)

        basic_card = Card(
            name=basic_name,
            card_type="Pokemon",
            stage=0,
            hp=basic_hp,
            pokemon_type=self.energy_type,
            evolves_from=None,
            attacks=[Attack(name="たいあたり", energy_cost=1, damage=basic_dmg)],
        )
        cards.extend([deepcopy(basic_card), deepcopy(basic_card)])

        # Second basic (different name, stage 0) to reach 6 basics
        basic2_card = Card(
            name=f"サブたねポケモン（{self.energy_type}）",
            card_type="Pokemon",
            stage=0,
            hp=max(60, self.hp // 3 * 2),
            pokemon_type=self.energy_type,
            evolves_from=None,
            attacks=[
                Attack(
                    name="サブわざ",
                    energy_cost=max(1, self.energy_cost - 1),
                    damage=max(20, self.damage // 2),
                )
            ],
        )
        cards.extend([deepcopy(basic2_card), deepcopy(basic2_card)])

        # Third basic (another sub for bench depth when has_evolution)
        basic3_card = Card(
            name=f"ベンチたねポケモン（{self.energy_type}）",
            card_type="Pokemon",
            stage=0,
            hp=max(50, self.hp // 3),
            pokemon_type=self.energy_type,
            evolves_from=None,
            attacks=[
                Attack(
                    name="ひっかく",
                    energy_cost=1,
                    damage=max(10, self.damage // 5),
                )
            ],
        )
        cards.extend([deepcopy(basic3_card), deepcopy(basic3_card)])

        # --- Trainer cards (12 cards, total = 8 Pokemon + 12 Trainers = 20) ---
        trainer_templates: list[tuple[str, str, str]] = [
            ("はかせのてがみ", "Supporter", "draw_5"),
            ("はかせのてがみ", "Supporter", "draw_5"),
            ("セレナ", "Supporter", "draw_3_and_bench_supporter"),
            ("セレナ", "Supporter", "draw_3_and_bench_supporter"),
            ("モンスターボール", "Item", "search_basic"),
            ("モンスターボール", "Item", "search_basic"),
            ("スーパーボール", "Item", "search_any"),
            ("スーパーボール", "Item", "search_any"),
            ("きずぐすり", "Item", "heal_30"),
            ("きずぐすり", "Item", "heal_30"),
            ("まけんきハチマキ", "Item", "boost_damage_30"),
            ("まけんきハチマキ", "Item", "boost_damage_30"),
        ]
        for name, card_type, effect in trainer_templates:
            cards.append(
                Card(
                    name=name,
                    card_type=card_type,
                    stage=None,
                    hp=None,
                    pokemon_type=None,
                    evolves_from=None,
                    attacks=[],
                    effect=effect,
                )
            )

        assert len(cards) == DECK_SIZE, f"デッキ枚数エラー: {len(cards)} 枚 ({self.deck_name})"
        return cards


def load_deck_specs(csv_path: Path) -> list[DeckSpec]:
    """Read gamewith_decks.csv and return a list of DeckSpec objects."""
    specs: list[DeckSpec] = []
    with open(csv_path, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                spec = DeckSpec(
                    deck_name=row["deck_name"].strip(),
                    tier=row["tier"].strip(),
                    usage_rate=float(row["usage_rate"] or 0),
                    win_rate=float(row["win_rate"] or 0),
                    main_pokemon=row["main_pokemon"].strip(),
                    energy_type=row["energy_type"].strip() or "Colorless",
                    hp=int(row["main_pokemon_hp"] or 100),
                    damage=int(row["main_attack_damage"] or 60),
                    energy_cost=int(row["main_attack_energy_cost"] or 2),
                    is_ex=str(row["is_ex"]).strip().lower() in ("true", "1", "yes"),
                    has_evolution=str(row["has_evolution"]).strip().lower() in ("true", "1", "yes"),
                    deck_style=row["deck_style"].strip() or "バランス",
                    description=row["description"].strip(),
                )
                specs.append(spec)
            except (KeyError, ValueError) as exc:
                print(f"[WARN] 行スキップ: {exc} ({row})", file=sys.stderr)
    return specs


# ---------------------------------------------------------------------------
# Simulation helpers
# ---------------------------------------------------------------------------

@dataclass
class CsvSimResult:
    deck1: DeckSpec
    deck2: DeckSpec
    sim: SimulationResult

    def to_csv_row(self) -> dict:
        return {
            "deck1_name": self.deck1.deck_name,
            "deck1_tier": self.deck1.tier,
            "deck1_usage_rate": self.deck1.usage_rate,
            "deck2_name": self.deck2.deck_name,
            "deck2_tier": self.deck2.tier,
            "deck2_usage_rate": self.deck2.usage_rate,
            "total_games": self.sim.total_games,
            "valid_games": self.sim.total_games - self.sim.games_with_accident,
            "deck1_wins": self.sim.deck1_wins,
            "deck2_wins": self.sim.deck2_wins,
            "draws": self.sim.draws,
            "deck1_win_rate_pct": f"{self.sim.deck1_win_rate * 100:.1f}",
            "deck2_win_rate_pct": f"{self.sim.deck2_win_rate * 100:.1f}",
            "deck1_accident_rate_pct": f"{self.sim.deck1_accident_rate * 100:.1f}",
            "deck2_accident_rate_pct": f"{self.sim.deck2_accident_rate * 100:.1f}",
            "first_player_win_rate_pct": f"{self.sim.first_player_win_rate * 100:.1f}",
            "second_player_win_rate_pct": f"{self.sim.second_player_win_rate * 100:.1f}",
        }


def _simulate_pair(
    spec1: DeckSpec,
    spec2: DeckSpec,
    n: int,
    rng: random.Random,
) -> SimulationResult:
    """Run n games between two DeckSpec objects and return results."""
    deck1_cards = spec1.to_card_list()
    deck2_cards = spec2.to_card_list()

    deck1_wins = deck2_wins = draws = 0
    deck1_accidents = deck2_accidents = games_with_accident = 0
    first_player_wins = second_player_wins = p1_first_count = 0

    def _had_hand_accident(player: Player) -> bool:
        all_cards = player.hand + ([player.active.card] if player.active else [])
        return all(
            not (c.card_type == "Pokemon" and c.stage == 0) for c in all_cards
        ) and player.active is None

    for _ in range(n):
        p1 = Player(spec1.deck_name, deepcopy(deck1_cards))
        p2 = Player(spec2.deck_name, deepcopy(deck2_cards))
        game = Game(p1, p2, rng, randomize_first_player=True)

        # setup returns (p1_accident, p2_accident)
        a1, a2 = game.setup()

        if a1 or a2:
            games_with_accident += 1
            if a1: deck1_accidents += 1
            if a2: deck2_accidents += 1
            continue

        result = game.play()

        # Track first/second player advantage
        p1_went_first = (game._first_player is p1)
        if p1_went_first:
            p1_first_count += 1
        if result == "p1":
            deck1_wins += 1
            if p1_went_first:
                first_player_wins += 1
            else:
                second_player_wins += 1
        elif result == "p2":
            deck2_wins += 1
            if p1_went_first:
                second_player_wins += 1
            else:
                first_player_wins += 1
        else:
            draws += 1

    return SimulationResult(
        deck1_name=spec1.deck_name,
        deck2_name=spec2.deck_name,
        total_games=n,
        deck1_wins=deck1_wins,
        deck2_wins=deck2_wins,
        draws=draws,
        deck1_hand_accidents=deck1_accidents,
        deck2_hand_accidents=deck2_accidents,
        games_with_accident=games_with_accident,
        first_player_wins=first_player_wins,
        second_player_wins=second_player_wins,
        p1_first_count=p1_first_count,
    )


def _print_summary_table(results: list[CsvSimResult], specs: list[DeckSpec]) -> None:
    """Print a win-rate matrix and aggregated ranking."""
    print("\n" + "=" * 70)
    print("■ デッキ総合勝率ランキング（全対戦の平均）")
    print("=" * 70)

    # Aggregate win rate per deck across all matchups
    win_totals: dict[str, list[float]] = {s.deck_name: [] for s in specs}
    for r in results:
        win_totals[r.deck1.deck_name].append(r.sim.deck1_win_rate)
        win_totals[r.deck2.deck_name].append(r.sim.deck2_win_rate)

    ranking = sorted(
        [(name, sum(wrs) / len(wrs) if wrs else 0.0) for name, wrs in win_totals.items()],
        key=lambda x: -x[1],
    )

    print(f"{'順位':>4}  {'デッキ名':<30}  {'ティア':>5}  {'平均勝率':>8}  {'使用率':>6}")
    print("-" * 70)
    tier_map = {s.deck_name: s.tier for s in specs}
    usage_map = {s.deck_name: s.usage_rate for s in specs}
    for rank, (name, avg_wr) in enumerate(ranking, 1):
        tier = tier_map.get(name, "?")
        usage = usage_map.get(name, 0.0)
        print(f"{rank:>4}  {name:<30}  {tier:>5}  {avg_wr:>7.1%}  {usage:>5.1f}%")

    print()


def _write_results_csv(results: list[CsvSimResult], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "deck1_name", "deck1_tier", "deck1_usage_rate",
        "deck2_name", "deck2_tier", "deck2_usage_rate",
        "total_games", "valid_games",
        "deck1_wins", "deck2_wins", "draws",
        "deck1_win_rate_pct", "deck2_win_rate_pct",
        "deck1_accident_rate_pct", "deck2_accident_rate_pct",
        "first_player_win_rate_pct", "second_player_win_rate_pct",
    ]
    with open(out_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for r in results:
            writer.writerow(r.to_csv_row())
    print(f"[OK] 結果を {out_path} に保存しました。")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="GameWith CSVデータを使ったポケポケ対戦シミュレーター",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--csv", type=Path, default=DEFAULT_CSV, help="デッキCSVパス")
    parser.add_argument("-n", "--games", type=int, default=1000, metavar="N", help="試合数")
    parser.add_argument("--seed", type=int, default=None, help="乱数シード")
    parser.add_argument("--tier", type=str, default=None, help="フィルタするティア (S/A/B/C)")
    parser.add_argument("--top", type=int, default=None, metavar="N", help="使用率上位N件")
    parser.add_argument("--output", type=Path, default=None, help="結果CSVの出力先")
    args = parser.parse_args(argv)

    # Load specs
    if not args.csv.exists():
        print(
            f"[ERROR] {args.csv} が見つかりません。\n"
            "  まず fetch_gamewith.py を実行してデータを取得してください:\n"
            "    python fetch_gamewith.py",
            file=sys.stderr,
        )
        return 1

    specs = load_deck_specs(args.csv)
    if not specs:
        print("[ERROR] CSVにデッキデータが見つかりませんでした。", file=sys.stderr)
        return 1

    # Filter
    if args.tier:
        specs = [s for s in specs if s.tier.upper() == args.tier.upper()]
        if not specs:
            print(f"[ERROR] ティア '{args.tier}' のデッキが見つかりません。", file=sys.stderr)
            return 1

    # Sort by usage rate and take top N
    specs.sort(key=lambda s: -s.usage_rate)
    if args.top:
        specs = specs[: args.top]

    if len(specs) < 2:
        print("[ERROR] 対戦させるデッキが2件以上必要です。", file=sys.stderr)
        return 1

    rng = random.Random(args.seed)
    pairs = list(combinations(specs, 2))

    print(f"データソース: {args.csv}  ({len(specs)} デッキ)")
    print(f"対戦組み合わせ: {len(pairs)} 件  各 {args.games} 試合\n")

    results: list[CsvSimResult] = []
    for spec1, spec2 in pairs:
        sim = _simulate_pair(spec1, spec2, args.games, rng)
        results.append(CsvSimResult(deck1=spec1, deck2=spec2, sim=sim))
        print(sim)

    _print_summary_table(results, specs)

    if args.output:
        _write_results_csv(results, args.output)

    return 0


if __name__ == "__main__":
    sys.exit(main())
