import csv
from pathlib import Path
import json

def generate_master_db():
    output_csv = Path("data/master_card_db.csv")
    
    # 既存のデータを読み込む (card_db.json)
    existing_db_path = Path("data/card_db.json")
    existing_data = {"pokemon": {}, "trainers": {}}
    if existing_db_path.exists():
        with open(existing_db_path, "r", encoding="utf-8") as f:
            existing_data = json.load(f)

    # 統合用の辞書
    pokemon_map = {int(k): v for k, v in existing_data.get("pokemon", {}).items()}
    trainer_map = {int(k): v for k, v in existing_data.get("trainers", {}).items()}

    # CSVのヘッダー
    headers = [
        "id", "name", "type", "card_type", "hp", "stage", "evolves_from", 
        "ability", "effect", "attack1_name", "attack1_cost", "attack1_damage", "attack1_effect",
        "attack2_name", "attack2_cost", "attack2_damage", "attack2_effect", "description"
    ]

    rows = []
    
    # 1 ~ 2000: ポケモン枠
    for i in range(1, 2001):
        if i in pokemon_map:
            p = pokemon_map[i]
            # 既存のデータをCSVフォーマットに変換
            a1 = p.get("attacks", [{}])[0] if len(p.get("attacks", [])) > 0 else {}
            a2 = p.get("attacks", [{}])[1] if len(p.get("attacks", [])) > 1 else {}
            rows.append({
                "id": i, "name": p.get("name", ""), "type": p.get("type", ""), "card_type": "Pokemon",
                "hp": p.get("hp", ""), "stage": p.get("stage", ""), "evolves_from": p.get("evolves_from", ""),
                "ability": p.get("ability", ""), "effect": p.get("effect", ""),
                "attack1_name": a1.get("name", ""), "attack1_cost": a1.get("energy_cost", ""), 
                "attack1_damage": a1.get("damage", ""), "attack1_effect": a1.get("effect", ""),
                "attack2_name": a2.get("name", ""), "attack2_cost": a2.get("energy_cost", ""), 
                "attack2_damage": a2.get("damage", ""), "attack2_effect": a2.get("effect", ""),
                "description": ""
            })
        else:
            # 空のテンプレート
            rows.append({
                "id": i, "name": f"未設定ポケモン_{i}", "type": "", "card_type": "Pokemon",
                "hp": "", "stage": "", "evolves_from": "", "ability": "", "effect": "",
                "attack1_name": "", "attack1_cost": "", "attack1_damage": "", "attack1_effect": "",
                "attack2_name": "", "attack2_cost": "", "attack2_damage": "", "attack2_effect": "",
                "description": ""
            })

    # 2001 ~ 2600: トレーナーズ・グッズ枠
    for i in range(2001, 2601):
        # jsonのキーは文字列なので注意（以前は1000番台も使っていたが、便宜上統合）
        t_id = i
        # 以前のID(1001等)がもしあれば引き継ぎたいが、ここでは簡略化のため
        # trainer_map にあるものを優先して上書きしていく
        t_data = trainer_map.get(t_id)
        if not t_data and (i - 1000) in trainer_map:
            # 1001等のサポートを2000番台にシフト（またはそのまま維持）
            # 今回はIDを変えない方が良いので、ループ外で追加する
            pass

    # IDを崩さないように、既存のトレーナーをそのまま追加
    for tid, t in trainer_map.items():
        rows.append({
            "id": tid, "name": t.get("name", ""), "type": "", "card_type": t.get("card_type", ""),
            "hp": "", "stage": "", "evolves_from": "", "ability": "", "effect": t.get("effect", ""),
            "attack1_name": "", "attack1_cost": "", "attack1_damage": "", "attack1_effect": "",
            "attack2_name": "", "attack2_cost": "", "attack2_damage": "", "attack2_effect": "",
            "description": t.get("description", "")
        })

    # 空のトレーナー枠を2100~2600に追加
    for i in range(2100, 2601):
        if i not in trainer_map:
            rows.append({
                "id": i, "name": f"未設定トレーナー_{i}", "type": "", "card_type": "Trainer",
                "hp": "", "stage": "", "evolves_from": "", "ability": "", "effect": "",
                "attack1_name": "", "attack1_cost": "", "attack1_damage": "", "attack1_effect": "",
                "attack2_name": "", "attack2_cost": "", "attack2_damage": "", "attack2_effect": "",
                "description": ""
            })

    # 重複排除してソート
    unique_rows = {r["id"]: r for r in rows}
    sorted_rows = [unique_rows[k] for k in sorted(unique_rows.keys())]

    with open(output_csv, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(sorted_rows)

    print(f"2600枚対応のマスターデータベースを生成しました: {output_csv}")

if __name__ == "__main__":
    generate_master_db()
