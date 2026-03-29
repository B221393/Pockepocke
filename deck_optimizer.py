#!/usr/bin/env python3
"""
deck_optimizer.py – デッキ最適化AI

ポケポケのデッキをシミュレーションに基づいて自動最適化します。
ヒルクライミング法で1枚ずつカードを入れ替え、勝率が向上する構成を探索します。

考慮要素:
  - タイプごとのカード選別 (ポケモンタイプ整合性)
  - HPごとの評価 (アタッカーの耐久力)
  - 特殊効果持ちカードの採用
  - サイラス（アカギ）の使用タイミング
  - EXあり/なしのデッキ方針
  - 先行・後攻両方で戦える構成
  - ベビィポケモンの採用検討

使い方:
    python deck_optimizer.py [オプション]

オプション:
    --deck PATH         最適化するデッキのJSONパス
    --opponents PATH    対戦相手デッキのJSONパス (複数可、カンマ区切り)
    --all-builtin       全組み込みデッキを対戦相手として使用
    -n, --games         1評価あたりの試合数 (デフォルト: 200)
    --iterations        最適化の反復回数 (デフォルト: 50)
    --seed              乱数シード
    --no-ex             EXポケモンを採用しない
    --type TYPE         優先するエネルギータイプ (例: Fire, Water, Psychic)
    --min-hp HP         アタッカーの最小HP (デフォルト: 80)
    --output PATH       最適化済みデッキの保存先JSON
    --verbose           詳細ログを出力

例:
    python deck_optimizer.py --deck decks/darkrai_altaria_deck.json --all-builtin -n 300 --iterations 30
    python deck_optimizer.py --deck decks/mega_charizard_deck.json --no-ex --iterations 20 --verbose
"""

from __future__ import annotations

import argparse
import csv
import json
import random
import sys
from collections import Counter
from copy import deepcopy
from pathlib import Path
from typing import Optional

from simulator import (
    BENCH_MAX,
    HAND_SIZE,
    ActivePokemon,
    Attack,
    Card,
    Game,
    Player,
    SimulationResult,
    load_deck_from_json,
)

DEFAULT_CSV = Path("data/all_cards.csv")
DECK_SIZE = 20
MIN_BASICS = 4     # デッキの最低たねポケモン枚数
MAX_COPIES = 2     # 同名カード最大枚数

BUILTIN_DECKS = [
    Path("decks/mega_heracross_deck.json"),
    Path("decks/darkrai_altaria_deck.json"),
    Path("decks/mega_charizard_deck.json"),
]


# ---------------------------------------------------------------------------
# Card pool loading
# ---------------------------------------------------------------------------

