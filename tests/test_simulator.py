"""
tests/test_simulator.py – ポケポケシミュレーターのユニットテスト
"""

from __future__ import annotations

import json
import random
from copy import deepcopy
from pathlib import Path

import pytest

from simulator import (
    HAND_SIZE,
    WIN_POINTS,
    ActivePokemon,
    Attack,
    Card,
    Game,
    Player,
    SimulationResult,
    load_deck_from_json,
    simulate,
)

DECKS_DIR = Path(__file__).parent.parent / "decks"

HERACROSS_DECK = DECKS_DIR / "mega_heracross_deck.json"
DARKRAI_DECK = DECKS_DIR / "darkrai_altaria_deck.json"
CHARIZARD_DECK = DECKS_DIR / "mega_charizard_deck.json"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_basic_card(name: str = "テスト", hp: int = 60, damage: int = 30) -> Card:
    return Card(
        name=name,
        card_type="Pokemon",
        stage=0,
        hp=hp,
        pokemon_type="Colorless",
        evolves_from=None,
        attacks=[Attack(name="たいあたり", energy_cost=1, damage=damage)],
    )


def _minimal_deck(basic_name: str = "テスト", hp: int = 60, damage: int = 30) -> list[Card]:
    """Create a valid 20-card deck with 2 basics and 18 Item cards."""
    basic = _make_basic_card(basic_name, hp, damage)
    item = Card(
        name="きずぐすり",
        card_type="Item",
        stage=None,
        hp=None,
        pokemon_type=None,
        evolves_from=None,
        attacks=[],
        effect="heal_30",
    )
    return [deepcopy(basic) for _ in range(2)] + [deepcopy(item) for _ in range(18)]


# ---------------------------------------------------------------------------
# Deck JSON tests
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("deck_path", [HERACROSS_DECK, DARKRAI_DECK, CHARIZARD_DECK])
def test_deck_json_loads_correctly(deck_path: Path) -> None:
    """Each deck JSON must load to exactly 20 Card objects."""
    cards = load_deck_from_json(deck_path)
    assert len(cards) == 20


@pytest.mark.parametrize("deck_path", [HERACROSS_DECK, DARKRAI_DECK, CHARIZARD_DECK])
def test_deck_json_has_at_least_one_basic(deck_path: Path) -> None:
    """Every deck must contain at least two Basic Pokémon to avoid near-certain accidents."""
    cards = load_deck_from_json(deck_path)
    basics = [c for c in cards if c.card_type == "Pokemon" and c.stage == 0]
    assert len(basics) >= 2, "デッキにたねポケモンが不足しています（最低2枚必要）"


@pytest.mark.parametrize("deck_path", [HERACROSS_DECK, DARKRAI_DECK, CHARIZARD_DECK])
def test_deck_json_max_two_copies(deck_path: Path) -> None:
    """No card name should appear more than 2 times (Pocket rules)."""
    cards = load_deck_from_json(deck_path)
    from collections import Counter
    counts = Counter(c.name for c in cards)
    for name, count in counts.items():
        assert count <= 2, f"'{name}' が {count} 枚含まれています（最大2枚）"


@pytest.mark.parametrize("deck_path", [HERACROSS_DECK, DARKRAI_DECK, CHARIZARD_DECK])
def test_deck_json_structure(deck_path: Path) -> None:
    """Deck JSON must have 'name', 'description', 'reference', and 'cards' fields."""
    data = json.loads(deck_path.read_text(encoding="utf-8"))
    assert "name" in data
    assert "description" in data
    assert "reference" in data
    assert "cards" in data


# ---------------------------------------------------------------------------
# Deck / shuffle / draw tests
# ---------------------------------------------------------------------------

def test_shuffle_changes_order() -> None:
    """Shuffling a deck should (with overwhelming probability) change card order."""
    rng = random.Random(42)
    deck_cards = _minimal_deck()
    player = Player("test", deck_cards)
    original_names = [c.name for c in player.deck]
    player.shuffle_deck(rng)
    # Shuffle of a deck with both "テスト" and "きずぐすり" changes order
    shuffled_names = [c.name for c in player.deck]
    assert shuffled_names != original_names


