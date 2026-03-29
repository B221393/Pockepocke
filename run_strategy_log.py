import json
import random
from copy import deepcopy
from pathlib import Path
from simulator import Player, Game, load_deck_from_json

# デッキロード
deck1_path = "decks/ononokus_id_deck.json"
deck2_path = "decks/gekko_id_deck.json"

deck1_cards = load_deck_from_json(deck1_path)
deck2_cards = load_deck_from_json(deck2_path)

rng = random.Random(42) # 再現性のため

print(f"--- 戦略シミュレーション開始 (ID管理・思考ログ記録) ---")

for i in range(3): # 最初の3試合の過程を詳細に記録
    p1 = Player("オノノクス", deepcopy(deck1_cards))
    p2 = Player("ゲッコウガ", deepcopy(deck2_cards))
    game = Game(p1, p2, rng, randomize_first_player=True)
    
    game.setup()
    result = game.play()
    
    print(f"\n【試合 {i+1} ログ】 結果: {result}")
    print(f"--- オノノクスの思考プロセス ---")
    for log in p1.history:
        print(f"  > {log}")
    
    print(f"--- ゲッコウガの思考プロセス ---")
    for log in p2.history:
        print(f"  > {log}")

print("\n--- シミュレーション終了 ---")
