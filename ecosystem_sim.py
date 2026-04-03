import random
import time
import os
import sys
import multiprocessing
from collections import defaultdict
from simulator import load_master_db, Player, Game, Card
from deck_archetypes import ARCHETYPES

DB_PATH = "data/master_card_db.csv"

def get_evolution_chain(card_name, master_db):
    """進化ラインを遡って全種取得"""
    chain = []
    current = next((c for c in master_db.values() if c.name == card_name), None)
    while current:
        chain.append(current)
        if current.evolves_from:
            current = next((c for c in master_db.values() if c.name == current.evolves_from), None)
        else:
            current = None
    return chain

def build_deck_from_archetype(arch, master_db, rng):
    deck = []
    all_cards = list(master_db.values())
    
    # 核心: 進化ラインを正しく含める
    for name in arch.get("axis_ex", []) + arch.get("sub_ex", []):
        chain = get_evolution_chain(name, master_db)
        for c in chain:
            deck.extend([c] * 2) # 各2枚ずつ
            
    trainers = [c for c in master_db.values() if c.card_type == "Trainer"]
    # 必須級トレーナー
    must_trainers = ["博士の研究", "キズグスリ", "ナツメ", "モンスターボール"]
    for tname in must_trainers:
        t_card = next((c for c in trainers if c.name == tname), None)
        if t_card: deck.extend([t_card] * 2)

    while len(deck) < 20: 
        deck.append(rng.choice(trainers))
    return deck[:20]

def simulate_batch(args):
    """並列実行用のバッチ処理"""
    batch_size, ladder_pool, master_db, seed = args
    rng = random.Random(seed)
    
    batch_results = []
    batch_stats = {
        "archetype_wins": defaultdict(int),
        "archetype_matches": defaultdict(int),
        "card_activations": defaultdict(int),
        "card_points": defaultdict(int),
        "card_dmg_dealt": defaultdict(int),
        "card_dmg_taken": defaultdict(int),
        "card_energy": defaultdict(int),
        "strategic_errors": 0
    }
    
    for _ in range(batch_size):
        d1, d2 = rng.choice(ladder_pool), rng.choice(ladder_pool)
        p1, p2 = Player("P1", d1["cards"]), Player("P2", d2["cards"])
        game = Game(p1, p2)
        res_key = game.play(rng)
        
        for d, p, k in [(d1, p1, "p1"), (d2, p2, "p2")]:
            batch_stats["archetype_matches"][d["name"]] += 1
            if res_key == k:
                batch_stats["archetype_wins"][d["name"]] += 1
            
            # Card stats
            for cname, count in p.stats.get("activations", {}).items():
                batch_stats["card_activations"][cname] += count
                if res_key == k: batch_stats["card_points"][cname] += count * 10
            
            for cname, dmg in p.stats.get("damage_dealt", {}).items():
                batch_stats["card_dmg_dealt"][cname] += dmg
            for cname, dmg in p.stats.get("damage_taken", {}).items():
                batch_stats["card_dmg_taken"][cname] += dmg
            for cname, count in p.stats.get("energy_attached", {}).items():
                batch_stats["card_energy"][cname] += count
                
            batch_stats["strategic_errors"] += p.stats.get("strategic_errors", 0)

    return batch_stats

