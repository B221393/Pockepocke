"""
tests/test_fetch_all_cards.py – fetch_all_cards.py のユニットテスト
"""

from __future__ import annotations

import csv
from pathlib import Path
from textwrap import dedent
from unittest.mock import MagicMock, patch

import pytest

from fetch_all_cards import (
    DEFAULT_URL,
    CSV_FIELDS,
    _clean,
    _normalize_type,
    _normalize_stage,
    _is_ex_name,
    _is_baby,
    _parse_int,
    _build_col_map,
    _parse_cards,
    _fill_evolves_from,
    _merge_with_existing,
    _write_csv,
    main,
)

try:
    from bs4 import BeautifulSoup
except ImportError:
    pytest.skip("beautifulsoup4 not installed", allow_module_level=True)


# ---------------------------------------------------------------------------
# 定数・ヘルパー関数のテスト
# ---------------------------------------------------------------------------

def test_default_url_points_to_card_list() -> None:
    assert "gamewith.jp/pokemon-tcg-pocket/462535" in DEFAULT_URL


def test_csv_fields_includes_required_columns() -> None:
    required = {
        "card_name", "card_type", "stage", "hp", "pokemon_type",
        "evolves_from", "is_ex", "trainer_effect", "set_name", "is_baby",
    }
    assert required <= set(CSV_FIELDS)


def test_clean_strips_whitespace() -> None:
    assert _clean("  ヒトカゲ  \n") == "ヒトカゲ"
    assert _clean("ヒト  カゲ") == "ヒト カゲ"


def test_normalize_type_japanese() -> None:
    assert _normalize_type("炎") == "Fire"
    assert _normalize_type("水") == "Water"
    assert _normalize_type("草") == "Grass"
    assert _normalize_type("雷") == "Lightning"
    assert _normalize_type("超") == "Psychic"
    assert _normalize_type("格闘") == "Fighting"
    assert _normalize_type("悪") == "Darkness"
    assert _normalize_type("鋼") == "Metal"
    assert _normalize_type("ドラゴン") == "Dragon"
    assert _normalize_type("無") == "Colorless"


def test_normalize_type_english() -> None:
    assert _normalize_type("Fire") == "Fire"
    assert _normalize_type("water") == "Water"
    assert _normalize_type("Lightning") == "Lightning"


def test_normalize_type_unknown_returns_colorless() -> None:
    assert _normalize_type("不明") == "Colorless"
    assert _normalize_type("") == "Colorless"


def test_normalize_stage_japanese() -> None:
    assert _normalize_stage("たね") == 0
    assert _normalize_stage("1進化") == 1
    assert _normalize_stage("2進化") == 2


def test_normalize_stage_english() -> None:
    assert _normalize_stage("basic") == 0
    assert _normalize_stage("stage1") == 1
    assert _normalize_stage("stage2") == 2


def test_normalize_stage_unknown_returns_none() -> None:
    assert _normalize_stage("不明") is None
    assert _normalize_stage("") is None


def test_is_ex_name() -> None:
    assert _is_ex_name("ミュウツーex") is True
    assert _is_ex_name("リザードンex") is True
    assert _is_ex_name("ピカチュウ") is False


def test_is_baby_name() -> None:
    assert _is_baby("ピチュー") is True
    assert _is_baby("トゲピー") is True
    assert _is_baby("ピカチュウ") is False


def test_parse_int() -> None:
    assert _parse_int("60") == "60"
    assert _parse_int("HP60") == "60"
    assert _parse_int("") == ""
    assert _parse_int("abc") == ""


# ---------------------------------------------------------------------------
# _build_col_map のテスト
# ---------------------------------------------------------------------------

def test_build_col_map_basic() -> None:
    headers = ["画像", "カード名", "HP", "タイプ", "セット"]
    col_map = _build_col_map(headers)
    assert col_map["name"] == 1
    assert col_map["hp"] == 2
    assert col_map["type"] == 3
    assert col_map["set"] == 4


def test_build_col_map_english_headers() -> None:
    headers = ["name", "hp", "type", "stage", "set"]
    col_map = _build_col_map(headers)
    assert col_map["name"] == 0
    assert col_map["hp"] == 1
    assert col_map["type"] == 2
    assert col_map["stage"] == 3
    assert col_map["set"] == 4


def test_build_col_map_empty() -> None:
    assert _build_col_map([]) == {}


# ---------------------------------------------------------------------------
# _parse_cards のテスト（HTMLフィクスチャ使用）
# ---------------------------------------------------------------------------

