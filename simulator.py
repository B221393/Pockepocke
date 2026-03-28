"""
simulator.py – ポケモンカードゲーム ポケポケ シミュレーター

ポケポケのルール概要:
  - デッキ枚数: 20枚（同名カード最大2枚）
  - 初期手札: 5枚
  - 毎ターン1枚ドロー
  - エネルギーはエネルギーゾーンから毎ターン1個補給（デッキに含まない）
  - バトル場1体 + ベンチ最大3体
  - 相手ポケモンを3体倒した方が勝ち（ポイント制）
  - 手札事故: 初期手札にたねポケモンが1枚もない状態
"""

from __future__ import annotations

import json
import random
from copy import deepcopy
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class Attack:
    energy_cost: int
    damage: int
    name: str = ""          # 技名（省略可能）
    coin_flips: int = 0     # コイントス枚数（0=固定ダメージ, 1+=表ごとにdamage加算）
    effect: str = ""


@dataclass
class Card:
    name: str
    card_type: str          # "Pokemon" | "Trainer" | "Item" | "Supporter"
    stage: Optional[int]    # 0=たね, 1=1進化, 2=2進化  (None for non-Pokemon)
    hp: Optional[int]
    pokemon_type: Optional[str]
    evolves_from: Optional[str]
    attacks: list[Attack]
    effect: str = ""        # For Trainer / Item / Supporter cards


@dataclass
class ActivePokemon:
    """A Card that has been placed in play, tracking damage counters and status."""
    card: Card
    damage: int = 0
    energy: int = 0
    status: str = ""        # "" | "sleep" | "poison" | "burn"
    is_ex: bool = field(init=False)

    def __post_init__(self) -> None:
        self.is_ex = self.card.name.endswith("ex")

    @property
    def remaining_hp(self) -> int:
        return max(0, self.card.hp - self.damage)  # type: ignore[operator]

    @property
    def is_knocked_out(self) -> bool:
        return self.remaining_hp <= 0

    @property
    def best_attack(self) -> Optional[Attack]:
        """Return the highest-damage attack the Pokémon can afford with its energy."""
        usable = [a for a in self.card.attacks if a.energy_cost <= self.energy]
        return max(usable, key=lambda a: a.damage) if usable else None

    @property
    def strongest_attack(self) -> Optional[Attack]:
        """Return the highest-damage attack regardless of energy (for planning)."""
        return max(self.card.attacks, key=lambda a: a.damage) if self.card.attacks else None

    def evolve(self, evolution_card: Card) -> None:
        """Replace this Pokémon's card with its evolution, preserving battle state."""
        self.card = evolution_card
        self.is_ex = evolution_card.name.endswith("ex")


# ---------------------------------------------------------------------------
# Deck loading helpers
# ---------------------------------------------------------------------------

def load_deck_from_json(path: str | Path) -> list[Card]:
    """Parse a deck JSON file into a flat list of Card objects (duplicates expanded)."""
    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    cards: list[Card] = []
    for entry in data["cards"]:
        attacks = [
            Attack(
                name=a.get("name", ""),
                energy_cost=a["energy_cost"],
                damage=a["damage"],
                coin_flips=a.get("coin_flips", 0),
                effect=a.get("effect", ""),
            )
            for a in entry.get("attacks", [])
        ]
        card = Card(
            name=entry["name"],
            card_type=entry["card_type"],
            stage=entry.get("stage"),
            hp=entry.get("hp"),
            pokemon_type=entry.get("type"),
            evolves_from=entry.get("evolves_from"),
            attacks=attacks,
            effect=entry.get("effect", ""),
        )
        for _ in range(entry.get("count", 1)):
            cards.append(deepcopy(card))

    assert len(cards) == 20, (
        f"デッキは20枚でなければなりません（現在 {len(cards)} 枚）: {path}"
    )
    return cards


# ---------------------------------------------------------------------------
# Player / Game state
# ---------------------------------------------------------------------------

WIN_POINTS = 3      # 相手ポケモンを3体倒したら勝利
BENCH_MAX = 3       # ベンチ最大数
HAND_SIZE = 5       # 初期手札枚数
ENERGY_PER_TURN = 1 # ターンごとに補給されるエネルギー量
MAX_TURNS = 50      # 無限ループ防止


