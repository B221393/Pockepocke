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
        if str(row["id"]) == "433":
            row["name"] = "リーシャン"
            row["attack1_name"] = "ねがいをかなえる"
            row["attack1_damage"] = "0"
            row["attack1_effect"] = "lock_item"
            row["description"] = "次の相手の番、グッズを使わせない"
        writer.writerow(row)

db_path.unlink()
temp_path.rename(db_path)
print("Chimecho updated to Item Lock (Goods Lock).")
