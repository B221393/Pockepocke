import csv
from pathlib import Path

db_path = Path("data/master_card_db.csv")
temp_path = Path("data/master_card_db_temp.csv")

# 完璧な雷軸データの定義
updates = {
    "133": {"name": "イーブイ", "type": "Colorless", "hp": "60", "stage": "0", "attack1_name": "しっぽをふる", "attack1_cost": "1", "attack1_damage": "10"},
    "135": {"name": "サンダース", "type": "Lightning", "hp": "90", "stage": "1", "evolves_from": "イーブイ", "attack1_name": "スピード飛行", "attack1_cost": "2", "attack1_damage": "60"},
    "309": {"name": "ラクライ", "type": "Lightning", "hp": "60", "stage": "0", "attack1_name": "つきとめる", "attack1_cost": "1", "attack1_damage": "10"},
    "310": {"name": "ライボルト", "type": "Lightning", "hp": "90", "stage": "1", "evolves_from": "ラクライ", "attack1_name": "ターボボルト", "attack1_cost": "2", "attack1_damage": "50", "attack1_effect": "energy_accel_from_discard"},
    "10310": {"name": "メガライボルトex", "type": "Lightning", "hp": "210", "stage": "1", "evolves_from": "310", "attack1_name": "ターボボルト", "attack1_cost": "2", "attack1_damage": "110", "attack1_effect": "energy_accel_from_discard"}
}

with open(db_path, "r", encoding="utf-8-sig") as f_in, \
     open(temp_path, "w", newline="", encoding="utf-8-sig") as f_out:
    reader = csv.DictReader(f_in)
    writer = csv.DictWriter(f_out, fieldnames=reader.fieldnames, extrasaction='ignore')
    writer.writeheader()
    
    for row in reader:
        cid = str(row["id"])
        if cid in updates:
            u = updates[cid]
            for k, v in u.items():
                row[k] = v
        writer.writerow(row)

db_path.unlink()
temp_path.rename(db_path)
print("Manectric, Jolteon, and Eevee data updated perfectly.")
