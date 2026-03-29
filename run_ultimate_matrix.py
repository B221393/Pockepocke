import os
import json
import csv
from pathlib import Path
from simulator import simulate
from datetime import datetime

def run_ultimate_matrix():
    print("--- 究極のメタゲーム・マトリックス・シミュレーション開始 ---")
    
    # 全デッキを取得
    all_decks = []
    deck_dirs = [Path("decks/meta"), Path("decks/experimental"), Path("decks/archetypes"), Path("decks/ex_axes")]
    
    for ddir in deck_dirs:
        if ddir.exists():
            for p in ddir.glob("**/*.json"):
                try:
                    with open(p, encoding="utf-8") as f:
                        data = json.load(f)
                        if "name" in data and "cards" in data and len(data["cards"]) > 0:
                            all_decks.append({
                                "path": p,
                                "name": data["name"],
                                "folder": p.parent.name
                            })
                except Exception as e:
                    print(f"Error loading {p}: {e}")

    # 100種類以上あると10000試合になるため、上位30デッキ程度に絞るか、または全対戦10試合で回すか
    # 今回は「すごいAI」の検証のため、各対戦50試合で全件総当たり（最大でも数十デッキ）を実行
    
    # 負荷軽減のため、代表的なデッキのみを抽出（1フォルダ最大5デッキ等）
    selected_decks = []
    folder_counts = {}
    for d in all_decks:
        c = folder_counts.get(d["folder"], 0)
        if c < 3: # 1アーキタイプにつき3バージョンまで
            selected_decks.append(d)
            folder_counts[d["folder"]] = c + 1
            
    # さらに、特定されたメタデッキや実験デッキは必ず含める
    for d in all_decks:
        if "meta" in str(d["path"]) or "experimental" in str(d["path"]):
            if d not in selected_decks:
                selected_decks.append(d)

    n_decks = len(selected_decks)
    print(f"対象デッキ数: {n_decks} (総対戦数: {n_decks * (n_decks - 1)})")
    
    matrix = []
    
    for i, d1 in enumerate(selected_decks):
        row = {"Deck": f"[{d1['folder']}] {d1['name']}"}
        win_rates = []
        for j, d2 in enumerate(selected_decks):
            if i == j:
                row[f"[{d2['folder']}] {d2['name']}"] = "-"
                continue
            
            try:
                res = simulate(str(d1["path"]), str(d2["path"]), n=50)
                wr = res.deck1_win_rate
                row[f"[{d2['folder']}] {d2['name']}"] = f"{wr:.1%}"
                win_rates.append(wr)
            except Exception as e:
                print(f"Simulation error {d1['name']} vs {d2['name']}: {e}")
                row[f"[{d2['folder']}] {d2['name']}"] = "ERR"
                
        if win_rates:
            row["Average Win Rate"] = f"{sum(win_rates)/len(win_rates):.1%}"
        else:
            row["Average Win Rate"] = "0.0%"
            
        matrix.append(row)
        print(f"Completed {i+1}/{n_decks}: {d1['name']} (Avg: {row['Average Win Rate']})")

    # CSV保存
    out_dir = Path("data")
    out_dir.mkdir(exist_ok=True)
    csv_path = out_dir / "ultimate_meta_matrix.csv"
    
    fieldnames = ["Deck", "Average Win Rate"] + [f"[{d['folder']}] {d['name']}" for d in selected_decks]
    
    with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(matrix)

    # HTMLレポート生成
    html_path = out_dir / "ultimate_meta_report.html"
    html_content = f"""
    <html>
    <head>
        <title>ポケポケ 究極メタゲーム・マトリックス</title>
        <style>
            body {{ font-family: sans-serif; margin: 20px; background-color: #1e1e1e; color: #fff; }}
            h1 {{ color: #00ffcc; }}
            table {{ border-collapse: collapse; width: 100%; margin-top: 20px; font-size: 12px; }}
            th, td {{ border: 1px solid #444; padding: 8px; text-align: center; }}
            th {{ background-color: #333; position: sticky; top: 0; }}
            td:first-child {{ text-align: left; font-weight: bold; background-color: #2a2a2a; position: sticky; left: 0; }}
            .high-win {{ background-color: rgba(0, 255, 0, 0.2); color: #0f0; font-weight: bold; }}
            .low-win {{ background-color: rgba(255, 0, 0, 0.2); color: #f66; }}
            .avg-col {{ background-color: #224466; font-weight: bold; font-size: 14px; }}
        </style>
    </head>
    <body>
        <h1>究極メタゲーム・マトリックス (Advanced AI)</h1>
        <p>生成日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p>対戦数: 各組み合わせ50試合（手札事故による再引き直し考慮済）</p>
        
        <table>
            <tr>
    """
    for f in fieldnames:
        html_content += f"<th>{f}</th>"
    html_content += "</tr>\n"
    
    for row in matrix:
        html_content += "<tr>"
        for col in fieldnames:
            val = row.get(col, "")
            class_name = ""
            if col == "Average Win Rate":
                class_name = "avg-col"
            elif "%" in val and val != "-":
                num = float(val.replace("%", ""))
                if num >= 60.0: class_name = "high-win"
                elif num <= 40.0: class_name = "low-win"
                
            html_content += f'<td class="{class_name}">{val}</td>'
        html_content += "</tr>\n"
        
    html_content += """
        </table>
    </body>
    </html>
    """
    
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"\\n--- 究極シミュレーション完了 ---")
    print(f"CSVレポート: {csv_path}")
    print(f"HTMLレポート: {html_path} (ブラウザで開いて確認してください)")

if __name__ == "__main__":
    run_ultimate_matrix()