_SAMPLE_HTML_TABLE = dedent("""\
    <html><body>
    <table>
      <thead>
        <tr>
          <th>カード名</th>
          <th>HP</th>
          <th>タイプ</th>
          <th>セット</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td>ヒトカゲ</td>
          <td>60</td>
          <td>炎</td>
          <td>A1</td>
        </tr>
        <tr>
          <td>リザードンex</td>
          <td>180</td>
          <td>炎</td>
          <td>A1</td>
        </tr>
        <tr>
          <td>ゼニガメ</td>
          <td>60</td>
          <td>水</td>
          <td>A1</td>
        </tr>
        <tr>
          <td>モンスターボール</td>
          <td></td>
          <td></td>
          <td>A1</td>
        </tr>
      </tbody>
    </table>
    </body></html>
""")


def _soup(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "html.parser")


def test_parse_cards_returns_records() -> None:
    records = _parse_cards(_soup(_SAMPLE_HTML_TABLE))
    assert len(records) >= 1


def test_parse_cards_pokemon_card_type() -> None:
    records = _parse_cards(_soup(_SAMPLE_HTML_TABLE))
    hitokage = next((r for r in records if r["card_name"] == "ヒトカゲ"), None)
    assert hitokage is not None
    assert hitokage["card_type"] == "Pokemon"
    assert hitokage["hp"] == "60"
    assert hitokage["pokemon_type"] == "Fire"
    assert hitokage["set_name"] == "A1"


def test_parse_cards_ex_flag() -> None:
    records = _parse_cards(_soup(_SAMPLE_HTML_TABLE))
    lizardon = next((r for r in records if r["card_name"] == "リザードンex"), None)
    assert lizardon is not None
    assert lizardon["is_ex"] == "True"


def test_parse_cards_trainer_card_type() -> None:
    records = _parse_cards(_soup(_SAMPLE_HTML_TABLE))
    ball = next((r for r in records if r["card_name"] == "モンスターボール"), None)
    assert ball is not None
    # No HP → treated as trainer card
    assert ball["card_type"] != "Pokemon"


def test_parse_cards_deduplicates() -> None:
    html = dedent("""\
        <html><body>
        <table>
          <thead><tr><th>カード名</th><th>HP</th><th>タイプ</th><th>セット</th></tr></thead>
          <tbody>
            <tr><td>ヒトカゲ</td><td>60</td><td>炎</td><td>A1</td></tr>
            <tr><td>ヒトカゲ</td><td>60</td><td>炎</td><td>A1</td></tr>
          </tbody>
        </table>
        </body></html>
    """)
    records = _parse_cards(_soup(html))
    names = [r["card_name"] for r in records]
    assert names.count("ヒトカゲ") == 1


def test_parse_cards_no_tables_uses_fallback() -> None:
    """ページにテーブルがない場合、リンクからカード名を抽出する。"""
    html = dedent("""\
        <html><body>
        <a href="/pokemon-tcg-pocket/card/12345">ヒトカゲ</a>
        <a href="/pokemon-tcg-pocket/card/12346">ゼニガメ</a>
        <a href="https://other.example.com">外部リンク</a>
        </body></html>
    """)
    records = _parse_cards(_soup(html))
    names = {r["card_name"] for r in records}
    assert "ヒトカゲ" in names
    assert "ゼニガメ" in names
    assert "外部リンク" not in names


# ---------------------------------------------------------------------------
# _fill_evolves_from のテスト
# ---------------------------------------------------------------------------

def test_fill_evolves_from_infers_base_for_ex() -> None:
    records = [
        {"card_name": "ヒトカゲ", "card_type": "Pokemon", "stage": "0", "evolves_from": ""},
        {"card_name": "リザードex", "card_type": "Pokemon", "stage": "1", "evolves_from": ""},
    ]
    _fill_evolves_from(records)
    # リザードex の evolves_from は 'リザード' が推定されるが name に 'ヒトカゲ' しかないので空のまま
    # (Inferred name 'リザード' is not in the all_names set, so it stays empty)
    assert records[1]["evolves_from"] == ""


def test_fill_evolves_from_does_not_overwrite_existing() -> None:
    records = [
        {"card_name": "ヒトカゲ", "card_type": "Pokemon", "stage": "0", "evolves_from": ""},
        {"card_name": "リザードex", "card_type": "Pokemon", "stage": "1", "evolves_from": "ヒトカゲ"},
    ]
    _fill_evolves_from(records)
    assert records[1]["evolves_from"] == "ヒトカゲ"


# ---------------------------------------------------------------------------
# _merge_with_existing のテスト
# ---------------------------------------------------------------------------