class Player:
    """Represents one player with deck, hand, board state, and simple AI."""

    def __init__(self, name: str, deck_cards: list[Card]) -> None:
        self.name = name
        self.deck: list[Card] = deck_cards[:]
        self.hand: list[Card] = []
        self.discard: list[Card] = []
        self.active: Optional[ActivePokemon] = None
        self.bench: list[ActivePokemon] = []
        self.energy_pool: int = 0   # accumulated energy in energy zone
        self.points: int = 0        # KO points scored
        self._supporter_played: bool = False

    # ------------------------------------------------------------------
    # Setup helpers
    # ------------------------------------------------------------------

    def shuffle_deck(self, rng: random.Random) -> None:
        rng.shuffle(self.deck)

    def draw(self, n: int = 1) -> list[Card]:
        drawn = self.deck[:n]
        self.deck = self.deck[n:]
        self.hand.extend(drawn)
        return drawn

    @property
    def has_basic_in_hand(self) -> bool:
        return any(c.card_type == "Pokemon" and c.stage == 0 for c in self.hand)

    def setup_active(self) -> bool:
        """Place the first Basic Pokémon from hand as the Active.  Returns False if none."""
        basics = [c for c in self.hand if c.card_type == "Pokemon" and c.stage == 0]
        if not basics:
            return False
        chosen = basics[0]
        self.hand.remove(chosen)
        self.active = ActivePokemon(card=chosen)
        return True

    # ------------------------------------------------------------------
    # Turn actions (priority-based AI)
    # ------------------------------------------------------------------

    def take_turn(self, opponent: "Player", rng: random.Random) -> Optional[str]:
        """
        Execute a full turn.  Returns the effect string of the attack used, or None.
        Priority order:
          1. Draw a card
          2. Gain energy
          3. Play Trainer / Item cards
          4. Evolve Active and Bench Pokémon
          5. Place Basics onto Bench
          6. Attach energy to Active
          7. Attack
        """
        self._supporter_played = False

        # 1. Draw
        if self.deck:
            self.draw(1)

        # 2. Gain energy
        self.energy_pool += ENERGY_PER_TURN

        # 3. Play items / supporters
        self._play_trainers(rng)

        # 4. Evolve
        self._evolve_pokemon()

        # 5. Place Basics to Bench
        self._place_basics_to_bench()

        # 6. Attach energy to Active (prefer highest-damage attack threshold)
        self._attach_energy()

        # 7. Attack
        return self._attack(opponent, rng)

    def _play_trainers(self, rng: random.Random) -> None:
        for card in self.hand[:]:   # iterate over copy
            if card.card_type == "Item":
                self._apply_item(card, rng)
                self.hand.remove(card)
                self.discard.append(card)
            elif card.card_type == "Supporter" and not self._supporter_played:
                self._apply_supporter(card, rng)
                self.hand.remove(card)
                self.discard.append(card)
                self._supporter_played = True

    def _apply_item(self, card: Card, rng: random.Random) -> None:
        if card.effect == "heal_30" and self.active:
            self.active.damage = max(0, self.active.damage - 30)
        elif card.effect in ("search_basic", "search_any"):
            self._search_deck(card.effect, rng)
        elif card.effect == "boost_damage_30" and self.active:
            # Handled at attack time via bonus stored on active – simplified:
            pass  # damage bonus already modelled in best_attack base damage
        elif card.effect == "rare_candy":
            self._apply_rare_candy()

    def _apply_rare_candy(self) -> None:
        """ふしぎのあめ: Basic Pokémon を Stage 2 に直接進化させる（Stage 1 スキップ）。
        手札にある Stage 2 カードを探し、場にある Basic から進化チェーンが繋がれば進化する。
        """
        in_play = []
        if self.active:
            in_play.append(self.active)
        in_play.extend(self.bench)

        stage2_cards = [c for c in self.hand if c.card_type == "Pokemon" and c.stage == 2]
        all_known = self.deck + self.hand + self.discard

        for slot in in_play:
            if slot.card.stage != 0:
                continue
            for stage2 in stage2_cards:
                # Stage 2 の evolves_from (= Stage 1 の名前) から Stage 1 を検索し、
                # その Stage 1 の evolves_from が現在の Basic と一致するか確認する
                stage1_name = stage2.evolves_from
                chain_exists = any(
                    c.card_type == "Pokemon"
                    and c.stage == 1
                    and c.name == stage1_name
                    and c.evolves_from == slot.card.name
                    for c in all_known
                )
                if chain_exists:
                    slot.evolve(stage2)
                    self.hand.remove(stage2)
                    return

    def _apply_supporter(self, card: Card, _rng: random.Random) -> None:
        if card.effect == "draw_5":
            self.draw(min(5, len(self.deck)))
        elif card.effect == "draw_3_and_bench_supporter":
            self.draw(min(3, len(self.deck)))
        elif card.effect == "discard_opponent_bench":
            pass  # opponent bench manipulation – simplified / skipped for win-rate balance

    def _search_deck(self, effect: str, rng: random.Random) -> None:
        """Move a matching card from deck to hand."""
        candidates = [
            c for c in self.deck
            if (effect == "search_basic" and c.card_type == "Pokemon" and c.stage == 0)
            or effect == "search_any"
        ]
        if candidates:
            chosen = rng.choice(candidates)
            self.deck.remove(chosen)
            self.hand.append(chosen)

    def _evolve_pokemon(self) -> None:
        """Evolve Active and Bench Pokémon if possible."""
        self._try_evolve(self.active)
        for bench_mon in self.bench:
            self._try_evolve(bench_mon)

    def _try_evolve(self, slot: Optional[ActivePokemon]) -> None:
        if slot is None:
            return
        for card in self.hand[:]:
            if (
                card.card_type == "Pokemon"
                and card.stage is not None
                and card.stage > 0
                and card.evolves_from == slot.card.name
            ):
                # Evolve: replace card, keep damage counters and energy
                slot.evolve(card)
                self.hand.remove(card)
                return

    def _place_basics_to_bench(self) -> None:
        for card in self.hand[:]:
            if len(self.bench) >= BENCH_MAX:
                break
            if card.card_type == "Pokemon" and card.stage == 0:
                self.bench.append(ActivePokemon(card=card))
                self.hand.remove(card)

    def _attach_energy(self) -> None:
        if self.active and self.energy_pool > 0:
            self.active.energy += self.energy_pool
            self.energy_pool = 0

    def _attack(self, opponent: "Player", rng: random.Random) -> Optional[str]:
        if self.active is None or opponent.active is None:
            return None
        # Sleep check: sleeping Pokémon cannot attack (50/50 wake chance)
        if self.active.status == "sleep":
            if rng.random() < 0.5:
                self.active.status = ""
            else:
                return None
        attack = self.active.best_attack
        if attack is None:
            return None
        # コイントスがある技: 表の数 × damage を計算する
        if attack.coin_flips > 0:
            heads = sum(1 for _ in range(attack.coin_flips) if rng.random() < 0.5)
            actual_damage = attack.damage * heads
        else:
            actual_damage = attack.damage
        opponent.active.damage += actual_damage
        if opponent.active.is_knocked_out:
            points = 2 if opponent.active.is_ex else 1
            self.points += points
            opponent.discard.append(opponent.active.card)
            opponent.active = None
            # Promote first Bench Pokémon
            if opponent.bench:
                opponent.active = opponent.bench.pop(0)
        if attack.effect == "sleep" and opponent.active:
            opponent.active.status = "sleep"
        return attack.effect


