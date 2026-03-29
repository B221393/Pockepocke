import random
import json
import os
from simulator import load_master_db, Player, Game
from concurrent.futures import ProcessPoolExecutor

# [CHAMPION] ULTIMATE TOURNAMENT v5: The Era of Great Enemies
# Evolved V6 Champions Roundup

def simulate_matchup(deck1_path, deck2_path, db_path, games=200):
    db = load_master_db(db_path)
    name_to_card = {c.name: c for c in db.values()}
    with open(deck1_path, encoding='utf-8') as f: d1_data = json.load(f)
    with open(deck2_path, encoding='utf-8') as f: d2_data = json.load(f)
    
    def cards_from_names(names): return [name_to_card[n] for n in names if n in name_to_card]
    
    rng = random.Random()
    d1_wins = 0
    d1_first_wins = 0
    d2_first_wins = 0
    
    for i in range(games):
        if i % 2 == 0: # Deck 1 First
            p1 = Player(d1_data["name"], cards_from_names(d1_data["deck_composition"]))
            p2 = Player(d2_data["name"], cards_from_names(d2_data["deck_composition"]))
            game = Game(p1, p2)
            if game.play(rng) == "p1":
                d1_wins += 1
                d1_first_wins += 1
        else: # Deck 2 First
            p1 = Player(d2_data["name"], cards_from_names(d2_data["deck_composition"]))
            p2 = Player(d1_data["name"], cards_from_names(d1_data["deck_composition"]))
            game = Game(p1, p2)
            if game.play(rng) == "p2":
                d1_wins += 1
            else:
                d2_first_wins += 1
                
    return d1_wins, d1_first_wins, d2_first_wins

def run_ultimate_tournament():
    db_path = "data/master_card_db.csv"
    gen_dir = "decks/generated"
    
    # Target Elite Participants (V6)
    targets = [
        "炎_リザードンX_究極_V6_アルティメット.json",
        "龍悪_ギラダク_究極_V6_アルティメット.json",
        "雷_ピカチュウ_究極_V6_アルティメット.json",
        "水_スターミー_究極_V6_アルティメット.json",
        "闘_ガブルカ_究極_V6_アルティメット.json",
        "超_ミュウツー_究極_V6_アルティメット.json"
    ]
    
    valid_paths = [os.path.join(gen_dir, t) for t in targets if os.path.exists(os.path.join(gen_dir, t))]
    if len(valid_paths) < 2:
        print("Error: Not enough elite decks generated yet.")
        return

    print(f"\n{'='*70}")
    print(f"[WORLD] ULTIMATE TOURNAMENT v5: ERA OF GREAT ENEMIES BEGINS")
    print(f"Participants: {len(valid_paths)} Evolved V6 Decks")
    print(f"{'='*70}\n")
    
    scores = {p: {"wins": 0, "total_games": 0} for p in valid_paths}
    
    with ProcessPoolExecutor() as executor:
        futures = []
        for i in range(len(valid_paths)):
            for j in range(i + 1, len(valid_paths)):
                futures.append((valid_paths[i], valid_paths[j], executor.submit(simulate_matchup, valid_paths[i], valid_paths[j], db_path)))
        
        for d1, d2, f in futures:
            wins, f1_wins, f2_wins = f.result()
            scores[d1]["wins"] += wins
            scores[d1]["total_games"] += 200
            scores[d2]["wins"] += (200 - wins)
            scores[d2]["total_games"] += 200
            print(f"Matchup: {os.path.basename(d1)} vs {os.path.basename(d2)} | Result: {wins}-{(200-wins)}")

    # Sort results
    sorted_results = sorted(scores.items(), key=lambda x: x[1]["wins"] / x[1]["total_games"] if x[1]["total_games"] > 0 else 0, reverse=True)

    print(f"\n{'-'*70}")
    print(f"[RANK] FINAL WORLD RANKING (LEVEL-UP v5)")
    print(f"{'Rank':<5} | {'Deck Name':<45} | {'Points':<8} | {'WR':<8}")
    print(f"{'-'*70}")
    
    for rank, (path, data) in enumerate(sorted_results, 1):
        name = os.path.basename(path).replace(".json", "")
        wr = (data["wins"] / data["total_games"]) * 100
        print(f"#{rank:<4} | {name[:43]:<45} | {data['wins']:>8} | {wr:>6.1f}%")
    print(f"{'-'*70}\n")

if __name__ == "__main__":
    run_ultimate_tournament()
