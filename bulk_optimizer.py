import os
import json
import random
import csv
from datetime import datetime
from simulator import load_master_db, Player, Game, deepcopy

# Configuration
DB_PATH = "data/master_card_db.csv"
INPUT_DECK_PATH = "decks/user_kodoku_base.json"
META_DECKS = [
    "decks/meta/mew_ex_meta.json",
    "decks/meta/optimized_giradaku.json",
    "decks/meta/ultimate_haxorus_deck.json"
]
TOTAL_GENERATIONS = 500
GAMES_PER_GEN = 100 # Accuracy vs Speed
LOG_DIR = "logs/win_rate_trends/"

def run_bulk_optimization():
    os.makedirs(LOG_DIR, exist_ok=True)
    db = load_master_db(DB_PATH)
    all_cids = list(db.keys())
    
    with open(INPUT_DECK_PATH, encoding="utf-8") as f: start_deck_cfg = json.load(f)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(LOG_DIR, f"ultimate_kodoku_trend_{timestamp}.csv")
    
    current_best_cids = start_deck_cfg["cards"][:]
    # Force deck size to 20
    while len(current_best_cids) < 20:
        current_best_cids.append(random.choice(all_cids))
        
    rng = random.Random()

    def run_sim(cids, cfg):
        total_wins = 0
        total_turns = 0
        count = 0
        for opp_path in META_DECKS:
            if not os.path.exists(opp_path): continue
            with open(opp_path, encoding="utf-8") as f: opp_cfg = json.load(f)
            games = GAMES_PER_GEN // len(META_DECKS)
            for _ in range(games):
                p1 = Player("P1", [deepcopy(db[cid]) for cid in cids if cid in db])
                p2 = Player("P2", [deepcopy(db[cid]) for cid in opp_cfg["cards"] if cid in db])
                game = Game(p1, p2, deck1_cfg=cfg, deck2_cfg=opp_cfg)
                if game.play(rng) == "p1": total_wins += 1
                total_turns += game.turn_count
            count += games
        return (total_wins / count if count > 0 else 0), (total_turns / count if count > 0 else 100)

    with open(log_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Gen", "Old_Card", "New_Card", "Win_Rate", "Turns"])
        
        current_best_rate, current_best_turns = run_sim(current_best_cids, start_deck_cfg)
        print(f"Gen 0 (Start): WR: {current_best_rate:.2%} | Turns: {current_best_turns:.1f}")

        for gen in range(1, TOTAL_GENERATIONS + 1):
            test_cids = current_best_cids[:]
            
            # Mutate ALL slots (full evolution)
            idx = rng.randrange(len(test_cids))
            old_cid = test_cids[idx]
            new_cid = rng.choice(all_cids)
            test_cids[idx] = new_cid

            # Win rate and turn calculation
            raw_win_rate, raw_turns = run_sim(test_cids, start_deck_cfg)
            win_rate = raw_win_rate
            
            # Evolution Consistency Penalty & Basic Count Penalty
            names = [db[cid].name for cid in test_cids if cid in db]
            basics = [cid for cid in test_cids if (db[cid].card_type == "Pokemon" and db[cid].stage == 0) or ("化石" in db[cid].name)]
            
            if len(basics) < 4: win_rate -= 0.1 # Mulligan risk penalty
            
            for cid in test_cids:
                c = db[cid]
                if c.stage and c.stage > 0 and "メガ" not in c.name:
                    if c.evolves_from not in names:
                        win_rate -= 0.1 # Dead card penalty

            if win_rate > current_best_rate or (abs(win_rate - current_best_rate) < 0.001 and raw_turns < current_best_turns):
                current_best_cids = test_cids
                current_best_rate = win_rate
                current_best_turns = raw_turns
                writer.writerow([gen, db[old_cid].name, db[new_cid].name, raw_win_rate, raw_turns])
                print(f"Gen {gen}: Ultimate Survival! {db[old_cid].name} -> {db[new_cid].name} | WR: {raw_win_rate:.2%} | Turns: {raw_turns:.1f}")
        
        # Save Ultimate Survivor
        final_cards = sorted(current_best_cids, key=lambda cid: db[cid].name)
        start_deck_cfg["cards"] = final_cards
        # Detect primary energy types
        e_types = set()
        for cid in final_cards:
            pt = db[cid].pokemon_type
            if pt and pt != "Colorless": e_types.add(pt)
        start_deck_cfg["energy_type"] = list(e_types)
        
        with open("decks/meta/ultimate_balanced_deck.json", "w", encoding="utf-8") as out:
            json.dump(start_deck_cfg, out, indent=2, ensure_ascii=False)

    print(f"Ultimate Kodoku Finished. Best WR: {current_best_rate:.2%} | Best Turns: {current_best_turns:.1f}")

if __name__ == "__main__":
    run_bulk_optimization()
