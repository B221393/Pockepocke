#!/usr/bin/env python3
"""
run_simulation.py – ポケポケ自動対戦シミュレーター CLI

使い方:
    python run_simulation.py [オプション]

オプション:
    -n, --games      試合数 (デフォルト: 1000)
    --seed           乱数シード (省略時はランダム)
    --deck1          デッキ1のJSONパス (省略時は組み込みデッキ)
    --deck2          デッキ2のJSONパス (省略時は組み込みデッキ)
    --all            全デッキの総当たりを実行

例:
    python run_simulation.py -n 10000
    python run_simulation.py --deck1 decks/mega_charizard_deck.json --deck2 decks/darkrai_altaria_deck.json -n 5000
    python run_simulation.py --all -n 1000
"""

from __future__ import annotations

import argparse
import sys
from itertools import combinations
from pathlib import Path

from simulator import simulate

BUILTIN_DECKS = [
    Path("decks/mega_heracross_deck.json"),
    Path("decks/darkrai_altaria_deck.json"),
    Path("decks/mega_charizard_deck.json"),
]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="ポケポケ デッキ勝率シミュレーター",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "-n", "--games",
        type=int,
        default=1000,
        metavar="N",
        help="シミュレーションする試合数 (デフォルト: 1000)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="乱数シード (省略時はランダム)",
    )
    parser.add_argument(
        "--deck1",
        type=Path,
        default=None,
        help="デッキ1のJSONパス",
    )
    parser.add_argument(
        "--deck2",
        type=Path,
        default=None,
        help="デッキ2のJSONパス",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        dest="run_all",
        help="全組み込みデッキの総当たり対戦を実行",
    )

    args = parser.parse_args(argv)

    matchups: list[tuple[Path, Path]] = []

    if args.run_all:
        matchups = list(combinations(BUILTIN_DECKS, 2))
    elif args.deck1 and args.deck2:
        matchups = [(args.deck1, args.deck2)]
    elif args.deck1 or args.deck2:
        parser.error("--deck1 と --deck2 は両方指定してください。")
    else:
        # Default: run all builtin matchups
        matchups = list(combinations(BUILTIN_DECKS, 2))

    print(f"シミュレーション開始: 各対戦 {args.games} 試合\n")

    for deck1_path, deck2_path in matchups:
        result = simulate(deck1_path, deck2_path, n=args.games, seed=args.seed)
        print(result)

    return 0


if __name__ == "__main__":
    sys.exit(main())
