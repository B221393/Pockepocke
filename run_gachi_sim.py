from simulator import simulate
from pathlib import Path

# カレントディレクトリからの相対パス
deck_ononokus = "decks/ononokus_id_deck.json"
deck_mewtwo = "decks/mewtwo_ex_deck.json"

# ディレクトリ作成
Path("decks").mkdir(exist_ok=True)

# ミュウツーexデッキがない場合は作成（比較用）
if not Path(deck_mewtwo).exists():
    import json
    mewtwo_data = {
        "name": "ミュウツーexデッキ (標準)",
        "cards": [
            {"name": "ラルトス", "card_type": "Pokemon", "stage": 0, "hp": 60, "type": "Psychic", "attacks": [{"name": "ねんりき", "energy_cost": 1, "damage": 10}], "count": 2},
            {"name": "キルリア", "card_type": "Pokemon", "stage": 1, "hp": 80, "type": "Psychic", "evolves_from": "ラルトス", "attacks": [{"name": "サイコキネシス", "energy_cost": 2, "damage": 30}], "count": 2},
            {"name": "サーナイトex", "card_type": "Pokemon", "stage": 2, "hp": 150, "type": "Psychic", "evolves_from": "キルリア", "attacks": [{"name": "サイコシャドウ", "energy_cost": 3, "damage": 60, "effect": "energy_accel"}], "count": 2},
            {"name": "ミュウツーex", "card_type": "Pokemon", "stage": 0, "hp": 150, "type": "Psychic", "attacks": [{"name": "ねんりき", "energy_cost": 2, "damage": 50}, {"name": "サイコドライブ", "energy_cost": 4, "damage": 150}], "count": 2},
            {"name": "博士の研究", "card_type": "Supporter", "effect": "draw_3", "count": 2},
            {"name": "ナツメ", "card_type": "Supporter", "effect": "switch_opponent_active", "count": 2},
            {"name": "キズぐすり", "card_type": "Item", "effect": "heal_30", "count": 2},
            {"name": "モンスターボール", "card_type": "Item", "effect": "search_basic", "count": 2},
            {"name": "スピーダー", "card_type": "Item", "effect": "switch", "count": 2},
            {"name": "ハンドスコープ", "card_type": "Item", "effect": "peek_hand", "count": 2}
        ]
    }
    with open(deck_mewtwo, "w", encoding="utf-8") as f:
        json.dump(mewtwo_data, f, ensure_ascii=False, indent=2)

print("ガチシミュレーション開始: オノノクス・アイリス vs ミュウツーex (1000試合)")
result = simulate(deck_ononokus, deck_mewtwo, n=1000)
print(result)