def load_card_pool(
    csv_path: Path = DEFAULT_CSV,
    allowed_types: Optional[list[str]] = None,
    no_ex: bool = False,
    min_hp: int = 0,
) -> list[Card]:
    """
    all_cards.csv から利用可能なカードの一覧を読み込み、Card オブジェクトのリストを返す。

    Parameters
    ----------
    csv_path      : all_cards.csv のパス
    allowed_types : 絞り込みを行うポケモンタイプのリスト (None=全タイプ)
    no_ex         : True の場合 EX ポケモンを除外する
    min_hp        : ポケモンカードの最小HP閾値 (この値未満は除外)
    """
    cards: list[Card] = []
    with open(csv_path, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            card_type = row["card_type"].strip()
            name = row["card_name"].strip()

            is_ex = str(row.get("is_ex", "False")).strip().lower() in ("true", "1", "yes")
            if no_ex and is_ex:
                continue

            is_baby = str(row.get("is_baby", "")).strip().lower() in ("true", "1", "yes")

            if card_type == "Pokemon":
                hp_str = row.get("hp", "")
                hp = int(hp_str) if hp_str.strip() else 0
                if hp < min_hp:
                    continue
                ptype = row.get("pokemon_type", "").strip() or "Colorless"
                if allowed_types and ptype not in allowed_types:
                    continue

                stage_str = row.get("stage", "")
                stage = int(stage_str) if stage_str.strip() else 0
                evolves_from = row.get("evolves_from", "").strip() or None

                attacks: list[Attack] = []
                for prefix in ("attack1_", "attack2_"):
                    ec_str = row.get(f"{prefix}energy_cost", "").strip()
                    dmg_str = row.get(f"{prefix}damage", "").strip()
                    if not ec_str or not dmg_str:
                        continue
                    attacks.append(Attack(
                        energy_cost=int(ec_str),
                        damage=int(dmg_str),
                        coin_flips=int(row.get(f"{prefix}coin_flips", "0").strip() or "0"),
                        effect=row.get(f"{prefix}effect", "").strip(),
                    ))

                cards.append(Card(
                    name=name,
                    card_type="Pokemon",
                    stage=stage,
                    hp=hp,
                    pokemon_type=ptype,
                    evolves_from=evolves_from,
                    attacks=attacks,
                    is_baby=is_baby,
                ))
            elif card_type in ("Item", "Supporter"):
                effect = row.get("trainer_effect", "").strip()
                cards.append(Card(
                    name=name,
                    card_type=card_type,
                    stage=None,
                    hp=None,
                    pokemon_type=None,
                    evolves_from=None,
                    attacks=[],
                    effect=effect,
                ))

    return cards


# ---------------------------------------------------------------------------
# Deck evaluation helpers
# ---------------------------------------------------------------------------

def _evaluate_deck(
    deck_cards: list[Card],
    opponent_decks: list[list[Card]],
    n: int,
    rng: random.Random,
    deck_name: str = "最適化デッキ",
) -> float:
    """
    デッキの平均勝率を計算して返す。
    先行・後攻ランダムで全対戦相手と対戦し、平均勝率を算出する。
    """
    if not opponent_decks:
        return 0.0

    total_wr = 0.0

    for i, opp_cards in enumerate(opponent_decks):
        opp_name = f"相手{i + 1}"
        wins = draws = 0
        total = 0

        for _ in range(n):
            p1 = Player(deck_name, deepcopy(deck_cards))
            p2 = Player(opp_name, deepcopy(opp_cards))
            game = Game(p1, p2, rng, randomize_first_player=True)
            game.setup()
            result = game.play()
            total += 1
            if result == "p1":
                wins += 1
            elif result == "draw":
                draws += 0.5

        wr = (wins + draws) / total if total > 0 else 0.0
        total_wr += wr

    return total_wr / len(opponent_decks)


def _is_valid_deck(deck_cards: list[Card]) -> bool:
    """デッキが有効か検証する（20枚・同名カード最大2枚・たね最低4枚）。"""
    if len(deck_cards) != DECK_SIZE:
        return False
    counts = Counter(c.name for c in deck_cards)
    if any(v > MAX_COPIES for v in counts.values()):
        return False
    basics = [c for c in deck_cards if c.card_type == "Pokemon" and c.stage == 0]
    if len(basics) < MIN_BASICS:
        return False
    return True


# ---------------------------------------------------------------------------
# Mutation strategies
# ---------------------------------------------------------------------------

def _mutate_deck(
    deck_cards: list[Card],
    card_pool: list[Card],
    rng: random.Random,
    preferred_type: Optional[str] = None,
    no_ex: bool = False,
    min_hp: int = 0,
    verbose: bool = False,
) -> list[Card]:
    """
    デッキから1枚ランダムに取り除き、カードプールから別のカードと交換する。
    制約（20枚・同名最大2枚・たね最低4枚）を守った有効なデッキを返す。
    試行が失敗した場合は元のデッキをそのまま返す。
    """
    for _ in range(30):   # 最大30回試行
        candidate = list(deck_cards)

        # 交換候補: ランダムに1枚選ぶ
        idx = rng.randrange(len(candidate))
        removed = candidate[idx]
        del candidate[idx]

        # 交換後のデッキでのカード枚数
        counts = Counter(c.name for c in candidate)

        # カードプールから置換先を選択
        # 同じカードタイプを優先（Pokémon→Pokémon, Item→Item, Supporter→Supporter）
        pool_filtered = [
            c for c in card_pool
            if c.card_type == removed.card_type
            and c.name != removed.name
            and counts.get(c.name, 0) < MAX_COPIES
        ]

        # タイプ整合性: Pokémon の場合は同タイプ優先
        if preferred_type and removed.card_type == "Pokemon":
            type_filtered = [c for c in pool_filtered if c.pokemon_type == preferred_type]
            if type_filtered:
                pool_filtered = type_filtered

        # HP フィルタ: アタッカー候補（stage ≥ 1 または高HP）
        if removed.card_type == "Pokemon" and removed.stage and removed.stage >= 1:
            hp_filtered = [c for c in pool_filtered if (c.hp or 0) >= min_hp]
            if hp_filtered:
                pool_filtered = hp_filtered

        # EX 制限
        if no_ex:
            pool_filtered = [c for c in pool_filtered if not c.name.endswith("ex")]

        if not pool_filtered:
            continue

        # ベビィポケモン採用: Pokémon を交換する場合、10% の確率でベビィポケモンを候補に追加
        baby_pool = [c for c in card_pool if c.is_baby and counts.get(c.name, 0) < MAX_COPIES]
        if (
            removed.card_type == "Pokemon"
            and baby_pool
            and rng.random() < 0.10
        ):
            # 既存フィルタ (タイプ・HP・EX) を尊重しつつベビィポケモンを追加候補として加える
            extra_babies = [c for c in baby_pool if c not in pool_filtered]
            pool_filtered = pool_filtered + extra_babies

        new_card = deepcopy(rng.choice(pool_filtered))
        candidate.insert(idx, new_card)

        if _is_valid_deck(candidate):
            if verbose:
                print(f"    入れ替え: {removed.name} → {new_card.name}")
            return candidate

    return list(deck_cards)   # 有効な変異が見つからなければ元を返す


# ---------------------------------------------------------------------------
# Main optimizer
# ---------------------------------------------------------------------------

class DeckOptimizer:
    """
    ヒルクライミング法によるデッキ最適化クラス。

    各反復で現在のデッキから1枚をランダムに交換し、
    勝率が向上すれば採用するという貪欲法で最良のデッキを探索します。
    """

    def __init__(
        self,
        initial_deck: list[Card],
        opponent_decks: list[list[Card]],
        card_pool: list[Card],
        n_games: int = 200,
        seed: Optional[int] = None,
        preferred_type: Optional[str] = None,
        no_ex: bool = False,
        min_hp: int = 0,
        verbose: bool = False,
    ) -> None:
        self.deck = list(initial_deck)
        self.opponent_decks = opponent_decks
        self.card_pool = card_pool
        self.n_games = n_games
        self.rng = random.Random(seed)
        self.preferred_type = preferred_type
        self.no_ex = no_ex
        self.min_hp = min_hp
        self.verbose = verbose

        # ベースラインの勝率を計算
        self.current_win_rate = _evaluate_deck(
            self.deck, self.opponent_decks, self.n_games, self.rng
        )

    def optimize(self, max_iterations: int = 50) -> list[Card]:
        """
        ヒルクライミング最適化を実行し、最良のデッキを返す。

        Parameters
        ----------
        max_iterations : 最大反復回数

        Returns
        -------
        list[Card]
            勝率が最大になったデッキのカードリスト（20枚）
        """
        best_deck = list(self.deck)
        best_wr = self.current_win_rate

        if self.verbose:
            print(f"初期勝率: {best_wr:.1%}")

        no_improve_streak = 0
        for i in range(1, max_iterations + 1):
            candidate = _mutate_deck(
                self.deck,
                self.card_pool,
                self.rng,
                preferred_type=self.preferred_type,
                no_ex=self.no_ex,
                min_hp=self.min_hp,
                verbose=self.verbose,
            )

            wr = _evaluate_deck(
                candidate, self.opponent_decks, self.n_games, self.rng
            )

            if self.verbose:
                print(f"  反復 {i:3d}/{max_iterations}  勝率: {wr:.1%}  (最良: {best_wr:.1%})")

            if wr > best_wr:
                best_wr = wr
                best_deck = list(candidate)
                self.deck = list(candidate)
                self.current_win_rate = wr
                no_improve_streak = 0
            else:
                no_improve_streak += 1
                # 10連続改善なし → リスタート（局所最適から脱出）
                if no_improve_streak >= 10:
                    self.deck = list(best_deck)
                    no_improve_streak = 0

        return best_deck

    def summary(self, optimized_deck: list[Card]) -> None:
        """最適化結果のサマリーを標準出力へ表示する。"""
        counts = Counter(c.name for c in optimized_deck)
        types = Counter(
            c.pokemon_type for c in optimized_deck
            if c.card_type == "Pokemon" and c.pokemon_type
        )
        ex_count = sum(1 for c in optimized_deck if c.name.endswith("ex"))
        baby_count = sum(1 for c in optimized_deck if c.is_baby)
        basics = [c for c in optimized_deck if c.card_type == "Pokemon" and c.stage == 0]
        supporters = [c for c in optimized_deck if c.card_type == "Supporter"]
        items = [c for c in optimized_deck if c.card_type == "Item"]

        print("\n" + "=" * 60)
        print("■ 最適化デッキ構成")
        print("=" * 60)
        print(f"最終勝率 (推定): {self.current_win_rate:.1%}")
        print(f"EXポケモン: {ex_count} 枚  ベビィポケモン: {baby_count} 枚")
        print(f"タイプ分布: {dict(types)}")
        print(f"たねポケモン: {len(basics)} 枚  サポーター: {len(supporters)} 枚  "
              f"グッズ: {len(items)} 枚")
        print()
        print(f"{'カード名':<28}  {'枚数':>4}  {'種別':<10}  {'HP':>5}  {'タイプ':<12}")
        print("-" * 70)
        for name, cnt in sorted(counts.items(), key=lambda x: (
            next((c.card_type for c in optimized_deck if c.name == x[0]), ""),
            x[0],
        )):
            card = next(c for c in optimized_deck if c.name == name)
            hp_str = str(card.hp) if card.hp else "-"
            ptype = card.pokemon_type or "-"
            baby_mark = "★ベビィ" if card.is_baby else ""
            print(f"{name + baby_mark:<28}  {cnt:>4}  {card.card_type:<10}  "
                  f"{hp_str:>5}  {ptype:<12}")
        print()


def _deck_to_json(deck_cards: list[Card], deck_name: str = "最適化デッキ") -> dict:
    """Card リストをデッキ JSON 形式（cards エントリ付き）に変換する。"""
    counts: dict[str, int] = Counter(c.name for c in deck_cards)
    seen: set[str] = set()
    entries = []
    for card in deck_cards:
        if card.name in seen:
            continue
        seen.add(card.name)
        attacks_data = [
            {
                "name": a.name,
                "energy_cost": a.energy_cost,
                "damage": a.damage,
                **({"coin_flips": a.coin_flips} if a.coin_flips else {}),
                **({"effect": a.effect} if a.effect else {}),
            }
            for a in card.attacks
        ]
        entry: dict = {
            "name": card.name,
            "card_type": card.card_type,
            "stage": card.stage,
            "hp": card.hp,
            "type": card.pokemon_type,
            "evolves_from": card.evolves_from,
            "attacks": attacks_data,
            "count": counts[card.name],
        }
        if card.effect:
            entry["effect"] = card.effect
        if card.is_baby:
            entry["is_baby"] = True
        entries.append(entry)
    return {
        "name": deck_name,
        "description": "deck_optimizer.py によって最適化されたデッキ",
        "reference": "",
        "cards": entries,
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="ポケポケ デッキ最適化AI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--deck", type=Path, required=True, help="最適化するデッキのJSONパス")
    parser.add_argument(
        "--opponents", type=str, default=None,
        help="対戦相手デッキのJSONパス（カンマ区切りで複数指定可）"
    )
    parser.add_argument(
        "--all-builtin", action="store_true",
        help="全組み込みデッキを対戦相手として使用"
    )
    parser.add_argument(
        "-n", "--games", type=int, default=200, metavar="N",
        help="1評価あたりの試合数 (デフォルト: 200)"
    )
    parser.add_argument(
        "--iterations", type=int, default=50, metavar="N",
        help="最適化の反復回数 (デフォルト: 50)"
    )
    parser.add_argument("--seed", type=int, default=None, help="乱数シード")
    parser.add_argument("--no-ex", action="store_true", help="EXポケモンを採用しない")
    parser.add_argument("--type", dest="ptype", default=None, help="優先するエネルギータイプ")
    parser.add_argument("--min-hp", type=int, default=0, help="アタッカーの最小HP")
    parser.add_argument("--output", type=Path, default=None, help="最適化済みデッキのJSON保存先")
    parser.add_argument("--verbose", action="store_true", help="詳細ログを出力")
    args = parser.parse_args(argv)

    # --- Load initial deck ---
    if not args.deck.exists():
        print(f"[ERROR] デッキファイルが見つかりません: {args.deck}", file=sys.stderr)
        return 1
    initial_deck = load_deck_from_json(args.deck)
    deck_meta = json.loads(args.deck.read_text(encoding="utf-8"))
    deck_name = deck_meta.get("name", str(args.deck))

    # --- Load opponent decks ---
    opp_paths: list[Path] = []
    if args.all_builtin:
        opp_paths = [p for p in BUILTIN_DECKS if p != args.deck and p.exists()]
    if args.opponents:
        for p in args.opponents.split(","):
            pp = Path(p.strip())
            if pp.exists():
                opp_paths.append(pp)
            else:
                print(f"[WARN] 対戦相手デッキが見つかりません: {pp}", file=sys.stderr)

    if not opp_paths:
        # デフォルト: 同梱デッキを対戦相手に
        opp_paths = [p for p in BUILTIN_DECKS if p.exists() and p != args.deck]

    if not opp_paths:
        print("[ERROR] 対戦相手デッキが1件も見つかりません。", file=sys.stderr)
        return 1

    opponent_decks = []
    for p in opp_paths:
        try:
            opponent_decks.append(load_deck_from_json(p))
        except Exception as exc:
            print(f"[WARN] {p} の読み込みに失敗: {exc}", file=sys.stderr)

    if not opponent_decks:
        print("[ERROR] 有効な対戦相手デッキがありません。", file=sys.stderr)
        return 1

    # --- Load card pool ---
    csv_path = DEFAULT_CSV
    if not csv_path.exists():
        print(f"[ERROR] カードプールCSVが見つかりません: {csv_path}", file=sys.stderr)
        return 1

    card_pool = load_card_pool(
        csv_path,
        allowed_types=[args.ptype] if args.ptype else None,
        no_ex=args.no_ex,
        min_hp=args.min_hp,
    )
    if not card_pool:
        print("[ERROR] カードプールが空です。フィルタ条件を確認してください。", file=sys.stderr)
        return 1

    # --- Run optimization ---
    print(f"最適化対象デッキ: {deck_name}")
    print(f"対戦相手: {len(opponent_decks)} デッキ  各 {args.games} 試合 × {args.iterations} 反復")
    print(f"カードプール: {len(card_pool)} 種  EX除外: {args.no_ex}  "
          f"優先タイプ: {args.ptype or '指定なし'}")
    print()

    optimizer = DeckOptimizer(
        initial_deck=initial_deck,
        opponent_decks=opponent_decks,
        card_pool=card_pool,
        n_games=args.games,
        seed=args.seed,
        preferred_type=args.ptype,
        no_ex=args.no_ex,
        min_hp=args.min_hp,
        verbose=args.verbose,
    )

    print(f"最適化前の推定勝率: {optimizer.current_win_rate:.1%}")
    optimized = optimizer.optimize(max_iterations=args.iterations)
    print(f"最適化後の推定勝率: {optimizer.current_win_rate:.1%}")

    optimizer.summary(optimized)

    # --- Save output ---
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        output_json = _deck_to_json(optimized, deck_name + "（最適化済み）")
        args.output.write_text(
            json.dumps(output_json, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"[OK] 最適化済みデッキを {args.output} に保存しました。")

    return 0


if __name__ == "__main__":
    sys.exit(main())