# ---------------------------------------------------------------------------
# Game
# ---------------------------------------------------------------------------

class Game:
    """Run a single game between two players and return the winner's name."""

    def __init__(
        self,
        player1: Player,
        player2: Player,
        rng: random.Random,
    ) -> None:
        self.p1 = player1
        self.p2 = player2
        self.rng = rng

    def setup(self) -> Optional[str]:
        """
        マリガンルール付きセットアップ。
        初期手札にたねポケモンが1枚もない場合は、手札をデッキに戻して
        たねポケモンを引くまでシャッフル＆ドローを繰り返す。
        常に None を返す（手札事故は発生しない）。
        """
        self._deal_opening_hand(self.p1)
        self._deal_opening_hand(self.p2)
        self.p1.setup_active()
        self.p2.setup_active()
        return None

    def _deal_opening_hand(self, player: Player) -> None:
        """たねポケモンが手札に来るまでシャッフル＆ドローを繰り返す（マリガンルール）。
        デッキにたねポケモンが1枚もない場合は即リターン（無限ループ防止）。
        """
        all_cards = player.deck + player.hand
        if not any(c.card_type == "Pokemon" and c.stage == 0 for c in all_cards):
            return  # たねが存在しないデッキはそのままにする
        for _ in range(100):  # 安全上限
            if player.hand:
                player.deck.extend(player.hand)
                player.hand.clear()
            player.shuffle_deck(self.rng)
            player.draw(HAND_SIZE)
            if player.has_basic_in_hand:
                return

    def play(self) -> str:
        """
        Play the game to completion.
        Returns "p1", "p2", or "draw" (timeout).
        """
        # First turn: no attack for the going-first player (Pocket rule)
        first_player, second_player = (self.p1, self.p2)

        for turn in range(1, MAX_TURNS * 2 + 1):
            current, other = (first_player, second_player) if turn % 2 == 1 else (second_player, first_player)

            # Can current player still fight?
            if current.active is None and not current.bench:
                return "p2" if current is self.p1 else "p1"
            if other.active is None and not other.bench:
                return "p1" if current is self.p1 else "p2"

            # First turn of the game: first player draws and sets up but does not attack
            if turn == 1:
                current.energy_pool += ENERGY_PER_TURN
                current._play_trainers(self.rng)
                current._evolve_pokemon()
                current._place_basics_to_bench()
                current._attach_energy()
                continue

            current.take_turn(other, self.rng)

            # Check win condition
            if current.points >= WIN_POINTS:
                return "p1" if current is self.p1 else "p2"
            if other.active is None and not other.bench:
                return "p1" if current is self.p1 else "p2"

        return "draw"


