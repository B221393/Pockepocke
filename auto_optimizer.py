import time
import json
import random
from copy import deepcopy
from pathlib import Path
from simulator import load_master_db, Player, Game, deepcopy

# 設定
DB_PATH = "data/master_card_db.csv"
BASE_DECK_PATH = "decks/meta/ultimate_haxorus_deck.json"
OPPONENT_DECK_PATH = "decks/lightning_rush_deck.json"
DURATION_HOURS = 12
GAMES_PER_TRIAL = 500

def run_optimization():
    print(f"Starting Autonomous Optimization for {DURATION_HOURS} hours...")
    db = load_master_db(DB_PATH)
    all_cids = list(db.keys())
    
    with open(BASE_DECK_PATH) as f: current_best_data = json.load(f)
    with open(OPPONENT_DECK_PATH) as f: opp_data = json.load(f)
    
    def get_deck_objs(cids): return [deepcopy(db[cid]) for cid in cids if cid in db]
    
    best_win_rate = 0.0
    start_time = time.time()
    end_time = start_time + (DURATION_HOURS * 3600)
    
    trial_count = 0
    while time.time() < end_time:
        trial_count += 1
        # 実験用デッキの作成（1枚差し替え）
        test_cids = current_best_data["cards"][:]
        idx_to_replace = random.randrange(len(test_cids))
        new_cid = random.choice(all_cids)
        old_cid = test_cids[idx_to_replace]
        test_cids[idx_to_replace] = new_cid
        
        # シミュレーション
        wins = 0
        total_turns = 0
        rng = random.Random()
        
        for _ in range(GAMES_PER_TRIAL):
            p1 = Player("Optimizer", get_deck_objs(test_cids))
            p2 = Player("Target", get_deck_objs(opp_data["cards"]))
            game = Game(p1, p2)
            res = game.play(rng)
            if res == "p1": wins += 1
            total_turns += game.turn_count
            
        win_rate = wins / GAMES_PER_TRIAL
        avg_turns = total_turns / GAMES_PER_TRIAL
        
        if win_rate > best_win_rate:
            print(f"Trial {trial_count}: [EVOLVED] {best_win_rate:.1%} -> {win_rate:.1%} (Avg Turns: {avg_turns:.1f})")
            print(f"  Replaced {db[old_cid].name} with {db[new_cid].name}")
            best_win_rate = win_rate
            current_best_data["cards"] = test_cids
            
            # 最強デッキを保存
            with open("decks/meta/optimized_haxorus_deck.json", "w", encoding="utf-8") as f:
                json.dump(current_best_data, f, ensure_ascii=False, indent=2)
        
        if trial_count % 10 == 0:
            elapsed = (time.time() - start_time) / 3600
            print(f"Optimization Progress: {elapsed:.1f}/{DURATION_HOURS} hours. Best Win Rate: {best_win_rate:.1%}")

    print("Optimization Complete. Best deck saved to decks/meta/optimized_haxorus_deck.json")

if __name__ == "__main__":
    run_optimization()
