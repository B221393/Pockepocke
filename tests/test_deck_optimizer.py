"""
tests/test_deck_optimizer.py – デッキ最適化AIのユニットテスト
"""

from __future__ import annotations

import random
from copy import deepcopy
from pathlib import Path

import pytest

from simulator import Attack, Card, Player, Game, ActivePokemon
from deck_optimizer import (
    MAX_COPIES,
    DeckOptimizer,
    _evaluate_deck,
    _is_valid_deck,
    _mutate_deck,
    _deck_to_json,
    load_card_pool,
)

DECKS_DIR = Path(__file__).parent.parent / "decks"
CSV_PATH = Path(__file__).parent.parent / "data" / "all_cards.csv"

HERACROSS_DECK = DECKS_DIR / "mega_heracross_deck.json"
DARKRAI_DECK = DECKS_DIR / "darkrai_altaria_deck.json"
CHARIZARD_DECK = DECKS_DIR / "mega_charizard_deck.json"


def _make_basic(name: str = "テスト", hp: int = 60, damage: int = 30) -> Card:
    return Card(
        name=name,
        card_type="Pokemon",
        stage=0,
        hp=hp,
        pokemon_type="Colorless",
        evolves_from=None,
        attacks=[Attack(name="たいあたり", energy_cost=1, damage=damage)],
    )


def _minimal_deck(name: str = "テスト", hp: int = 60, damage: int = 30) -> list[Card]:
    basic = _make_basic(name, hp, damage)
    item = Card("きずぐすり", "Item", None, None, None, None, [], "heal_30")
    return [deepcopy(basic) for _ in range(2)] + [deepcopy(item) for _ in range(18)]


# ---------------------------------------------------------------------------
# load_card_pool tests
# ---------------------------------------------------------------------------

def test_load_card_pool_returns_cards() -> None:
    """カードプールが読み込まれ、少なくとも1枚のカードが返る。"""
    pool = load_card_pool(CSV_PATH)
    assert len(pool) > 0


def test_load_card_pool_no_ex_excludes_ex() -> None:
    """no_ex=True のとき EX ポケモンが除外される。"""
    pool = load_card_pool(CSV_PATH, no_ex=True)
    ex_cards = [c for c in pool if c.name.endswith("ex")]
    assert len(ex_cards) == 0


def test_load_card_pool_type_filter() -> None:
    """allowed_types フィルタが動作する。"""
    pool = load_card_pool(CSV_PATH, allowed_types=["Fire"])
    for c in pool:
        if c.card_type == "Pokemon":
            assert c.pokemon_type == "Fire", f"{c.name} のタイプが Fire 以外: {c.pokemon_type}"


def test_load_card_pool_min_hp_filter() -> None:
    """min_hp フィルタが動作する。"""
    pool = load_card_pool(CSV_PATH, min_hp=100)
    for c in pool:
        if c.card_type == "Pokemon":
            assert (c.hp or 0) >= 100, f"{c.name} の HP {c.hp} が min_hp 100 未満"


def test_load_card_pool_includes_baby_pokemon() -> None:
    """カードプールにベビィポケモンが含まれている。"""
    pool = load_card_pool(CSV_PATH)
    babies = [c for c in pool if c.is_baby]
    assert len(babies) >= 3, f"ベビィポケモンが不足: {len(babies)} 枚"


def test_load_card_pool_baby_pokemon_have_is_baby_true() -> None:
    """ベビィポケモンの is_baby フラグが True になっている。"""
    pool = load_card_pool(CSV_PATH)
    baby_names = {"ピチュー", "ソーナノ", "ゴンベ"}
    found = {c.name: c.is_baby for c in pool if c.name in baby_names}
    for name in baby_names:
        assert found.get(name) is True, f"{name} の is_baby が True でない: {found.get(name)}"


# ---------------------------------------------------------------------------
# _is_valid_deck tests
# ---------------------------------------------------------------------------

def test_is_valid_deck_accepts_valid() -> None:
    """有効な20枚デッキが合格する。"""
    from simulator import load_deck_from_json
    deck = load_deck_from_json(DARKRAI_DECK)
    assert _is_valid_deck(deck) is True


def test_is_valid_deck_rejects_wrong_size() -> None:
    """20枚でないデッキは不合格。"""
    from simulator import load_deck_from_json
    deck = load_deck_from_json(DARKRAI_DECK)[:19]
    assert _is_valid_deck(deck) is False


def test_is_valid_deck_rejects_too_many_copies() -> None:
    """同名カードが3枚以上あるデッキは不合格。"""
    from simulator import load_deck_from_json
    deck = load_deck_from_json(DARKRAI_DECK)
    # Replace the last card with an extra copy of deck[0] (creating 3 copies)
    first_name = deck[0].name
    extra = deepcopy(deck[0])
    # Count how many first_name already in deck
    existing = [c for c in deck if c.name == first_name]
    assert len(existing) == 2  # sanity check
    # Remove one card that is NOT first_name, append an extra first_name copy
    idx_other = next(i for i, c in enumerate(deck) if c.name != first_name)
    deck[idx_other] = extra  # now first_name appears 3 times
    assert _is_valid_deck(deck) is False