def run_ecosystem_simulation(total_matches=10000):
    num_procs = multiprocessing.cpu_count()
    batch_size = total_matches // num_procs
    
    rng = random.Random(42)
    master_db = load_master_db(DB_PATH)
    
    # 1. メタプールの生成
    meta_pool = []
    for name, arch in ARCHETYPES.items():
        cards = build_deck_from_archetype(arch, master_db, rng)
        meta_pool.append({"name": name, "cards": deck_to_serializable(cards), "type": "Competitive"})
    
    # 並列化のためにCardオブジェクトをシリアライズ可能にする(実際は既に対象なのでそのまま)
    ladder_pool = rng.choices(meta_pool, k=min(1000, len(meta_pool)*10))
    # Cardオブジェクトに戻す
    for d in ladder_pool:
        d["cards"] = [master_db[c.id] for c in d["cards"]]

    print(f"Starting Massive Simulation: {total_matches} matches on {num_procs} cores...")
    
    pool = multiprocessing.Pool(processes=num_procs)
    seeds = [rng.randint(0, 1000000) for _ in range(num_procs)]
    tasks = [(batch_size, ladder_pool, None, s) for s in seeds]
    
    results = pool.map(simulate_batch, tasks)
    pool.close(); pool.join()
    
    # 集計
    final_stats = {
        "arch": defaultdict(lambda: {"wins": 0, "matches": 0}),
        "card": defaultdict(lambda: {"activations": 0, "points": 0, "dmg_dealt": 0, "dmg_taken": 0, "energy": 0, "type": ""}),
        "errors": 0
    }
    
    for b in results:
        for name, wins in b["archetype_wins"].items():
            final_stats["arch"][name]["wins"] += wins
        for name, matches in b["archetype_matches"].items():
            final_stats["arch"][name]["matches"] += matches
        for cname, val in b["card_activations"].items():
            final_stats["card"][cname]["activations"] += val
        for cname, val in b["card_points"].items():
            final_stats["card"][cname]["points"] += val
        for cname, val in b["card_dmg_dealt"].items():
            final_stats["card"][cname]["dmg_dealt"] += val
        for cname, val in b["card_dmg_taken"].items():
            final_stats["card"][cname]["dmg_taken"] += val
        for cname, val in b["card_energy"].items():
            final_stats["card"][cname]["energy"] += val
        final_stats["errors"] += b["strategic_errors"]

    # レポート作成
    save_report(final_stats, total_matches, master_db)

def deck_to_serializable(deck):
    return deck # Card objects are already simple enough for pickling if defined at top level

def save_report(stats, total, master_db):
    out_path = "logs/ecosystem_report.md"
    os.makedirs("logs", exist_ok=True)
    
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("# ⚖️ PockePocke Massive Ecosystem Report & Judge Insights\n\n")
        f.write(f"- **Simulation Scale:** {total} matches (Multiprocessing active)\n")
        f.write(f"- **Referee Log:** Total of {stats['errors']} strategic errors (Energy attached to doomed Pokemon)\n\n")
        
        f.write("## 🏆 Archetype Meta Rankings\n\n")
        f.write("| Rank | Archetype | Win Rate | Matches |\n")
        f.write("|---|---|---|---|\n")
        sorted_arch = sorted(stats["arch"].items(), key=lambda x: x[1]["wins"]/max(1, x[1]["matches"]), reverse=True)
        for idx, (name, s) in enumerate(sorted_arch[:20]):
            wr = s["wins"] / max(1, s["matches"])
            f.write(f"| {idx+1} | {name} | {wr:.2%} | {s['matches']} |\n")

        for ctype in ["Pokemon", "Trainer"]:
            f.write(f"\n## 🃏 {ctype} Efficiency Analysis\n\n")
            if ctype == "Pokemon":
                f.write("| Name | Dmg Dealt | Dmg Taken | Energy Attached | Synergy Score |\n")
                f.write("|---|---|---|---|---|\n")
            else:
                f.write("| Name | Activations | Impact Score |\n")
                f.write("|---|---|---|\n")

            cards_in_db = {c.name: c.card_type for c in master_db.values()}
            typed_stats = []
            for name, s in stats["card"].items():
                if cards_in_db.get(name) == ctype:
                    typed_stats.append((name, s))
            
            sorted_typed = sorted(typed_stats, key=lambda x: x[1]["points"], reverse=True)
            for name, s in sorted_typed[:20]:
                if ctype == "Pokemon":
                    f.write(f"| {name} | {s['dmg_dealt']} | {s['dmg_taken']} | {s['energy']} | {s['points']} |\n")
                else:
                    f.write(f"| {name} | {s['activations']} | {s['points']} |\n")

    print(f"Report saved to {out_path}")

if __name__ == "__main__":
    count = 100000
    if len(sys.argv) > 1 and sys.argv[1].isdigit():
        count = int(sys.argv[1])
    # 1億回は流石に時間がかかるので、1000万回を超えると警告するロジック（実際はそのまま実行）
    if count > 10000000:
        print("⚠️ Warning: Scale is extremely large. This may take a long time even with Multiprocessing.")
    run_ecosystem_simulation(count)
