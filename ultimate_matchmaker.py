import os
import json
import random
import csv
from simulator import load_master_db, Player, Game, deepcopy

# Configuration
DB_PATH = "data/master_card_db.csv"
USER_DECK_PATH = "decks/meta/ultimate_balanced_deck.json"
META_POOLS = {
    "ミュウツーex": "decks/meta/mew_ex_meta.json",
    "ギラダク": "decks/meta/optimized_giradaku.json",
    "オノノクス重量級": "decks/meta/ultimate_haxorus_deck.json"
}
TOTAL_TRIALS = 1000 # For testing, can be 100000

def run_ultimate_simulation():
    db = load_master_db(DB_PATH)
    if not os.path.exists(USER_DECK_PATH):
        print(f"User deck {USER_DECK_PATH} not found.")
        return

    with open(USER_DECK_PATH, encoding="utf-8") as f: user_cfg = json.load(f)
    user_cards = [deepcopy(db[cid]) for cid in user_cfg["cards"] if cid in db]

    results = {name: {"wins": 0, "total": 0, "t1_wins": 0, "t2_wins": 0, "reversals": 0} for name in META_POOLS}
    
    rng = random.Random()
    
    print(f"Starting Matchmaking Simulation ({TOTAL_TRIALS} trials)...")
    
    for i in range(TOTAL_TRIALS):
        # 1. Select opponent based on share
        opp_name = rng.choice(list(META_POOLS.keys()))
        opp_path = META_POOLS[opp_name]
        
        if not os.path.exists(opp_path): continue
        with open(opp_path, encoding="utf-8") as f: opp_cfg = json.load(f)
        opp_cards = [deepcopy(db[cid]) for cid in opp_cfg["cards"] if cid in db]

        # 2. Run simulation with random seed
        p1 = Player("User", deepcopy(user_cards))
        p2 = Player("Meta", deepcopy(opp_cards))
        game = Game(p1, p2, deck1_cfg=user_cfg, deck2_cfg=opp_cfg)
        
        # Reversal condition: Check if user starts with a lower HP Basic than opponent
        # or has type disadvantage
        is_unfavorable = False
        if p1.active and p2.active:
            if p1.active.card.hp < p2.active.card.hp: is_unfavorable = True
            if p1.active.card.weakness == p2.active.card.pokemon_type: is_unfavorable = True

        winner = game.play(rng)
        
        results[opp_name]["total"] += 1
        if winner == "p1":
            results[opp_name]["wins"] += 1
            if game.turn_count % 2 == 1: results[opp_name]["t1_wins"] += 1
            else: results[opp_name]["t2_wins"] += 1
            if is_unfavorable: results[opp_name]["reversals"] += 1

    # 3. Output Report
    print("\n" + "="*50)
    print("      真のマッチアップ勝率レポート (Ultimate Report)")
    print("="*50)
    print(f"対象デッキ: {user_cfg['name']}")
    print(f"総試行回数: {TOTAL_TRIALS}")
    
    total_wins = sum(r["wins"] for r in results.values())
    total_games = sum(r["total"] for r in results.values())
    print(f"\n総合勝率: {total_wins/total_games:.2%}" if total_games > 0 else "No Games Played")
    
    print("\n[対面デッキ別マトリクス]")
    print(f"{'対戦相手':<15} | {'勝率':<8} | {'先攻勝率':<8} | {'逆転力':<8}")
    print("-" * 50)
    for name, r in results.items():
        if r["total"] == 0: continue
        wr = r["wins"] / r["total"]
        t1_total = r["total"] // 2 # Approximation for t1/t2 share
        t1_wr = r["t1_wins"] / t1_total if t1_total > 0 else 0
        rev_score = r["reversals"] / r["wins"] if r["wins"] > 0 else 0
        print(f"{name:<15} | {wr:<8.2%} | {t1_wr:<8.2%} | {rev_score:<8.2%}")

    print("\n[分析結論]")
    if total_wins/total_games > 0.7:
        print(">> このデッキは現在の環境において「覇権」レベルの安定性を持っています。")
    elif total_wins/total_games > 0.5:
        print(">> 十分に強力ですが、特定の対面（相性）での微調整の余地があります。")
    else:
        print(">> 構造的な欠陥、または特定のメタに対する致命的な弱点があります。")
    
    print("="*50)

if __name__ == "__main__":
    run_ultimate_simulation()