# ---------------------------------------------------------------------------
# Simulation runner
# ---------------------------------------------------------------------------

@dataclass
class SimulationResult:
    deck1_name: str
    deck2_name: str
    total_games: int
    deck1_wins: int
    deck2_wins: int
    draws: int
    deck1_hand_accidents: int
    deck2_hand_accidents: int
    games_with_accident: int

    @property
    def deck1_win_rate(self) -> float:
        valid = self.total_games - self.games_with_accident
        return self.deck1_wins / valid if valid else 0.0

    @property
    def deck2_win_rate(self) -> float:
        valid = self.total_games - self.games_with_accident
        return self.deck2_wins / valid if valid else 0.0

    @property
    def deck1_accident_rate(self) -> float:
        return self.deck1_hand_accidents / self.total_games if self.total_games else 0.0

    @property
    def deck2_accident_rate(self) -> float:
        return self.deck2_hand_accidents / self.total_games if self.total_games else 0.0

    def __str__(self) -> str:
        valid = self.total_games - self.games_with_accident
        return (
            f"=== {self.deck1_name} vs {self.deck2_name} ===\n"
            f"総試合数: {self.total_games}  有効試合数: {valid}\n"
            f"[{self.deck1_name}]  勝利: {self.deck1_wins}  "
            f"勝率: {self.deck1_win_rate:.1%}  "
            f"手札事故率: {self.deck1_accident_rate:.1%}\n"
            f"[{self.deck2_name}]  勝利: {self.deck2_wins}  "
            f"勝率: {self.deck2_win_rate:.1%}  "
            f"手札事故率: {self.deck2_accident_rate:.1%}\n"
            f"引き分け: {self.draws}\n"
        )


def simulate(
    deck1_path: str | Path,
    deck2_path: str | Path,
    n: int = 1000,
    seed: Optional[int] = None,
) -> SimulationResult:
    """
    Run *n* simulated games between the two decks and return aggregated results.

    Parameters
    ----------
    deck1_path : path to first deck JSON
    deck2_path : path to second deck JSON
    n          : number of games to simulate
    seed       : random seed for reproducibility (None = random)
    """
    rng = random.Random(seed)

    deck1_cards = load_deck_from_json(deck1_path)
    deck2_cards = load_deck_from_json(deck2_path)

    deck1_json = json.loads(Path(deck1_path).read_text(encoding="utf-8"))
    deck2_json = json.loads(Path(deck2_path).read_text(encoding="utf-8"))
    deck1_name = deck1_json.get("name", str(deck1_path))
    deck2_name = deck2_json.get("name", str(deck2_path))

    deck1_wins = deck2_wins = draws = 0
    deck1_accidents = deck2_accidents = games_with_accident = 0

    def _had_hand_accident(player: Player) -> bool:
        """Return True if the player's opening hand contained no Basic Pokémon."""
        all_cards = player.hand + ([player.active.card] if player.active else [])
        return all(
            not (c.card_type == "Pokemon" and c.stage == 0) for c in all_cards
        ) and player.active is None

    for _ in range(n):
        p1 = Player(deck1_name, deepcopy(deck1_cards))
        p2 = Player(deck2_name, deepcopy(deck2_cards))
        game = Game(p1, p2, rng)

        accident = game.setup()

        if accident == "accident":
            games_with_accident += 1
            if _had_hand_accident(p1):
                deck1_accidents += 1
            if _had_hand_accident(p2):
                deck2_accidents += 1
            continue

        result = game.play()
        if result == "p1":
            deck1_wins += 1
        elif result == "p2":
            deck2_wins += 1
        else:
            draws += 1

    return SimulationResult(
        deck1_name=deck1_name,
        deck2_name=deck2_name,
        total_games=n,
        deck1_wins=deck1_wins,
        deck2_wins=deck2_wins,
        draws=draws,
        deck1_hand_accidents=deck1_accidents,
        deck2_hand_accidents=deck2_accidents,
        games_with_accident=games_with_accident,
    )
