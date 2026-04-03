import random
import time
import os
import copy
from collections import defaultdict
from simulator import load_master_db, Player, Game, Card

DB_PATH = "data/master_card_db.csv"

def generate_competitive_decks(master_db, base_decks, count=100, rng=None):
    """ガチ勢（60%）: 強いデッキのマイナーチェンジを100種類生成"""
    competitive_decks = []
    all_cards = list(master_db.values())
    trainers = [c for c in all_cards if c.card_type == "Trainer"]
    
    for i in range(count):
        base = rng.choice(base_decks)
        new_deck = copy.deepcopy(base["cards"])
        
        # 1〜2枚のカード（主にグッズやサポート）を環境に合わせて入れ替えるマイナーチェンジ
        for _ in range(rng.randint(1, 2)):
            if new_deck:
                swap_idx = rng.randrange(len(new_deck))
                if new_deck[swap_idx].card_type == "Trainer":
                    new_deck[swap_idx] = rng.choice(trainers)
        
        competitive_decks.append({"name": f"{base['name']}_Variant_{i}", "cards": new_deck, "type": "Competitive"})
    return competitive_decks

def generate_rogue_decks(master_db, count=50, rng=None):
    """ロマン派（30%）: 使われていないカードや面白い特性を中心に組んだデッキ"""
    rogue_decks = []
    all_cards = list(master_db.values())
    basics = [c for c in all_cards if c.card_type == "Pokemon" and c.stage == 0]
    
    for i in range(count):
        deck = []
        # たねポケモンを3〜5枚入れる
        for _ in range(rng.randint(3, 5)):
            deck.append(rng.choice(basics))
        
        # 残りはランダムに面白そうなカード（または無作為）を詰め込む
        while len(deck) < 20:
            deck.append(rng.choice(all_cards))
            
        rogue_decks.append({"name": f"Rogue_Combo_{i}", "cards": deck, "type": "Rogue_Creator"})
    return rogue_decks

def run_ecosystem_simulation(total_matches=10000):
    rng = random.Random(42)
    master_db = load_master_db(DB_PATH)
    
    # 既存の強いデッキをロード（モックとして数個の強力なカードセットを作成）
    strong_cards = [c for c in master_db.values() if "ex" in c.name.lower() or c.card_type == "Trainer"]
    if not strong_cards: strong_cards = list(master_db.values())
    
    base_meta_decks = [
        {"name": "Meta_Venusaur", "cards": [rng.choice(strong_cards) for _ in range(20)]},
        {"name": "Meta_Pikachu", "cards": [rng.choice(strong_cards) for _ in range(20)]},
        {"name": "Meta_Mewtwo", "cards": [rng.choice(strong_cards) for _ in range(20)]}
    ]
    
    print("Generating Meta Ecosystem...")
    # 1. デッキプールの生成
    comp_decks = generate_competitive_decks(master_db, base_meta_decks, count=100, rng=rng)
    rogue_decks = generate_rogue_decks(master_db, count=50, rng=rng)
    
    # ロマン派コピー層（10%）は、Rogue Creatorのデッキをそのまま使うのでプールは同じ
    
    # 2. プレイヤー人口の分布設定 (60%, 30%, 10%)
    # シミュレーション上の「対戦待ちキュー」を作成
    ladder_pool = []
    for _ in range(600): ladder_pool.append(rng.choice(comp_decks))      # 60% ガチ勢
    for _ in range(300): ladder_pool.append(rng.choice(rogue_decks))     # 30% ロマン派
    for _ in range(100): ladder_pool.append(rng.choice(rogue_decks))     # 10% ロマンコピペ勢
    
    print(f"Ecosystem Ready. Simulating {total_matches} matches on the ladder...")
    
    results = defaultdict(lambda: {"wins": 0, "matches": 0})
    card_intel = defaultdict(lambda: {"activations": 0, "points": 0, "adoptions": 0})
    
    # 採用数の集計
    for deck in ladder_pool:
        seen = set()
        for c in deck["cards"]:
            if c.name not in seen:
                card_intel[c.name]["adoptions"] += 1
                seen.add(c.name)

    start_time = time.time()
    
    # マッチングと対戦
    for i in range(total_matches):
        if i > 0 and i % 2000 == 0:
            print(f"  ... {i} matches completed.")
            
        d1 = rng.choice(ladder_pool)
        d2 = rng.choice(ladder_pool)
        
        p1 = Player("P1", d1["cards"])
        p2 = Player("P2", d2["cards"])
        game = Game(p1, p2)
        res = game.play(rng)
        
        d1_name = d1["type"]
        d2_name = d2["type"]
        
        results[d1_name]["matches"] += 1
        results[d2_name]["matches"] += 1
        
        winner_p = None
        if res == "p1":
            results[d1_name]["wins"] += 1
            winner_p = p1
        elif res == "p2":
            results[d2_name]["wins"] += 1
            winner_p = p2
            
        # MVPカードの集計
        for p in [p1, p2]:
            for cname, count in p.stats.get("activations", {}).items():
                card_intel[cname]["activations"] += count
                if p == winner_p:
                    card_intel[cname]["points"] += count * 10
                    
    elapsed = time.time() - start_time
    print(f"Simulation finished in {elapsed:.2f} seconds.")
    
    # レポート出力
    out_path = "logs/ecosystem_report.md"
    os.makedirs("logs", exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("# 🌍 PockePocke Massive Ecosystem Report\n\n")
        f.write(f"- **Total Ladder Matches:** {total_matches}\n")
        f.write("- **Demographics:** 60% Competitive, 30% Rogue Creators, 10% Rogue Followers\n\n")
        
        f.write("## 🏆 Archetype Performance\n\n")
        f.write("| Player Archetype | Win Rate | Total Matches |\n")
        f.write("|---|---|---|\n")
        for arch, stats in sorted(results.items(), key=lambda x: x[1]["wins"]/max(1, x[1]["matches"]), reverse=True):
            wr = stats["wins"] / max(1, stats["matches"])
            f.write(f"| {arch} | {wr:.2%} | {stats['matches']} |\n")
            
        f.write("\n## 🃏 Meta-Defining Cards (MVP in Ecosystem)\n\n")
        f.write("| Card Name | Adoption (in 1000 decks) | Activations | Contribution Score |\n")
        f.write("|---|---|---|---|\n")
        
        sorted_cards = sorted(card_intel.items(), key=lambda x: x[1]["points"], reverse=True)
        for name, stats in sorted_cards[:20]:
            f.write(f"| {name} | {stats['adoptions']} | {stats['activations']} | {stats['points']} |\n")
            
    print(f"Report saved to {out_path}")

if __name__ == "__main__":
    run_ecosystem_simulation(10000)
