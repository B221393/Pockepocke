import json
import csv
from pathlib import Path

# --- 変換マッピング ---
TYPE_MAP = {
    "草": "Grass", "火": "Fire", "水": "Water", "雷": "Lightning", 
    "超": "Psychic", "闘": "Fighting", "悪": "Dark", "鋼": "Metal", 
    "竜": "Dragon", "無": "Colorless"
}

TRAINER_TYPE_MAP = {
    "サ": "Supporter", "グ": "Item", "ス": "Stadium"
}

def convert_gamewith_to_master(gw_data):
    master_rows = []
    
    for d in gw_data:
        card_id = d.get("id")
        name = d.get("n", "")
        raw_type = d.get("t", "")
        category = d.get("c", "") # P=Pokemon, T=Trainer
        
        hp = d.get("hp", "")
        
        # ワザの抽出
        attacks = d.get("mv", [])
        a1_name = attacks[0].get("n", "") if len(attacks) > 0 else ""
        a1_damage = attacks[0].get("v", "") if len(attacks) > 0 else ""
        a1_cost = attacks[0].get("c1", {}).get("count", "") if len(attacks) > 0 else ""
        
        a2_name = attacks[1].get("n", "") if len(attacks) > 1 else ""
        a2_damage = attacks[1].get("v", "") if len(attacks) > 1 else ""
        a2_cost = attacks[1].get("c1", {}).get("count", "") if len(attacks) > 1 else "" # 簡易化

        # カードタイプ判定
        card_type = "Pokemon" if category == "P" else TRAINER_TYPE_MAP.get(raw_type, "Trainer")
        mapped_type = TYPE_MAP.get(raw_type, raw_type) if card_type == "Pokemon" else "-"

        # 進化判定 (o: "ba"=たね, "1e"=1進化, "2e"=2進化)
        stage_map = {"ba": 0, "1e": 1, "2e": 2}
        stage = ""
        if d.get("o") and len(d.get("o")) > 0:
            stage = stage_map.get(d.get("o")[0], "")

        row = {
            "id": card_id,
            "name": name,
            "type": mapped_type,
            "card_type": card_type,
            "hp": hp,
            "stage": stage,
            "evolves_from": "", # 必要に応じて追加解析
            "ability": d.get("ability", ""),
            "effect": d.get("txt", ""),
            "attack1_name": a1_name,
            "attack1_cost": a1_cost,
            "attack1_damage": a1_damage,
            "attack1_effect": "",
            "attack2_name": a2_name,
            "attack2_cost": a2_cost,
            "attack2_damage": a2_damage,
            "attack2_effect": "",
            "description": f"Source: {d.get('link', '')}"
        }
        master_rows.append(row)
        
    return master_rows

def save_to_csv(rows, path):
    if not rows: return
    headers = rows[0].keys()
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)

if __name__ == "__main__":
    # このスクリプトは直接実行せず、chrome-devtoolsで取得したJSONを食わせる想定
    pass
