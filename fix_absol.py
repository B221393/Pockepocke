import csv
from pathlib import Path

db_path = Path("data/master_card_db.csv")
temp_path = Path("data/master_card_db_temp.csv")

with open(db_path, "r", encoding="utf-8-sig") as f_in, \
     open(temp_path, "w", newline="", encoding="utf-8-sig") as f_out:
    reader = csv.DictReader(f_in)
    writer = csv.DictWriter(f_out, fieldnames=reader.fieldnames)
    writer.writeheader()
    
    found = False
    for row in reader:
        if str(row["id"]) == "10359":
            row["name"] = "メガアブソルex"
            row["type"] = "Dark"
            row["hp"] = "210"
            row["stage"] = "1"
            row["evolves_from"] = "359"
            row["attack1_name"] = "ディザスタークロー"
            row["attack1_cost"] = "3"
            row["attack1_damage"] = "120"
            row["attack1_effect"] = "lock_supporter"
            row["description"] = "相手のサポーターを封じる"
            found = True
        writer.writerow(row)
    
    # もし見つからなければ末尾に追加
    if not found:
        writer.writerow({
            "id": "10359", "name": "メガアブソルex", "type": "Dark", "card_type": "Pokemon",
            "hp": "210", "stage": "1", "evolves_from": "359", "attack1_name": "ディザスタークロー",
            "attack1_cost": "3", "attack1_damage": "120", "attack1_effect": "lock_supporter",
            "description": "相手のサポーターを封じる"
        })

db_path.unlink()
temp_path.rename(db_path)
print("Mega Absol ex updated successfully.")
