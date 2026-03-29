import requests
from bs4 import BeautifulSoup
import csv
import re
from pathlib import Path

def scrape_gamewith_pokepoke():
    url = "https://gamewith.jp/pokemon-tcg-pocket/462535"
    headers = {"User-Agent": "Mozilla/5.0"}
    
    print(f"Fetching {url}...")
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
    except Exception as e:
        print(f"Error fetching URL: {e}")
        return

    soup = BeautifulSoup(response.text, 'html.parser')
    
    # ターゲットとするCSVのヘッダー (simulator.py用)
    csv_headers = [
        "id", "name", "type", "card_type", "hp", "stage", "evolves_from", 
        "ability", "effect", "attack1_name", "attack1_cost", "attack1_damage", "attack1_effect",
        "attack2_name", "attack2_cost", "attack2_damage", "attack2_effect", "description"
    ]
    
    cards = []
    
    # GameWithのテーブルをすべて走査
    tables = soup.find_all("table")
    print(f"Found {len(tables)} tables. Parsing...")

    current_id = 1
    for table in tables:
        rows = table.find_all("tr")
        if not rows: continue
        
        # ヘッダー確認
        header_cells = [th.get_text(strip=True) for th in rows[0].find_all(["th", "td"])]
        if not any(k in "".join(header_cells) for k in ["名前", "カード名", "ポケモン名"]):
            continue
            
        print(f"Parsing table with headers: {header_cells}")
        
        # カラムインデックスの特定
        col_map = {}
        for i, h in enumerate(header_cells):
            if "名前" in h or "カード名" in h or "ポケモン名" in h: col_map["name"] = i
            if "HP" in h or "体力" in h: col_map["hp"] = i
            if "タイプ" in h: col_map["type"] = i
            if "ワザ" in h or "技" in h:
                if "1" in h or "ワザ名" in h: col_map["atk1_name"] = i
                if "ダメージ" in h: col_map["atk1_damage"] = i
                if "コスト" in h: col_map["atk1_cost"] = i

        for tr in rows[1:]:
            cells = tr.find_all("td")
            if len(cells) < 2: continue
            
            name = cells[col_map.get("name", 0)].get_text(strip=True)
            if not name or "未設定" in name: continue
            
            # 簡易的なデータ抽出 (進化前などは個別ページを見ないと正確には取れないが、名前から推測)
            hp = cells[col_map.get("hp", 1)].get_text(strip=True) if "hp" in col_map else ""
            p_type = ""
            # タイプアイコンのalt属性などを探す
            type_td = cells[col_map.get("type", 2)] if "type" in col_map else None
            if type_td:
                img = type_td.find("img")
                if img: p_type = img.get("alt", "").replace("タイプ", "")
            
            atk_name = cells[col_map.get("atk1_name", 4)].get_text(strip=True) if "atk1_name" in col_map else ""
            atk_dmg = cells[col_map.get("atk1_damage", 5)].get_text(strip=True) if "atk1_damage" in col_map else ""
            atk_cost = cells[col_map.get("atk1_cost", 3)].get_text(strip=True) if "atk1_cost" in col_map else ""

            # ダメージから数値を抽出
            dmg_val = "".join(filter(str.isdigit, atk_dmg)) or "0"
            
            # カードIDは連番で振り直し (ユーザーの要望通り無駄を省く)
            card = {
                "id": current_id,
                "name": name,
                "type": p_type,
                "card_type": "Pokemon" if hp else "Trainer",
                "hp": hp,
                "stage": "0", # デフォルト
                "evolves_from": "",
                "ability": "",
                "effect": "",
                "attack1_name": atk_name,
                "attack1_cost": atk_cost,
                "attack1_damage": dmg_val,
                "attack1_effect": "",
                "attack2_name": "",
                "attack2_cost": "",
                "attack2_damage": "",
                "attack2_effect": "",
                "description": ""
            }
            cards.append(card)
            current_id += 1

    # 重複排除
    unique_cards = []
    seen = set()
    for c in cards:
        if c["name"] not in seen:
            seen.add(c["name"])
            unique_cards.append(c)

    # 保存
    output_path = Path("data/master_card_db.csv")
    with open(output_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=csv_headers)
        writer.writeheader()
        writer.writerows(unique_cards)
    
    print(f"Successfully scraped {len(unique_cards)} cards to {output_path}")
    
    # サンプルの表示
    print("\n--- Samples for Verification ---")
    for c in unique_cards[:5]:
        print(f"Name: {c['name']}, HP: {c['hp']}, Type: {c['type']}, Atk: {c['attack1_name']}, Dmg: {c['attack1_damage']}")

if __name__ == "__main__":
    scrape_gamewith_pokepoke()
