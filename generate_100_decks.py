import json
import csv
import random
from pathlib import Path

# --- 設定 ---
ARCHETYPES = ["sleep", "hand_dest", "energy_accel", "evolve_power", "gimmick", "control", "one_shot"]
CORE_PATH = Path("decks/archetypes")

# 軸となるポケモンのIDセット (master_card_db.csvから抜粋)
AXIS_POKEMON = {
    "fire": ["2564", "146"],    # メガリザードンX, ファイヤーex
    "water": ["121", "144"],    # スターミーex, フリーザーex
    "lightning": ["25", "145"], # ピカチュウex, サンダーex
    "psychic": ["150", "94"],   # ミュウツーex, ゲンガーex
    "dark": ["491", "10359"],   # ダークライex, メガアブソルex
    "dragon": ["612", "149"],   # オノノクス, カイリューex
    "colorless": ["40", "143"]  # プクリンex, カビゴン
}

# 必須級サポーター/グッズ
STAPLE_TRAINERS = ["1003", "1003", "1006", "2006", "2001", "2001", "2002", "2002", "2003", "2003"] # 10枚

def generate_100_decks():
    deck_count = 0
    
    for archetype, axis_ids in AXIS_POKEMON.items():
        for axis_id in axis_ids:
            # 各軸に対して 7~8 パターンの変遷（遷移）を作成
            for v in range(1, 8):
                # 基本構成: 軸ポケモンとその進化前(適当に推測またはID固定)
                # 今回は簡略化のため、軸IDを4枚、スタプル10枚、残りをランダムなメタカードで埋める
                deck_ids = [axis_id] * 4
                deck_ids += STAPLE_TRAINERS
                
                # 残り6枚をメタカード（ナツメ、サカキ、レッドカード、アイリス、ものまね娘）から選択
                meta_pool = ["1001", "1004", "1005", "1002", "1006", "2005", "2006"]
                # バージョンによって比率を変える
                if v == 1: # Speed重視
                    extra = ["1004", "1004", "2003", "2003", "1003", "1003"]
                elif v == 2: # 安定重視
                    extra = ["1006", "1006", "2006", "2006", "2001", "2001"]
                elif v == 3: # 妨害重視
                    extra = ["1002", "1002", "2005", "2005", "1005", "1005"]
                else: # 混合・究極への繊維
                    random.shuffle(meta_pool)
                    extra = meta_pool[:6]
                
                deck_ids += extra
                
                # フォルダ振り分け
                target_folder = CORE_PATH / "gimmick"
                if archetype == "dark": target_folder = CORE_PATH / "sleep"
                if archetype == "fire": target_folder = CORE_PATH / "one_shot"
                if archetype == "water": target_folder = CORE_PATH / "energy_accel"
                if archetype == "dragon": target_folder = CORE_PATH / "evolve_power"
                
                target_folder.mkdir(parents=True, exist_ok=True)
                
                deck_name = f"{archetype}_axis_{axis_id}_v{v}"
                file_path = target_folder / f"{deck_name}.json"
                
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump({"name": deck_name, "cards": deck_ids}, f, ensure_ascii=False, indent=2)
                
                deck_count += 1
                if deck_count >= 100: break
            if deck_count >= 100: break
        if deck_count >= 100: break

    print(f"100種類の戦術変遷デッキを生成しました。")

if __name__ == "__main__":
    generate_100_decks()
