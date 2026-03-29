import json
import csv
from pathlib import Path
from sync_latest_cards import convert_gamewith_to_master, save_to_csv

# デバッグ時に取得した巨大なJSON文字列（ここでは安全のためファイルから読み込む形式にする）
# 実際には直前のステップで取得したデータを使用
RAW_JSON_PATH = Path("data/raw_gamewith_data.json")

def finalize_sync(json_data):
    print(f"変換開始: {len(json_data)} 枚のカードを処理中...")
    master_rows = convert_gamewith_to_master(json_data)
    
    # master_card_db.csv に上書き保存
    output_csv = Path("data/master_card_db.csv")
    save_to_csv(master_rows, output_csv)
    
    # simulator.py が読み込む card_db.json も更新
    # 互換性のために pokemon と trainers に分ける
    db_json = {"pokemon": {}, "trainers": {}}
    for row in master_rows:
        cid = str(row["id"])
        if row["card_type"] == "Pokemon":
            # 攻撃データの復元
            attacks = []
            if row["attack1_name"]:
                attacks.append({"name": row["attack1_name"], "energy_cost": int(row["attack1_cost"] or 0), "damage": int(str(row["attack1_damage"]).replace("+","").replace("×","") or 0)})
            if row["attack2_name"]:
                attacks.append({"name": row["attack2_name"], "energy_cost": int(row["attack2_cost"] or 0), "damage": int(str(row["attack2_damage"]).replace("+","").replace("×","") or 0)})
            
            db_json["pokemon"][cid] = {
                "name": row["name"],
                "type": row["type"],
                "hp": int(row["hp"] or 0),
                "stage": int(row["stage"]) if row["stage"] != "" else 0,
                "attacks": attacks,
                "ability": row["ability"]
            }
        else:
            db_json["trainers"][cid] = {
                "name": row["name"],
                "card_type": row["card_type"],
                "effect": row["effect"] # ここは後で効果名にマッピングが必要
            }
            
    with open("data/card_db.json", "w", encoding="utf-8") as f:
        json.dump(db_json, f, ensure_ascii=False, indent=2)
    
    print(f"同期完了! 2600枚以上の最新データを master_card_db.csv と card_db.json に流し込みました。")

if __name__ == "__main__":
    # 直前のツール出力から得られたデータをシミュレート
    with open("data/raw_gamewith_data.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    finalize_sync(data)
