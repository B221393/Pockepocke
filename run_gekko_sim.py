from simulator import simulate

deck_ononokus = "decks/ononokus_iris_deck.json"
deck_gekko = "decks/gekko_deck.json"

print("ガチシミュレーション開始: オノノクス・アイリス vs ゲッコウガ (1000試合)")
result = simulate(deck_ononokus, deck_gekko, n=1000)
print(result)