def test_merge_with_existing_new_record_added(tmp_path: Path) -> None:
    existing_csv = tmp_path / "all_cards.csv"
    existing_records = [
        {f: "" for f in CSV_FIELDS} | {"card_name": "ヒトカゲ", "card_type": "Pokemon", "hp": "60"},
    ]
    _write_csv(existing_records, existing_csv)

    new_records = [
        {f: "" for f in CSV_FIELDS} | {"card_name": "ゼニガメ", "card_type": "Pokemon", "hp": "60"},
    ]
    merged = _merge_with_existing(new_records, existing_csv)
    names = {r["card_name"] for r in merged}
    assert "ヒトカゲ" in names
    assert "ゼニガメ" in names


def test_merge_with_existing_new_overwrites_old(tmp_path: Path) -> None:
    existing_csv = tmp_path / "all_cards.csv"
    existing_records = [
        {f: "" for f in CSV_FIELDS} | {"card_name": "ヒトカゲ", "hp": "60"},
    ]
    _write_csv(existing_records, existing_csv)

    new_records = [
        {f: "" for f in CSV_FIELDS} | {"card_name": "ヒトカゲ", "hp": "70"},
    ]
    merged = _merge_with_existing(new_records, existing_csv)
    hitokage = next(r for r in merged if r["card_name"] == "ヒトカゲ")
    assert hitokage["hp"] == "70"


def test_merge_with_existing_no_file_returns_new(tmp_path: Path) -> None:
    missing = tmp_path / "no_such_file.csv"
    new_records = [{f: "" for f in CSV_FIELDS} | {"card_name": "ヒトカゲ"}]
    merged = _merge_with_existing(new_records, missing)
    assert merged == new_records


# ---------------------------------------------------------------------------
# _write_csv のテスト
# ---------------------------------------------------------------------------

def test_write_csv_creates_file(tmp_path: Path) -> None:
    out = tmp_path / "cards.csv"
    records = [{f: "" for f in CSV_FIELDS} | {"card_name": "ヒトカゲ", "card_type": "Pokemon", "hp": "60"}]
    _write_csv(records, out)
    assert out.exists()


def test_write_csv_has_correct_header(tmp_path: Path) -> None:
    out = tmp_path / "cards.csv"
    _write_csv([], out)
    with open(out, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        assert set(reader.fieldnames or []) == set(CSV_FIELDS)


def test_write_csv_round_trips(tmp_path: Path) -> None:
    out = tmp_path / "cards.csv"
    records = [
        {f: "" for f in CSV_FIELDS}
        | {"card_name": "ヒトカゲ", "card_type": "Pokemon", "hp": "60", "set_name": "A1"},
    ]
    _write_csv(records, out)
    with open(out, encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    assert rows[0]["card_name"] == "ヒトカゲ"
    assert rows[0]["hp"] == "60"


# ---------------------------------------------------------------------------
# main() のテスト（HTTPリクエストをモック）
# ---------------------------------------------------------------------------

def test_main_success(tmp_path: Path) -> None:
    out = tmp_path / "cards.csv"
    with patch("fetch_all_cards._fetch_html", return_value=_SAMPLE_HTML_TABLE):
        rc = main(["--out", str(out)])
    assert rc == 0
    assert out.exists()


def test_main_network_error_returns_1(tmp_path: Path) -> None:
    import requests
    out = tmp_path / "cards.csv"
    with patch(
        "fetch_all_cards._fetch_html",
        side_effect=requests.RequestException("connection error"),
    ):
        rc = main(["--out", str(out)])
    assert rc == 1


def test_main_no_records_returns_2(tmp_path: Path) -> None:
    out = tmp_path / "cards.csv"
    with patch("fetch_all_cards._fetch_html", return_value="<html><body></body></html>"):
        rc = main(["--out", str(out)])
    assert rc == 2


def test_main_merge_flag(tmp_path: Path) -> None:
    """--merge フラグで既存 CSV に追記される。"""
    out = tmp_path / "cards.csv"
    existing = [{f: "" for f in CSV_FIELDS} | {"card_name": "既存カード", "card_type": "Pokemon"}]
    _write_csv(existing, out)

    with patch("fetch_all_cards._fetch_html", return_value=_SAMPLE_HTML_TABLE):
        rc = main(["--out", str(out), "--merge"])
    assert rc == 0
    with open(out, encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    names = {r["card_name"] for r in rows}
    assert "既存カード" in names
    assert "ヒトカゲ" in names


def test_main_default_url() -> None:
    """デフォルト URL が正しいページを指している。"""
    assert DEFAULT_URL == "https://gamewith.jp/pokemon-tcg-pocket/462535"