def test_draw_reduces_deck_and_fills_hand() -> None:
    player = Player("test", _minimal_deck())
    assert len(player.deck) == 20
    assert len(player.hand) == 0
    player.draw(HAND_SIZE)
    assert len(player.hand) == HAND_SIZE
    assert len(player.deck) == 20 - HAND_SIZE


def test_draw_does_not_exceed_deck_size() -> None:
    player = Player("test", _minimal_deck())
    player.draw(25)   # More than 20 — should draw all available
    assert len(player.hand) == 20
    assert len(player.deck) == 0


# ---------------------------------------------------------------------------
# Hand accident detection tests
# ---------------------------------------------------------------------------

def test_has_basic_in_hand_true() -> None:
    player = Player("test", _minimal_deck())
    player.draw(HAND_SIZE)
    # _minimal_deck has 2 basics; statistically very likely to draw one in 5
    # Force it by injecting a basic at the start of the deck
    player2 = Player("test2", [_make_basic_card()] + [
        Card("きずぐすり", "Item", None, None, None, None, [], "heal_30")
        for _ in range(19)
    ])
    player2.draw(1)
    assert player2.has_basic_in_hand is True


def test_has_basic_in_hand_false_when_only_trainers() -> None:
    item = Card("きずぐすり", "Item", None, None, None, None, [], "heal_30")
    player = Player("test", [deepcopy(item) for _ in range(20)])
    player.draw(HAND_SIZE)
    assert player.has_basic_in_hand is False


def test_setup_active_fails_without_basics() -> None:
    item = Card("きずぐすり", "Item", None, None, None, None, [], "heal_30")
    player = Player("test", [deepcopy(item) for _ in range(20)])
    player.draw(HAND_SIZE)
    result = player.setup_active()
    assert result is False
    assert player.active is None


def test_setup_active_succeeds_with_basic() -> None:
    deck = [_make_basic_card()] + [
        Card("きずぐすり", "Item", None, None, None, None, [], "heal_30")
        for _ in range(19)
    ]
    player = Player("test", deck)
    player.draw(HAND_SIZE)
    result = player.setup_active()
    assert result is True
    assert player.active is not None
    assert player.active.card.stage == 0


# ---------------------------------------------------------------------------
# ActivePokemon tests
# ---------------------------------------------------------------------------

def test_active_pokemon_remaining_hp() -> None:
    card = _make_basic_card(hp=100)
    ap = ActivePokemon(card=card)
    assert ap.remaining_hp == 100
    ap.damage = 40
    assert ap.remaining_hp == 60


def test_active_pokemon_knocked_out() -> None:
    card = _make_basic_card(hp=60)
    ap = ActivePokemon(card=card)
    ap.damage = 60
    assert ap.is_knocked_out is True
    ap.damage = 50
    assert ap.is_knocked_out is False


def test_active_pokemon_best_attack_requires_energy() -> None:
    card = _make_basic_card(damage=30)
    ap = ActivePokemon(card=card)
    ap.energy = 0
    assert ap.best_attack is None
    ap.energy = 1
    assert ap.best_attack is not None
    assert ap.best_attack.damage == 30


def test_active_pokemon_is_ex_flag() -> None:
    ex_card = Card("リザードンex", "Pokemon", 1, 150, "Fire", "リザードン", [])
    non_ex_card = _make_basic_card()
    assert ActivePokemon(card=ex_card).is_ex is True
    assert ActivePokemon(card=non_ex_card).is_ex is False


# ---------------------------------------------------------------------------
# Full game tests
# ---------------------------------------------------------------------------

def _make_game(hp1: int = 60, dmg1: int = 30, hp2: int = 60, dmg2: int = 30) -> Game:
    deck1 = _minimal_deck("ポケモンA", hp1, dmg1)
    deck2 = _minimal_deck("ポケモンB", hp2, dmg2)
    rng = random.Random(0)
    p1 = Player("P1", deck1)
    p2 = Player("P2", deck2)
    return Game(p1, p2, rng)


def test_game_setup_places_active() -> None:
    game = _make_game()
    accident = game.setup()
    assert accident is None
    assert game.p1.active is not None
    assert game.p2.active is not None