def test_is_valid_deck_rejects_too_few_basics() -> None:
    """たねポケモンが4枚未満のデッキは不合格。"""
    from simulator import load_deck_from_json
    deck = load_deck_from_json(DARKRAI_DECK)
    # Remove basics until fewer than 4 remain
    kept = []
    removed_basics = 0
    for c in deck:
        if c.card_type == "Pokemon" and c.stage == 0 and removed_basics < 3:
            removed_basics += 1
        else:
            kept.append(c)
    # Pad back to 20 with a known item
    item = Card("きずぐすり", "Item", None, None, None, None, [], "heal_30")
    while len(kept) < 20:
        kept.append(deepcopy(item))
    # Trim to 20 (may need if somehow longer)
    kept = kept[:20]
    assert _is_valid_deck(kept) is False


# ---------------------------------------------------------------------------
# _mutate_deck tests
# ---------------------------------------------------------------------------

def test_mutate_deck_returns_valid_deck() -> None:
    """_mutate_deck は有効な20枚デッキを返す。"""
    from simulator import load_deck_from_json
    pool = load_card_pool(CSV_PATH)
    deck = load_deck_from_json(DARKRAI_DECK)
    rng = random.Random(42)
    mutated = _mutate_deck(deck, pool, rng)
    assert _is_valid_deck(mutated), "変異後のデッキが無効"
    assert len(mutated) == 20


def test_mutate_deck_no_ex_excludes_ex() -> None:
    """no_ex=True のとき変異後デッキに EX カードが入らない。"""
    from simulator import load_deck_from_json
    pool = load_card_pool(CSV_PATH, no_ex=True)
    # Build a no-EX version of Darkrai deck by removing EX Pokémon
    base_deck = load_deck_from_json(DARKRAI_DECK)
    no_ex_deck = [c for c in base_deck if not c.name.endswith("ex")]
    # Pad back to 20 with non-EX basics from CSV
    non_ex_basics = [c for c in pool if c.card_type == "Pokemon" and c.stage == 0]
    from collections import Counter
    counts = Counter(c.name for c in no_ex_deck)
    for card in non_ex_basics:
        if len(no_ex_deck) >= 20:
            break
        if counts.get(card.name, 0) < MAX_COPIES:
            no_ex_deck.append(deepcopy(card))
            counts[card.name] += 1
    if not _is_valid_deck(no_ex_deck[:20]):
        pytest.skip("no-EX デッキが有効な20枚にならないためスキップ")
    deck = no_ex_deck[:20]

    rng = random.Random(7)
    for _ in range(10):
        mutated = _mutate_deck(deck, pool, rng, no_ex=True)
        ex_cards = [c for c in mutated if c.card_type == "Pokemon" and c.name.endswith("ex")]
        assert len(ex_cards) == 0, "no_ex=True なのに EX カードが含まれている"


# ---------------------------------------------------------------------------
# _evaluate_deck tests
# ---------------------------------------------------------------------------

def test_evaluate_deck_returns_float_between_0_and_1() -> None:
    """_evaluate_deck は 0〜1 の浮動小数点を返す。"""
    from simulator import load_deck_from_json
    deck = load_deck_from_json(HERACROSS_DECK)
    opp = load_deck_from_json(DARKRAI_DECK)
    rng = random.Random(0)
    wr = _evaluate_deck(deck, [opp], n=50, rng=rng)
    assert 0.0 <= wr <= 1.0, f"勝率 {wr} が範囲外"


def test_evaluate_deck_empty_opponents_returns_zero() -> None:
    """対戦相手なしのとき 0.0 が返る。"""
    from simulator import load_deck_from_json
    deck = load_deck_from_json(HERACROSS_DECK)
    rng = random.Random(0)
    wr = _evaluate_deck(deck, [], n=50, rng=rng)
    assert wr == 0.0


# ---------------------------------------------------------------------------
# DeckOptimizer tests
# ---------------------------------------------------------------------------

def test_deck_optimizer_runs_without_error() -> None:
    """DeckOptimizer が正常に動作する（スモークテスト）。"""
    from simulator import load_deck_from_json
    deck = load_deck_from_json(DARKRAI_DECK)
    opp = load_deck_from_json(CHARIZARD_DECK)
    pool = load_card_pool(CSV_PATH)
    optimizer = DeckOptimizer(
        initial_deck=deck,
        opponent_decks=[opp],
        card_pool=pool,
        n_games=30,
        seed=99,
    )
    result = optimizer.optimize(max_iterations=5)
    assert _is_valid_deck(result), "最適化後のデッキが無効"
    assert len(result) == 20


