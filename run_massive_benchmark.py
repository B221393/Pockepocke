import json
import csv
import random
from pathlib import Path
from simulator import simulate

def run_massive_benchmark():
    print("--- 20デッキ・100試合徹底比較ベンチマーク開始 ---")
    
    # 20種類の代表的デッキを収集
    selected_decks = []
    
    # 1. metaから
    meta_dir = Path("decks/archetypes")
    # 各フォルダから1-2個ずつ代表をピックアップ
    archetype_folders = ["energy_accel", "evolve_power", "hand_dest", "sleep", "gimmick"]
    for folder in archetype_folders:
        path = meta_dir / folder
        if path.exists():
            files = list(path.glob("*.json"))
            if files:
                # 最新・最強と思われるものを1つ選ぶ
                best = sorted(files, key=lambda x: x.name, reverse=True)[0]
                selected_decks.append(best)

    # 2. 実験用（リーシャン、アブソル、ライボルト、水なしゲッコウガ）
    exp_dir = Path("decks/experimental")
    if exp_dir.exists():
        selected_decks.extend(list(exp_dir.glob("*.json")))

    # 3. ex軸から足りないタイプを補完
    ex_dir = Path("decks/ex_axes")
    if ex_dir.exists():
        for d in ex_dir.glob("**/standard_axis.json"):
            if len(selected_decks) < 20:
                if d not in selected_decks:
                    selected_decks.append(d)

    # 重複削除と数調整
    unique_paths = list(dict.fromkeys(selected_decks))[:20]
    n_decks = len(unique_paths)
    
    deck_info = []
    for p in unique_paths:
        with open(p, encoding="utf-8") as f:
            data = json.load(f)
            deck_info.append({"path": p, "name": f"[{p.parent.name}] {data['name']}"})

    print(f"比較対象: {n_decks} デッキ / 試合数: 各100戦")
    
    matrix = []
    for i, d1 in enumerate(deck_info):
        row = {"Deck": d1["name"]}
        win_rates = []
        for j, d2 in enumerate(deck_info):
            if i == j:
                row[d2["name"]] = "-"
                continue
            
            # 100戦シミュレーション
            res = simulate(str(d1["path"]), str(d2["path"]), n=100)
            wr = res.deck1_win_rate
            row[d2["name"]] = f"{wr:.1%}"
            win_rates.append(wr)
            
        row["Avg Win Rate"] = f"{sum(win_rates)/len(win_rates):.1%}"
        matrix.append(row)
        print(f"Finished {i+1}/{n_decks}: {d1['name']} (Avg: {row['Avg Win Rate']})")

    # 結果保存
    output_path = Path("data/massive_benchmark_100.csv")
    fieldnames = ["Deck", "Avg Win Rate"] + [d["name"] for d in deck_info]
    with open(output_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(matrix)

    print(f"\n--- ベンチマーク完了! 結果を保存しました: {output_path}")

if __name__ == "__main__":
    run_massive_benchmark()