def test_game_completes_and_returns_winner() -> None:
    game = _make_game()
    game.setup()
    result = game.play()
    assert result in ("p1", "p2", "draw")


def test_stronger_deck_wins_more_often() -> None:
    """A deck with double the HP should win more than 60 % of *valid* (non-accident) games."""
    wins_strong = 0
    valid_games = 0
    n = 300
    rng = random.Random(42)
    for _ in range(n):
        deck_strong = _minimal_deck("強いポケモン", hp=120, damage=30)
        deck_weak = _minimal_deck("弱いポケモン", hp=60, damage=30)
        p1 = Player("Strong", deck_strong)
        p2 = Player("Weak", deck_weak)
        g = Game(p1, p2, rng)
        if g.setup() is None:
            valid_games += 1
            if g.play() == "p1":
                wins_strong += 1
    assert valid_games > 0, "有効試合が1件もありませんでした"
    assert wins_strong / valid_games > 0.60


def test_win_points_threshold() -> None:
    """Players start with 0 points; WIN_POINTS is 3."""
    game = _make_game()
    assert game.p1.points == 0
    assert game.p2.points == 0
    assert WIN_POINTS == 3


# ---------------------------------------------------------------------------
# Simulation runner tests
# ---------------------------------------------------------------------------

def test_simulate_returns_result_object() -> None:
    result = simulate(HERACROSS_DECK, DARKRAI_DECK, n=50, seed=1)
    assert isinstance(result, SimulationResult)
    assert result.total_games == 50


def test_simulate_win_rates_sum_to_one() -> None:
    result = simulate(HERACROSS_DECK, CHARIZARD_DECK, n=100, seed=2)
    valid = result.total_games - result.games_with_accident
    if valid > 0:
        total_decided = result.deck1_wins + result.deck2_wins + result.draws
        assert total_decided == valid


def test_simulate_accident_rate_in_range() -> None:
    result = simulate(DARKRAI_DECK, CHARIZARD_DECK, n=500, seed=3)
    assert 0.0 <= result.deck1_accident_rate <= 1.0
    assert 0.0 <= result.deck2_accident_rate <= 1.0


def test_simulate_all_three_decks() -> None:
    """Smoke-test all three deck matchups."""
    pairs = [
        (HERACROSS_DECK, DARKRAI_DECK),
        (HERACROSS_DECK, CHARIZARD_DECK),
        (DARKRAI_DECK, CHARIZARD_DECK),
    ]
    for d1, d2 in pairs:
        result = simulate(d1, d2, n=50, seed=0)
        assert result.total_games == 50
        assert result.deck1_wins + result.deck2_wins + result.draws + result.games_with_accident == 50


def test_simulate_seed_is_reproducible() -> None:
    r1 = simulate(HERACROSS_DECK, DARKRAI_DECK, n=100, seed=42)
    r2 = simulate(HERACROSS_DECK, DARKRAI_DECK, n=100, seed=42)
    assert r1.deck1_wins == r2.deck1_wins
    assert r1.deck2_wins == r2.deck2_wins


# ---------------------------------------------------------------------------
# Hand accident rate (dedicated test)
# ---------------------------------------------------------------------------

def test_first_turn_hand_accident_rate_is_low_for_valid_decks() -> None:
    """
    For decks with 6 Basic Pokémon (as all 3 builtin decks have),
    the probability of drawing NO basic in a 5-card opening hand should be low.
    Hypergeometric: P(0 basics in 5 from 20 with 6 basics) ≈ 12.9%
    We check that the simulated rate stays within a generous band (< 20%).
    """
    result = simulate(HERACROSS_DECK, DARKRAI_DECK, n=2000, seed=7)
    # Check each deck's accident rate individually
    assert result.deck1_accident_rate < 0.20, (
        f"デッキ1の手札事故率が高すぎます: {result.deck1_accident_rate:.1%} (期待値 < 20%)"
    )
    assert result.deck2_accident_rate < 0.20, (
        f"デッキ2の手札事故率が高すぎます: {result.deck2_accident_rate:.1%} (期待値 < 20%)"
    )


