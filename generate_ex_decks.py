import csv
import json
from pathlib import Path

def generate_ex_axis_decks():
    db_path = Path("data/master_card_db.csv")
    output_root = Path("decks/ex_axes")
    output_root.mkdir(parents=True, exist_ok=True)
    
    # 必須級の汎用パーツ
    STAPLES = ["1003", "1003", "1006", "2006", "2001", "2001", "2002", "2002", "1005", "1001"] # 10枚
    
    ex_list = []
    with open(db_path, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if "ex" in row["name"].lower():
                ex_list.append(row)
    
    print(f"特定されたexカード: {len(ex_list)}種類")
    
    deck_count = 0
    for ex in ex_list:
        cid = str(ex["id"])
        name = ex["name"].replace("/", "_").replace(" ", "_")
        
        # デッキ構築: ex 4枚 + 汎用10枚 + 残り6枚（進化前やサポートで調整）
        # 進化前の特定（簡易的にID-1, ID-2をチェック）
        pre_evolutions = []
        if ex["evolves_from"]:
            pre_evolutions.append(ex["evolves_from"])
            # さらにその前があるか（2進化の場合）
            # ここでは簡易的にマスターDBを再走査せず、軸カードを厚くする構成にする
        
        deck_ids = [cid] * 4
        if pre_evolutions:
            deck_ids += pre_evolutions * 3
        else:
            deck_ids += [cid] * 2 # たねexなら多めに
            
        deck_ids += STAPLES
        
        # 20枚になるまで調整
        while len(deck_ids) < 20:
            deck_ids.append("1003") # 足りなければドローソース
        deck_ids = deck_ids[:20]
        
        # 保存
        folder = output_root / name
        folder.mkdir(exist_ok=True)
        file_path = folder / "standard_axis.json"
        
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump({"name": f"{ex['name']} 軸", "cards": deck_ids}, f, ensure_ascii=False, indent=2)
        
        deck_count += 1
        if deck_count >= 50: break # 一旦上位50種に絞る

    print(f"{deck_count}種類のex軸デッキを生成しました: {output_root}")

if __name__ == "__main__":
    generate_ex_axis_decks()
