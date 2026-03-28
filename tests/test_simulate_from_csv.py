"""
tests/test_simulate_from_csv.py – CSVシミュレーターのユニットテスト
"""

from __future__ import annotations

from pathlib import Path

import pytest

from simulate_from_csv import DeckSpec, load_deck_specs, _simulate_pair
import random

CSV_PATH = Path(__file__).parent.parent / "data" / "gamewith_decks.csv"


# ---------------------------------------------------------------------------
# CSV loading tests
# ---------------------------------------------------------------------------

def test_load_deck_specs_returns_records() -> None:
    specs = load_deck_specs(CSV_PATH)
    assert len(specs) >= 1


def test_load_deck_specs_fields() -> None:
    specs = load_deck_specs(CSV_PATH)
    for s in specs:
        assert s.deck_name
        assert s.tier in ("S", "S+", "A", "B", "C", "")
        assert s.hp > 0
        assert s.damage > 0
        assert s.energy_cost > 0
        assert isinstance(s.is_ex, bool)
        assert isinstance(s.has_evolution, bool)


def test_load_deck_specs_usage_rate_range() -> None:
    specs = load_deck_specs(CSV_PATH)
    for s in specs:
        assert 0.0 <= s.usage_rate <= 100.0
        assert 0.0 <= s.win_rate <= 100.0


# ---------------------------------------------------------------------------
# DeckSpec → card list tests
# ---------------------------------------------------------------------------

def _make_spec(**kwargs) -> DeckSpec:
    defaults = dict(
        deck_name="テストデッキ",
        tier="A",
        usage_rate=10.0,
        win_rate=50.0,
        main_pokemon="テストex",
        energy_type="Colorless",
        hp=100,
        damage=60,
        energy_cost=2,
        is_ex=True,
        has_evolution=False,
        deck_style="バランス",
        description="テスト",
    )
    defaults.update(kwargs)
    return DeckSpec(**defaults)


def test_to_card_list_length() -> None:
    spec = _make_spec()
    cards = spec.to_card_list()
    assert len(cards) == 20


def test_to_card_list_length_evolution() -> None:
    spec = _make_spec(has_evolution=True)
    cards = spec.to_card_list()
    assert len(cards) == 20


def test_to_card_list_has_enough_basics() -> None:
    """All generated decks must have ≥ 6 Basic Pokémon to keep accident rates low."""
    for has_ev in (True, False):
        spec = _make_spec(has_evolution=has_ev)
        cards = spec.to_card_list()
        basics = [c for c in cards if c.card_type == "Pokemon" and c.stage == 0]
        assert len(basics) >= 6, (
            f"has_evolution={has_ev}: たねポケモンが不足 ({len(basics)} 枚)"
        )


def test_to_card_list_max_two_copies() -> None:
    from collections import Counter
    spec = _make_spec()
    cards = spec.to_card_list()
    counts = Counter(c.name for c in cards)
    for name, count in counts.items():
        assert count <= 2, f"'{name}' が {count} 枚（最大2枚）"


def test_to_card_list_control_deck_has_sleep_attack() -> None:
    spec = _make_spec(deck_style="コントロール")
    cards = spec.to_card_list()
    main = next(c for c in cards if c.name == spec.main_pokemon)
    effects = [a.effect for a in main.attacks]
    assert "sleep" in effects


def test_to_card_list_all_csv_decks_valid() -> None:
    """Every deck row in the CSV must produce a valid 20-card deck."""
    specs = load_deck_specs(CSV_PATH)
    for spec in specs:
        cards = spec.to_card_list()
        assert len(cards) == 20, f"{spec.deck_name}: {len(cards)} 枚"


# ---------------------------------------------------------------------------
# _simulate_pair tests
# ---------------------------------------------------------------------------

def test_simulate_pair_returns_result() -> None:
    specs = load_deck_specs(CSV_PATH)
    rng = random.Random(0)
    result = _simulate_pair(specs[0], specs[1], n=50, rng=rng)
    assert result.total_games == 50
    assert result.deck1_wins + result.deck2_wins + result.draws + result.games_with_accident == 50


def test_simulate_pair_accident_rate_low() -> None:
    specs = load_deck_specs(CSV_PATH)
    rng = random.Random(7)
    result = _simulate_pair(specs[0], specs[1], n=500, rng=rng)
    assert result.deck1_accident_rate < 0.20
    assert result.deck2_accident_rate < 0.20


# ---------------------------------------------------------------------------
# CLI smoke test
# ---------------------------------------------------------------------------

def test_cli_tier_filter(capsys) -> None:
    from simulate_from_csv import main
    rc = main(["--csv", str(CSV_PATH), "--tier", "S", "-n", "50", "--seed", "1"])
    assert rc == 0
    captured = capsys.readouterr()
    assert "デッキ総合勝率ランキング" in captured.out


def test_cli_top_n(capsys) -> None:
    from simulate_from_csv import main
    rc = main(["--csv", str(CSV_PATH), "--top", "3", "-n", "50", "--seed", "2"])
    assert rc == 0


def test_cli_output_csv(tmp_path) -> None:
    from simulate_from_csv import main
    out = tmp_path / "out.csv"
    rc = main(["--csv", str(CSV_PATH), "--top", "3", "-n", "50", "--seed", "3", "--output", str(out)])
    assert rc == 0
    assert out.exists()
    lines = out.read_text(encoding="utf-8-sig").splitlines()
    assert len(lines) >= 4  # header + 3 matchups
