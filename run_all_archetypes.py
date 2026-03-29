import os
import json
import csv
from pathlib import Path
from simulator import simulate

def run_archetype_matrix():
    archetype_root = Path("decks/archetypes")
    # すべてのサブフォルダ内のJSONを取得
    deck_paths = list(archetype_root.glob("**/*.json"))
    deck_names = []
    for p in deck_paths:
        with open(p, encoding="utf-8") as f:
            data = json.load(f)
            # フォルダ名も含めて表示
            folder = p.parent.name
            deck_names.append(f"[{folder}] {data['name']}")
            
    matrix = []
    print(f"--- 戦術別（アーキタイプ）総当たりシミュレーション開始 ({len(deck_paths)} デッキ) ---")
    
    for i, p1 in enumerate(deck_paths):
        row = {"Deck": deck_names[i]}
        for j, p2 in enumerate(deck_paths):
            if i == j:
                row[deck_names[j]] = "-"
                continue
            
            res = simulate(p1, p2, n=100)
            row[deck_names[j]] = f"{res.deck1_win_rate:.1%}"
            
        matrix.append(row)
        print(f"Completed: {deck_names[i]}")

    # 結果保存
    fieldnames = ["Deck"] + deck_names
    output_path = Path("data/archetype_evolution_matrix.csv")
    with open(output_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(matrix)

    print(f"\n--- 完了! 戦術の変遷（相性表）を保存しました: {output_path}")

if __name__ == "__main__":
    run_archetype_matrix()
