from simulator import simulate
from pathlib import Path

deck_haxorus = "decks/meta/ultimate_haxorus_deck.json"
deck_lightning = "decks/lightning_rush_deck.json"

print("--- シミュレーション1: オノノクス vs オノノクス (ミラーマッチ) ---")
result_mirror = simulate(deck_haxorus, deck_haxorus, n=1000)
print(result_mirror)

print("\n--- シミュレーション2: オノノクス vs 雷速攻 (ライボルト・サンダース軸) ---")
result_vs = simulate(deck_haxorus, deck_lightning, n=1000)
print(result_vs)
