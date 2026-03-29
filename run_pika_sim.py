from simulator import simulate

deck_ononokus = "decks/ononokus_iris_deck.json"
deck_pikachu = "decks/pikachu_deck.json"

print("ガチシミュレーション開始: オノノクス・アイリス vs ピカチュウex Tier-1 (1000試合)")
result = simulate(deck_ononokus, deck_pikachu, n=1000)
print(result)
