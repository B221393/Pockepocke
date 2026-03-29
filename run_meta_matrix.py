import os
import json
import csv
from pathlib import Path
from simulator import simulate

def run_matrix():
    meta_dir = Path("decks/meta")
    exp_dir = Path("decks/experimental")
    
    deck_paths = list(meta_dir.glob("*.json")) + list(exp_dir.glob("*.json"))
    deck_names = []
    for p in deck_paths:
        with open(p, encoding="utf-8") as f:
            deck_names.append(json.load(f)["name"])
            
    matrix = []
    
    print(f"--- メタゲーム・マトリックス・シミュレーション開始 ({len(deck_paths)} デッキ) ---")
    
    for i, p1 in enumerate(deck_paths):
        row = {"Deck": deck_names[i]}
        for j, p2 in enumerate(deck_paths):
            if i == j:
                row[deck_names[j]] = "-"
                continue
            
            # 各対戦100試合
            res = simulate(p1, p2, n=100)
            row[deck_names[j]] = f"{res.deck1_win_rate:.1%}"
            
        matrix.append(row)
        print(f"Progress: Completed matchups for {deck_names[i]}")

    # 結果保存
    fieldnames = ["Deck"] + deck_names
    with open("data/meta_matrix_results.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(matrix)

    print("\n--- シミュレーション完了! data/meta_matrix_results.csv を確認してください ---")

if __name__ == "__main__":
    run_matrix()
