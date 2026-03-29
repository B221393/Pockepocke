import csv
from pathlib import Path

db_path = Path("data/master_card_db.csv")
temp_path = Path("data/master_card_db_temp.csv")

with open(db_path, "r", encoding="utf-8-sig") as f_in, \
     open(temp_path, "w", newline="", encoding="utf-8-sig") as f_out:
    reader = csv.DictReader(f_in)
    writer = csv.DictWriter(f_out, fieldnames=reader.fieldnames)
    writer.writeheader()
    
    for row in reader:
        cid = str(row["id"])
        if cid == "309":
            row["name"], row["type"], row["hp"], row["stage"] = "ラクライ", "Lightning", "60", "0"
            row["attack1_name"], row["attack1_cost"], row["attack1_damage"] = "つきとめる", "1", "10"
        elif cid == "310":
            row["name"], row["type"], row["hp"], row["stage"], row["evolves_from"] = "ライボルトex", "Lightning", "170", "0", ""
            row["attack1_name"], row["attack1_cost"], row["attack1_damage"] = "オーバーラン", "1", "20"
            row["attack2_name"], row["attack2_cost"], row["attack2_damage"] = "アサルトレーザー", "2", "60"
        elif cid == "10310":
            row["name"], row["type"], row["hp"], row["stage"], row["evolves_from"] = "メガライボルトex", "Lightning", "210", "1", "310"
            row["attack1_name"], row["attack1_cost"], row["attack1_damage"], row["attack1_effect"] = "ターボボルト", "2", "110", "energy_accel_from_discard"
            row["description"] = "トラッシュからエネ2個加速"
        writer.writerow(row)

db_path.unlink()
temp_path.rename(db_path)
print("Mega Manectric ex (メガライボルト) implemented.")
