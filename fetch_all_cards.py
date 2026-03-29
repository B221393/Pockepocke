#!/usr/bin/env python3
"""
fetch_all_cards.py – GameWith ポケポケ 全カードリスト スクレイパー

GameWith の下記ページからポケポケの全カード情報を取得し、
data/all_cards.csv に保存します。

    https://gamewith.jp/pokemon-tcg-pocket/462535

使い方:
    pip install requests beautifulsoup4
    python fetch_all_cards.py

オプション:
    --url URL       スクレイピング対象 URL (デフォルト: 上記 URL)
    --out PATH      出力 CSV パス (デフォルト: data/all_cards.csv)
    --timeout N     HTTP タイムアウト秒数 (デフォルト: 15)
    --merge         既存の data/all_cards.csv の内容と統合する (デフォルト: 上書き)
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Dependency check
# ---------------------------------------------------------------------------
try:
    import requests
    from bs4 import BeautifulSoup, Tag
except ImportError as exc:
    print(
        f"[ERROR] 必要ライブラリが見つかりません: {exc}\n"
        "  pip install requests beautifulsoup4\n"
        "を実行してからもう一度お試しください。",
        file=sys.stderr,
    )
    sys.exit(1)

DEFAULT_URL = "https://gamewith.jp/pokemon-tcg-pocket/462535"
DEFAULT_OUT = Path("data/all_cards.csv")

# CSV column names (matches the existing all_cards.csv schema)
CSV_FIELDS = [
    "card_name",              # カード名
    "card_type",              # Pokemon / Item / Supporter / Stadium / Tool
    "stage",                  # 0=たね / 1=1進化 / 2=2進化 / None(トレーナー)
    "hp",                     # HP (ポケモンのみ)
    "pokemon_type",           # Fire/Water/Grass/Lightning/Psychic/Fighting/Darkness/Metal/Dragon/Colorless
    "evolves_from",           # 進化前のカード名
    "is_ex",                  # EX ポケモン (True/False)
    "attack1_energy_cost",    # わざ1 エネルギーコスト
    "attack1_damage",         # わざ1 ダメージ
    "attack1_coin_flips",     # わざ1 コイン枚数
    "attack1_effect",         # わざ1 効果キーワード
    "attack2_energy_cost",    # わざ2 エネルギーコスト
    "attack2_damage",         # わざ2 ダメージ
    "attack2_coin_flips",     # わざ2 コイン枚数
    "attack2_effect",         # わざ2 効果キーワード
    "trainer_effect",         # トレーナー効果キーワード
    "set_name",               # 収録セット名
    "is_baby",                # ベビィポケモン (True/False)
]

# Mapping from Japanese type names to English keys used in the codebase
_TYPE_MAP: dict[str, str] = {
    "炎": "Fire",
    "ほのお": "Fire",
    "fire": "Fire",
    "水": "Water",
    "みず": "Water",
    "water": "Water",
    "草": "Grass",
    "くさ": "Grass",
    "grass": "Grass",
    "雷": "Lightning",
    "でんき": "Lightning",
    "lightning": "Lightning",
    "electric": "Lightning",
    "超": "Psychic",
    "エスパー": "Psychic",
    "psychic": "Psychic",
    "格闘": "Fighting",
    "かくとう": "Fighting",
    "fighting": "Fighting",
    "悪": "Darkness",
    "あく": "Darkness",
    "darkness": "Darkness",
    "dark": "Darkness",
    "鋼": "Metal",
    "はがね": "Metal",
    "metal": "Metal",
    "steel": "Metal",
    "ドラゴン": "Dragon",
    "dragon": "Dragon",
    "無": "Colorless",
    "むしょく": "Colorless",
    "colorless": "Colorless",
    "normal": "Colorless",
}

# Mapping from Japanese stage labels to integers
_STAGE_MAP: dict[str, int] = {
    "たね": 0,
    "基本": 0,
    "basic": 0,
    "1進化": 1,
    "stage1": 1,
    "stage 1": 1,
    "2進化": 2,
    "stage2": 2,
    "stage 2": 2,
}

# Known baby Pokémon names (Pokémon TCG Pocket)
_BABY_POKEMON: frozenset[str] = frozenset([
    "ピチュー", "トゲピー", "クリンク", "ソーナノ", "ゴンベ",
    "リラ", "ムチュール", "ネイティ", "ハネッコ",
])

# Trainer card type keywords
_TRAINER_TYPE_KEYWORDS: dict[str, str] = {
    "サポート": "Supporter",
    "supporter": "Supporter",
    "グッズ": "Item",
    "item": "Item",
    "スタジアム": "Stadium",
    "stadium": "Stadium",
    "ポケモンのどうぐ": "Tool",
    "tool": "Tool",
}


def _fetch_html(url: str, timeout: int) -> str:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0 Safari/537.36"
        ),
        "Accept-Language": "ja,en;q=0.9",
    }
    resp = requests.get(url, headers=headers, timeout=timeout)
    resp.raise_for_status()
    return resp.text


def _clean(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _normalize_type(raw: str) -> str:
    """炎/水/草/… → Fire/Water/Grass/…  (unknown → Colorless)"""
    key = raw.strip().lower()
    for jp, en in _TYPE_MAP.items():
        if jp.lower() in key:
            return en
    return "Colorless"


def _normalize_stage(raw: str) -> int | None:
    """'たね'/'1進化'/… → 0/1/2  (不明 → None)"""
    key = raw.strip().lower()
    for label, val in _STAGE_MAP.items():
        if label.lower() in key:
            return val
    return None


def _detect_trainer_type(cells: list[str]) -> str:
    """Return Pokemon/Item/Supporter/Stadium/Tool based on cell text hints."""
    combined = " ".join(cells).lower()
    for kw, ttype in _TRAINER_TYPE_KEYWORDS.items():
        if kw.lower() in combined:
            return ttype
    return "Item"  # default for unknown trainer cards


def _parse_int(text: str) -> str:
    """Extract first integer from text, return '' if none."""
    m = re.search(r"\d+", text)
    return m.group() if m else ""


def _is_ex_name(name: str) -> bool:
    return bool(re.search(r"ex\b", name, re.IGNORECASE))


def _is_baby(name: str) -> bool:
    return name in _BABY_POKEMON


def _row_template() -> dict:
    return {f: "" for f in CSV_FIELDS}


def _infer_evolves_from(name: str, all_names: set[str]) -> str:
    """
    Heuristic: strip Pokémon TCG Pocket suffixes ('ex', 'メガ', '☆' etc.)
    from evolved card names and try to find a matching base form in the
    known card set.
    """
    stripped = re.sub(r"(ex|EX|☆|◇)\s*$", "", name).strip()
    stripped = re.sub(r"^(メガ|Mega)", "", stripped).strip()
    if stripped and stripped != name and stripped in all_names:
        return stripped
    return ""


# ---------------------------------------------------------------------------
# Main parser
# ---------------------------------------------------------------------------

def _parse_cards(soup: BeautifulSoup) -> list[dict]:
    """
    GameWith のポケポケ全カードリストページから行データを抽出します。

    ページ構造の例（典型的なGameWithテーブル）:
      <table>
        <thead>
          <tr>
            <th>カード画像</th>
            <th>カード名</th>
            <th>HP</th>
            <th>タイプ</th>
            <th>レアリティ</th>
            <th>セット</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td><img ...></td>
            <td><a href="...">ヒトカゲ</a></td>
            <td>60</td>
            <td>炎</td>
            <td>◆</td>
            <td>遺伝子の秘密</td>
          </tr>
          ...
        </tbody>
      </table>

    見出し行 (th) からカラム位置を動的に検出し、各テーブルをパース。
    """
    records: list[dict] = []
    seen_names: set[str] = set()

    # Collect all tables on the page
    tables = soup.find_all("table")
    if not tables:
        # Fallback: look for list-style card entries (div/li patterns)
        records.extend(_parse_card_list_items(soup))
        return _dedupe(records)

    for table in tables:
        assert isinstance(table, Tag)
        header_row = table.find("tr")
        if not header_row:
            continue

        # Build column index map from th/td in the first row
        header_cells = [_clean(th.get_text()) for th in header_row.find_all(["th", "td"])]
        col_map = _build_col_map(header_cells)

        # If we can't identify at least a name column, skip this table
        if "name" not in col_map:
            continue

        for tr in table.find_all("tr")[1:]:
            cells_tags = tr.find_all(["td", "th"])
            if not cells_tags:
                continue
            cells = [_clean(td.get_text()) for td in cells_tags]

            row = _parse_row(cells, col_map, cells_tags)
            if not row or not row.get("card_name"):
                continue

            name = row["card_name"]
            if name not in seen_names:
                seen_names.add(name)
                records.append(row)

    return _dedupe(records)


def _build_col_map(headers: list[str]) -> dict[str, int]:
    """
    Map semantic column roles to column indices based on header text.
    Returns a dict: role → index.
    """
    col_map: dict[str, int] = {}
    for i, h in enumerate(headers):
        hl = h.lower()
        if any(k in hl for k in ("カード名", "名前", "name", "ポケモン名")):
            col_map.setdefault("name", i)
        elif any(k in hl for k in ("hp",)):
            col_map.setdefault("hp", i)
        elif any(k in hl for k in ("タイプ", "type", "属性")):
            col_map.setdefault("type", i)
        elif any(k in hl for k in ("進化", "stage", "段階")):
            col_map.setdefault("stage", i)
        elif any(k in hl for k in ("セット", "set", "パック", "シリーズ", "弾")):
            col_map.setdefault("set", i)
        elif any(k in hl for k in ("レアリティ", "rarity", "希少")):
            col_map.setdefault("rarity", i)
        elif any(k in hl for k in ("わざ1", "attack1", "技1")):
            col_map.setdefault("atk1", i)
        elif any(k in hl for k in ("わざ2", "attack2", "技2")):
            col_map.setdefault("atk2", i)
        elif any(k in hl for k in ("進化前", "evolves", "前の形")):
            col_map.setdefault("evolves_from", i)
    return col_map


def _parse_row(cells: list[str], col_map: dict[str, int], cells_tags: list[Tag]) -> dict | None:
    """Convert a table row into a card record dict."""
    row = _row_template()

    def get(role: str, default: str = "") -> str:
        idx = col_map.get(role)
        if idx is None or idx >= len(cells):
            return default
        return cells[idx]

    # --- Card name ---
    name_raw = get("name")
    if not name_raw:
        # Try to find a non-empty cell that looks like a card name
        for c in cells:
            if c and not c.isdigit() and len(c) >= 2:
                name_raw = c
                break
    if not name_raw:
        return None

    # Strip set/rarity suffixes that sometimes appear in the name cell
    name_clean = re.sub(r"\s*(◆{1,4}|◇|☆{1,3}|♦{1,4}|♢|[A-Z]\d+-\d+)\s*$", "", name_raw).strip()
    if not name_clean:
        return None

    row["card_name"] = name_clean

    # --- EX / baby ---
    row["is_ex"] = str(_is_ex_name(name_clean))
    row["is_baby"] = str(_is_baby(name_clean))

    # --- HP ---
    hp_raw = get("hp")
    if not hp_raw:
        # Try to find a numeric-only cell that is plausibly HP (30–340)
        for c in cells:
            if re.fullmatch(r"\d+", c) and 30 <= int(c) <= 340:
                hp_raw = c
                break
    row["hp"] = hp_raw

    # Determine if this is a Pokémon or Trainer card
    if row["hp"]:
        row["card_type"] = "Pokemon"
    else:
        row["card_type"] = _detect_trainer_type(cells)

    # --- Type ---
    type_raw = get("type")
    if not type_raw:
        # Try to infer type from alt text of img in the type cell
        for tag in cells_tags:
            img = tag.find("img")
            if img:
                alt = img.get("alt", "")
                if alt:
                    type_raw = alt
                    break
    row["pokemon_type"] = _normalize_type(type_raw) if type_raw else ""

    # --- Stage ---
    stage_raw = get("stage")
    if stage_raw:
        stage_val = _normalize_stage(stage_raw)
        row["stage"] = "" if stage_val is None else str(stage_val)
    elif row["card_type"] == "Pokemon":
        # Default: Basic
        row["stage"] = "0"

    # --- Set name ---
    row["set_name"] = get("set")

    # --- Evolves from (if column exists) ---
    row["evolves_from"] = get("evolves_from")

    # --- Attack columns (if present) ---
    for atk_role, cost_field, dmg_field, flip_field, eff_field in [
        ("atk1", "attack1_energy_cost", "attack1_damage", "attack1_coin_flips", "attack1_effect"),
        ("atk2", "attack2_energy_cost", "attack2_damage", "attack2_coin_flips", "attack2_effect"),
    ]:
        atk_raw = get(atk_role)
        if atk_raw:
            row[cost_field] = _parse_int(atk_raw) or ""
            # Damage often formatted as "60" or "60×"
            dmg_m = re.search(r"(\d+)\s*[×x＋+]?$", atk_raw)
            row[dmg_field] = dmg_m.group(1) if dmg_m else _parse_int(atk_raw)

    return row


def _parse_card_list_items(soup: BeautifulSoup) -> list[dict]:
    """
    Fallback parser for list/grid style card pages (no table structure).
    Looks for common GameWith card link/div patterns.
    """
    records: list[dict] = []
    seen: set[str] = set()

    # Try to find card links like <a href="/pokemon-tcg-pocket/card/xxxxx">カード名</a>
    for a in soup.find_all("a", href=True):
        href = a.get("href", "")
        if "/pokemon-tcg-pocket/" not in href:
            continue
        name = _clean(a.get_text())
        if not name or len(name) < 2 or name in seen:
            continue
        # Avoid navigation/menu links (too short or contain symbols)
        if re.search(r"[【】「」『』\d]{3,}", name):
            continue

        row = _row_template()
        row["card_name"] = name
        row["is_ex"] = str(_is_ex_name(name))
        row["is_baby"] = str(_is_baby(name))
        seen.add(name)
        records.append(row)

    return records


def _dedupe(records: list[dict]) -> list[dict]:
    """Remove duplicate entries (keep first occurrence by card_name)."""
    seen: set[str] = set()
    result: list[dict] = []
    for r in records:
        key = r["card_name"]
        if key and key not in seen:
            seen.add(key)
            result.append(r)
    return result


def _fill_evolves_from(records: list[dict]) -> None:
    """
    Post-processing: for cards that have stage=1 or stage=2 and no evolves_from,
    attempt to fill it in using the _infer_evolves_from heuristic.
    """
    all_names = {r["card_name"] for r in records}
    for r in records:
        if r["card_type"] == "Pokemon" and r["stage"] in ("1", "2") and not r["evolves_from"]:
            guessed = _infer_evolves_from(r["card_name"], all_names)
            if guessed:
                r["evolves_from"] = guessed


def _merge_with_existing(new_records: list[dict], existing_path: Path) -> list[dict]:
    """
    Merge new records with those already in existing_path.
    New records take precedence (overwrite by card_name key).
    Existing records not present in new_records are preserved.
    """
    if not existing_path.exists():
        return new_records

    existing: dict[str, dict] = {}
    with open(existing_path, encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            name = row.get("card_name", "").strip()
            if name:
                # Ensure all expected fields are present
                filled = _row_template()
                filled.update({k: v for k, v in row.items() if k in filled})
                existing[name] = filled

    # New records overwrite existing ones
    for r in new_records:
        existing[r["card_name"]] = r

    return list(existing.values())


def _write_csv(records: list[dict], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(records)
    print(f"[OK] {len(records)} 件を {out_path} に保存しました。")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="GameWith ポケポケ全カードリスト スクレイパー",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--url", default=DEFAULT_URL, help="スクレイピング対象 URL")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT, help="出力 CSV パス")
    parser.add_argument("--timeout", type=int, default=15, help="HTTP タイムアウト秒数")
    parser.add_argument(
        "--merge",
        action="store_true",
        help="既存 CSV の内容と統合する（デフォルト: 上書き）",
    )
    args = parser.parse_args(argv)

    print(f"[INFO] {args.url} を取得中...")
    try:
        html = _fetch_html(args.url, args.timeout)
    except requests.RequestException as exc:
        print(f"[ERROR] ページの取得に失敗しました: {exc}", file=sys.stderr)
        return 1

    soup = BeautifulSoup(html, "html.parser")
    records = _parse_cards(soup)

    if not records:
        print(
            "[WARN] カードデータが見つかりませんでした。\n"
            "       ページ構造が変わっている可能性があります。\n"
            "       data/all_cards.csv の既存データをご確認ください。",
            file=sys.stderr,
        )
        return 2

    _fill_evolves_from(records)

    if args.merge:
        records = _merge_with_existing(records, args.out)
        print(f"[INFO] 既存データと統合後: {len(records)} 件")

    _write_csv(records, args.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