# ---------------------------------------------------------------------------
# Mulligan rule tests
# ---------------------------------------------------------------------------

def test_mulligan_guarantees_basic_in_hand() -> None:
    """マリガンルール: デッキにたねポケモンが1枚しかなくても必ず手札に来る。"""
    # Deck with only 1 Basic, 19 Items
    basic = _make_basic_card("たねポケモン", hp=60)
    item = Card("きずぐすり", "Item", None, None, None, None, [], "heal_30")
    deck = [deepcopy(basic)] + [deepcopy(item) for _ in range(19)]
    rng = random.Random(99)
    for _ in range(50):
        p1 = Player("P1", deepcopy(deck))
        p2 = Player("P2", _minimal_deck())
        game = Game(p1, p2, rng)
        result = game.setup()
        assert result is None, "setup() should always return None with mulligan rule"
        assert game.p1.active is not None, "Active should always be set after setup"
        assert game.p1.active.card.stage == 0


def test_mulligan_no_accident_games() -> None:
    """マリガンルール適用後は games_with_accident が必ず 0 になる。"""
    result = simulate(HERACROSS_DECK, DARKRAI_DECK, n=200, seed=11)
    assert result.games_with_accident == 0, (
        f"マリガンルール有効時は事故ゲームは0件のはず: {result.games_with_accident}"
    )
    assert result.deck1_wins + result.deck2_wins + result.draws == result.total_games


def test_mulligan_all_games_played() -> None:
    """マリガンルールにより、全試合が有効試合として進行する。"""
    n = 100
    result = simulate(DARKRAI_DECK, CHARIZARD_DECK, n=n, seed=22)
    valid = result.total_games - result.games_with_accident
    assert valid == n
    assert result.deck1_wins + result.deck2_wins + result.draws == n


# ---------------------------------------------------------------------------
# Attack name optional tests
# ---------------------------------------------------------------------------

def test_attack_name_defaults_to_empty_string() -> None:
    """Attack.name のデフォルト値は空文字列。"""
    attack = Attack(energy_cost=1, damage=30)
    assert attack.name == ""


def test_attack_without_name_still_works_in_game() -> None:
    """技名なしの Attack を持つデッキでゲームが正常に進行する。"""
    basic = Card(
        name="なまえなし",
        card_type="Pokemon",
        stage=0,
        hp=60,
        pokemon_type="Colorless",
        evolves_from=None,
        attacks=[Attack(energy_cost=1, damage=30)],  # name 省略
    )
    item = Card("きずぐすり", "Item", None, None, None, None, [], "heal_30")
    deck = [deepcopy(basic) for _ in range(2)] + [deepcopy(item) for _ in range(18)]
    rng = random.Random(5)
    p1 = Player("P1", deepcopy(deck))
    p2 = Player("P2", deepcopy(deck))
    game = Game(p1, p2, rng)
    game.setup()
    result = game.play()
    assert result in ("p1", "p2", "draw")


# ---------------------------------------------------------------------------
# Coin flip attack tests
# ---------------------------------------------------------------------------

def test_coin_flip_attack_zero_damage_on_all_tails() -> None:
    """コイントス技: 全部裏ならダメージ0。"""
    rng = random.Random()
    # Force all tails by patching rng.random
    rng.random = lambda: 0.9  # always > 0.5 → tails
    attacker_card = _make_basic_card("コイン技", hp=60, damage=40)
    attacker_card.attacks[0].coin_flips = 1
    ap = ActivePokemon(card=attacker_card)
    ap.energy = 10

    defender_card = _make_basic_card("まと", hp=100, damage=10)
    defender = ActivePokemon(card=defender_card)

    p_atk = Player("A", [deepcopy(attacker_card)])
    p_def = Player("D", [deepcopy(defender_card)])
    p_atk.active = ap
    p_def.active = defender
    p_atk._attack(p_def, rng)
    assert p_def.active.damage == 0


