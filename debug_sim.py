import json
from simulator import load_master_db, Player, Game, deepcopy
import random

db = load_master_db("data/master_card_db.csv")
with open("decks/meta/giradaku_deck.json", encoding="utf-8") as f: d1 = json.load(f)
with open("decks/meta/mew_ex_meta.json", encoding="utf-8") as f: d2 = json.load(f)

p1 = Player("GiraDaku", [deepcopy(db[cid]) for cid in d1["cards"] if cid in db])
p2 = Player("MewMeta", [deepcopy(db[cid]) for cid in d2["cards"] if cid in db])

print(f"P1 Deck size: {len(p1.deck)}")
print(f"P2 Deck size: {len(p2.deck)}")

game = Game(p1, p2, deck1_cfg=d1, deck2_cfg=d2)
rng = random.Random(42)
res = game.play(rng)
print(f"Winner: {res}")
print(f"Turns: {game.turn_count}")
print(f"P1 Points: {p1.points}, P2 Points: {p2.points}")
