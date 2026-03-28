#!/usr/bin/env python3
"""
fetch_gamewith.py – GameWith ポケポケ デッキ情報スクレイパー

GameWith の下記ページからデッキのティア・使用率・勝率などを取得し、
data/gamewith_decks.csv に保存します。

    https://gamewith.jp/pokemon-tcg-pocket/463660

使い方:
    pip install requests beautifulsoup4
    python fetch_gamewith.py

オプション:
    --url URL       スクレイピング対象 URL (デフォルト: 上記 URL)
    --out PATH      出力 CSV パス (デフォルト: data/gamewith_decks.csv)
    --timeout N     HTTP タイムアウト秒数 (デフォルト: 15)
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
    from bs4 import BeautifulSoup
except ImportError as exc:
    print(
        f"[ERROR] 必要ライブラリが見つかりません: {exc}\n"
        "  pip install requests beautifulsoup4\n"
        "を実行してからもう一度お試しください。",
        file=sys.stderr,
    )
    sys.exit(1)

DEFAULT_URL = "https://gamewith.jp/pokemon-tcg-pocket/463660"
DEFAULT_OUT = Path("data/gamewith_decks.csv")

# CSV column names (also written as the header row)
CSV_FIELDS = [
    "deck_name",        # デッキ名
    "tier",             # ティア (S/A/B/C)
    "usage_rate",       # 使用率 (%)
    "win_rate",         # 勝率 (%)
    "main_pokemon",     # メインポケモン
    "energy_type",      # タイプ (Fire/Water/…)
    "main_pokemon_hp",  # メインアタッカー HP
    "main_attack_damage",      # メインわざ ダメージ
    "main_attack_energy_cost", # メインわざ エネルギーコスト
    "is_ex",            # EX ポケモン (True/False)
    "has_evolution",    # 進化ポケモンあり (True/False)
    "deck_style",       # アグロ/コントロール/バランス
    "description",      # 特徴
]


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


def _pct_to_float(text: str) -> str:
    """'62.3%' → '62.3'. Returns '' if not parseable."""
    m = re.search(r"[\d.]+", text)
    return m.group() if m else ""


def _parse_tier_label(text: str) -> str:
    for t in ("S+", "S", "A", "B", "C"):
        if t in text:
            return t
    return ""


def _parse_decks(soup: BeautifulSoup) -> list[dict]:
    """
    GameWith のデッキ強さランキング記事から行データを抽出します。

    記事構造の例:
      <h2 class="...">Sランク</h2>
      <table>
        <tbody>
          <tr> ... </tr>
        </tbody>
      </table>

    見つかったテーブルをすべてパース。ティアは直前の h2/h3/h4 見出しから推定。
    """
    rows: list[dict] = []
    current_tier = ""

    for element in soup.find_all(["h2", "h3", "h4", "table"]):
        tag = element.name
        if tag in ("h2", "h3", "h4"):
            text = _clean(element.get_text())
            tier = _parse_tier_label(text)
            if tier:
                current_tier = tier
            continue

        # It's a <table>
        for tr in element.find_all("tr"):
            cells = [_clean(td.get_text()) for td in tr.find_all(["td", "th"])]
            if not cells or all(c == "" for c in cells):
                continue
            # Skip header rows
            if cells[0].lower() in ("デッキ", "deck", "デッキ名"):
                continue

            row = _row_from_cells(cells, current_tier)
            if row and row["deck_name"]:
                rows.append(row)

    # De-duplicate by deck_name (keep first occurrence)
    seen: set[str] = set()
    deduped: list[dict] = []
    for r in rows:
        if r["deck_name"] not in seen:
            seen.add(r["deck_name"])
            deduped.append(r)
    return deduped


def _row_from_cells(cells: list[str], tier: str) -> dict:
    """Try to map a list of table cell strings to a deck row dict."""
    row: dict = {f: "" for f in CSV_FIELDS}
    row["tier"] = tier

    # Heuristic: first non-empty cell is deck name
    for c in cells:
        if c:
            row["deck_name"] = c
            break

    # Look for percentage values → usage_rate / win_rate
    pcts = [c for c in cells if re.search(r"\d+\.?\d*%", c)]
    if len(pcts) >= 1:
        row["usage_rate"] = _pct_to_float(pcts[0])
    if len(pcts) >= 2:
        row["win_rate"] = _pct_to_float(pcts[1])

    # Tier in cells takes precedence
    for c in cells:
        t = _parse_tier_label(c)
        if t:
            row["tier"] = t
            break

    # Join remaining cells as description
    row["description"] = " | ".join(c for c in cells if c and c != row["deck_name"])

    return row


def _write_csv(records: list[dict], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(records)
    print(f"[OK] {len(records)} 件を {out_path} に保存しました。")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="GameWith デッキ情報スクレイパー",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--url", default=DEFAULT_URL, help="スクレイピング対象 URL")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT, help="出力 CSV パス")
    parser.add_argument("--timeout", type=int, default=15, help="HTTP タイムアウト秒数")
    args = parser.parse_args(argv)

    print(f"[INFO] {args.url} を取得中...")
    try:
        html = _fetch_html(args.url, args.timeout)
    except requests.RequestException as exc:
        print(f"[ERROR] ページの取得に失敗しました: {exc}", file=sys.stderr)
        return 1

    soup = BeautifulSoup(html, "html.parser")
    records = _parse_decks(soup)

    if not records:
        print(
            "[WARN] テーブルデータが見つかりませんでした。\n"
            "       ページ構造が変わっている可能性があります。\n"
            "       data/gamewith_decks.csv の既存データをご確認ください。",
            file=sys.stderr,
        )
        return 2

    _write_csv(records, args.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