def test_coin_flip_attack_full_damage_on_all_heads() -> None:
    """コイントス技: 全部表なら damage × coin_flips のダメージ。"""
    rng = random.Random()
    rng.random = lambda: 0.1  # always < 0.5 → heads
    attacker_card = _make_basic_card("コイン技", hp=60, damage=40)
    attacker_card.attacks[0].coin_flips = 2  # 2枚トス
    ap = ActivePokemon(card=attacker_card)
    ap.energy = 10

    defender_card = _make_basic_card("まと", hp=200, damage=10)
    defender = ActivePokemon(card=defender_card)

    p_atk = Player("A", [deepcopy(attacker_card)])
    p_def = Player("D", [deepcopy(defender_card)])
    p_atk.active = ap
    p_def.active = defender
    p_atk._attack(p_def, rng)
    assert p_def.active.damage == 80  # 40 × 2 heads


def test_coin_flip_average_damage_is_half() -> None:
    """コイントス1枚技の期待ダメージは damage/2 に近い。"""
    rng = random.Random(42)
    total_damage = 0
    n = 1000
    for _ in range(n):
        attacker_card = _make_basic_card("コイン技", hp=60, damage=40)
        attacker_card.attacks[0].coin_flips = 1
        ap = ActivePokemon(card=attacker_card)
        ap.energy = 10

        defender_card = _make_basic_card("まと", hp=10000, damage=10)
        defender = ActivePokemon(card=defender_card)

        p_atk = Player("A", [deepcopy(attacker_card)])
        p_def = Player("D", [deepcopy(defender_card)])
        p_atk.active = ap
        p_def.active = defender
        p_atk._attack(p_def, rng)
        total_damage += p_def.active.damage

    avg = total_damage / n
    assert 15 <= avg <= 25, f"コイントス1枚(damage=40)の平均ダメージは20±5のはず: {avg:.1f}"


# ---------------------------------------------------------------------------
# all_cards.csv tests
# ---------------------------------------------------------------------------

def test_all_cards_csv_exists() -> None:
    """data/all_cards.csv が存在する。"""
    csv_path = Path(__file__).parent.parent / "data" / "all_cards.csv"
    assert csv_path.exists(), "data/all_cards.csv が見つかりません"


def test_all_cards_csv_has_required_columns() -> None:
    """all_cards.csv に必須カラムが含まれている。"""
    import csv
    csv_path = Path(__file__).parent.parent / "data" / "all_cards.csv"
    with open(csv_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames or []
    required = {
        "card_name", "card_type", "stage", "hp", "pokemon_type",
        "evolves_from", "is_ex", "trainer_effect", "set_name",
    }
    missing = required - set(fieldnames)
    assert not missing, f"all_cards.csv に必須カラムが不足: {missing}"


def test_all_cards_csv_pokemon_have_hp() -> None:
    """all_cards.csv のポケモンカードは HP が設定されている。"""
    import csv
    csv_path = Path(__file__).parent.parent / "data" / "all_cards.csv"
    with open(csv_path, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["card_type"] == "Pokemon":
                assert row["hp"], f"{row['card_name']} の HP が空です"
                assert int(row["hp"]) > 0, f"{row['card_name']} の HP が 0 以下です"


def test_all_cards_csv_evolution_chain_consistency() -> None:
    """all_cards.csv の進化チェーンが整合している（Stage1 の evolves_from が存在するカード）。"""
    import csv
    csv_path = Path(__file__).parent.parent / "data" / "all_cards.csv"
    rows = list(csv.DictReader(open(csv_path, encoding="utf-8")))
    all_names = {r["card_name"] for r in rows}
    for row in rows:
        if row["card_type"] == "Pokemon" and row.get("evolves_from"):
            evolves_from = row["evolves_from"]
            assert evolves_from in all_names, (
                f"{row['card_name']} の evolves_from='{evolves_from}' がCSVに存在しません"
            )


def test_all_cards_csv_rare_candy_present() -> None:
    """all_cards.csv にふしぎのあめが含まれている。"""
    import csv
    csv_path = Path(__file__).parent.parent / "data" / "all_cards.csv"
    with open(csv_path, encoding="utf-8") as f:
        names = [row["card_name"] for row in csv.DictReader(f)]
    assert "ふしぎのあめ" in names, "ふしぎのあめ が all_cards.csv に含まれていません"