def test_deck_optimizer_win_rate_is_float() -> None:
    """current_win_rate が 0〜1 の浮動小数点。"""
    from simulator import load_deck_from_json
    deck = load_deck_from_json(HERACROSS_DECK)
    opp = load_deck_from_json(DARKRAI_DECK)
    pool = load_card_pool(CSV_PATH)
    optimizer = DeckOptimizer(
        initial_deck=deck,
        opponent_decks=[opp],
        card_pool=pool,
        n_games=20,
        seed=5,
    )
    assert 0.0 <= optimizer.current_win_rate <= 1.0


def test_deck_optimizer_no_ex() -> None:
    """no_ex=True のとき最適化後デッキに EX カードが含まれない。"""
    from simulator import load_deck_from_json
    base_deck = load_deck_from_json(DARKRAI_DECK)
    pool = load_card_pool(CSV_PATH, no_ex=True)

    # Build a valid no-EX starting deck using non-EX cards
    no_ex_deck = [c for c in base_deck if not c.name.endswith("ex")]
    from collections import Counter
    counts = Counter(c.name for c in no_ex_deck)
    non_ex_basics = [c for c in pool if c.card_type == "Pokemon" and c.stage == 0]
    for card in non_ex_basics:
        if len(no_ex_deck) >= 20:
            break
        if counts.get(card.name, 0) < MAX_COPIES:
            no_ex_deck.append(deepcopy(card))
            counts[card.name] += 1
    deck = no_ex_deck[:20]
    if not _is_valid_deck(deck):
        pytest.skip("no-EX デッキが有効な20枚にならないためスキップ")

    opp = load_deck_from_json(CHARIZARD_DECK)
    if not pool:
        pytest.skip("no-EX カードプールが空のためスキップ")

    optimizer = DeckOptimizer(
        initial_deck=deck,
        opponent_decks=[opp],
        card_pool=pool,
        n_games=20,
        seed=7,
        no_ex=True,
    )
    result = optimizer.optimize(max_iterations=3)
    ex_in_result = [c for c in result if c.card_type == "Pokemon" and c.name.endswith("ex")]
    assert len(ex_in_result) == 0


# ---------------------------------------------------------------------------
# _deck_to_json tests
# ---------------------------------------------------------------------------

def test_deck_to_json_structure() -> None:
    """_deck_to_json が正しい JSON 構造を返す。"""
    from simulator import load_deck_from_json
    deck = load_deck_from_json(DARKRAI_DECK)
    result = _deck_to_json(deck, "テストデッキ")
    assert "name" in result
    assert "cards" in result
    assert isinstance(result["cards"], list)
    total = sum(e["count"] for e in result["cards"])
    assert total == 20


def test_deck_to_json_count_is_correct() -> None:
    """_deck_to_json の count が正確。"""
    basic = _make_basic("ポケモンX")
    item = Card("モンスターボール", "Item", None, None, None, None, [], "search_basic")
    deck = [deepcopy(basic) for _ in range(2)] + [deepcopy(item) for _ in range(18)]
    result = _deck_to_json(deck)
    entries_by_name = {e["name"]: e["count"] for e in result["cards"]}
    assert entries_by_name["ポケモンX"] == 2
    assert entries_by_name["モンスターボール"] == 18


# ---------------------------------------------------------------------------
# gamewith_decks.csv tests
# ---------------------------------------------------------------------------

def test_gamewith_decks_has_non_ex_decks() -> None:
    """gamewith_decks.csv に非EXデッキが含まれている。"""
    import csv
    csv_path = Path(__file__).parent.parent / "data" / "gamewith_decks.csv"
    rows = list(csv.DictReader(open(csv_path, encoding="utf-8")))
    non_ex = [r for r in rows if str(r.get("is_ex", "True")).strip().lower() != "true"]
    assert len(non_ex) >= 2, f"非EXデッキが不足: {len(non_ex)} 件"


# ---------------------------------------------------------------------------
# CLI smoke test
# ---------------------------------------------------------------------------

def test_cli_smoke_test(capsys, tmp_path) -> None:
    """CLIが正常に動作する（少ない試合数・反復でスモークテスト）。"""
    from deck_optimizer import main
    out_path = tmp_path / "optimized.json"
    rc = main([
        "--deck", str(DARKRAI_DECK),
        "--all-builtin",
        "-n", "30",
        "--iterations", "3",
        "--seed", "1",
        "--output", str(out_path),
    ])
    assert rc == 0
    assert out_path.exists()
    import json
    data = json.loads(out_path.read_text(encoding="utf-8"))
    assert "cards" in data
    total = sum(e["count"] for e in data["cards"])
    assert total == 20
