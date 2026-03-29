
import os
import json
import random
import glob
from simulator import load_master_db, Card, Player, HumanPlayer, Game

DB_PATH = "data/master_card_db.csv"
CHAMPION_DECK_PATH = "decks/generated/雷_ライコウ_2ex_V4_グッズ偏重_ピンサブ.json"

def list_decks():
    decks = glob.glob("decks/*.json") + glob.glob("decks/generated/*.json") + glob.glob("decks/meta/*.json")
    return sorted(list(set(decks)))

def load_deck(path, master_db):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    name_to_card = {c.name: c for c in master_db.values()}
    cards = []
    
    # JSONの形式が 'deck_composition' (リスト) か 'cards' (IDリスト) かで分岐
    if "deck_composition" in data:
        for cname in data["deck_composition"]:
            if cname in name_to_card: cards.append(name_to_card[cname])
            else: cards.append(Card(id="dummy", name=cname, card_type="Pokemon", hp=60, stage=0))
    elif "cards" in data:
        for cid in data["cards"]:
            if cid in master_db: cards.append(master_db[cid])
            else: cards.append(Card(id=cid, name="Unknown", card_type="Pokemon", hp=60, stage=0))
    
    return {"name": data.get("name", os.path.basename(path)), "cards": cards}

def main():
    print("=== Pockepocke: Human vs AI Battle Module ===")
    master_db = load_master_db(DB_PATH)
    
    all_decks = list_decks()
    print("\nSelect your deck:")
    for i, d in enumerate(all_decks):
        print(f" ({i}) {os.path.basename(d)}")
    
    choice = input("\nYour choice (index): ")
    if not choice.isdigit() or int(choice) >= len(all_decks):
        print("Invalid choice. Using top champion deck for you too.")
        user_deck_path = CHAMPION_DECK_PATH
    else:
        user_deck_path = all_decks[int(choice)]
        
    user_deck = load_deck(user_deck_path, master_db)
    opp_deck = load_deck(CHAMPION_DECK_PATH, master_db)
    
    print(f"\nMatch: {user_deck['name']} (You) vs {opp_deck['name']} (AI)")
    
    p1 = HumanPlayer(user_deck['name'], user_deck['cards'])
    p2 = Player(opp_deck['name'], opp_deck['cards'])
    
    rng = random.Random()
    game = Game(p1, p2)
    
    print("\n--- BATTLE START ---")
    result = game.play(rng, verbose=True)
    
    print(f"\n--- BATTLE END ---")
    if result == "p1":
        print("CONGRATULATIONS! YOU WON!")
    elif result == "p2":
        print("DEFEAT... The AI was stronger this time.")
    else:
        print("DRAW.")

if __name__ == "__main__":
    main()
