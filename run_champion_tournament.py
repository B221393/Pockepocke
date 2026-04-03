
import json
import csv
import random
import os
from pathlib import Path
from simulator import Card, Attack, ActivePokemon, Player, Game, load_master_db

# コア設定
DB_PATH = "data/master_card_db.csv"
GENERATED_DIR = "decks/generated"
REPORT_PATH = "logs/autonomous/champion_report.md"
TOURNAMENT_REPORT = "logs/master_tournament_results.md"
GAMES_PER_MATCHUP = 50

def extract_top_decks(n=10):
    decks = []
    if not os.path.exists(REPORT_PATH):
        return []
    with open(REPORT_PATH, "r", encoding="utf-8") as f:
        lines = f.readlines()
        for line in lines:
            if line.startswith("| #"):
                parts = [p.strip() for p in line.split("|")]
                if len(parts) >= 3:
                    name = parts[2]
                    decks.append(name)
                    if len(decks) >= n:
                        break
    return decks

def load_deck_json(deck_name, master_db):
    safe_name = deck_name.replace("/", "_").replace("\\", "_")
    path = os.path.join(GENERATED_DIR, f"{safe_name}.json")
    if not os.path.exists(path):
        return None
    
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    name_to_card = {c.name: c for c in master_db.values()}
    deck_cards = []
    for cname in data["deck_composition"]:
        if cname in name_to_card:
            deck_cards.append(name_to_card[cname])
        else:
            found = False
            for db_name, card in name_to_card.items():
                if cname in db_name:
                    deck_cards.append(card)
                    found = True
                    break
            if not found:
                deck_cards.append(Card(id="dummy", name=cname, card_type="Pokemon", hp=60, stage=0))
    
    return {"name": deck_name, "cards": deck_cards, "strategy": data.get("strategy", "aggro")}

def run_tournament():
    master_db = load_master_db(DB_PATH)
    top_deck_names = extract_top_decks(10)
    
    decks = []
    for name in top_deck_names:
        d = load_deck_json(name, master_db)
        if d: decks.append(d)
    
    if not decks:
        print("No decks found to run tournament.")
        return

    print(f"Starting Master Tournament with {len(decks)} decks...")
    
    results = {d["name"]: {"wins": 0, "total": 0, "matchups": {}} for d in decks}
    card_intel = {} # カード名 -> {adoption: 0, activations: 0, points: 0}
    
    # 採用数の初期集計
    for d in decks:
        seen_in_deck = set()
        for c in d["cards"]:
            if c.name not in card_intel: card_intel[c.name] = {"adoption": 0, "activations": 0, "points": 0}
            if c.name not in seen_in_deck:
                card_intel[c.name]["adoption"] += 1
                seen_in_deck.add(c.name)

    rng = random.Random(42)

    for i in range(len(decks)):
        for j in range(i + 1, len(decks)):
            d1, d2 = decks[i], decks[j]
            d1_wins, d2_wins = 0, 0
            
            print(f"Matchup: {d1['name']} vs {d2['name']}")
            
            for _ in range(GAMES_PER_MATCHUP):
                p1 = Player(d1["name"], d1["cards"])
                p2 = Player(d2["name"], d2["cards"])
                game = Game(p1, p2)
                res = game.play(rng)
                
                if res == "p1": d1_wins += 1
                elif res == "p2": d2_wins += 1
                
                # 統計の集約
                for p in [p1, p2]:
                    for cname, count in p.stats["activations"].items():
                        if cname in card_intel:
                            card_intel[cname]["activations"] += count
                            # その試合で勝ったプレイヤーのカードなら貢献ポイント付与
                            if (p == p1 and res == "p1") or (p == p2 and res == "p2"):
                                card_intel[cname]["points"] += (count * 10) # 簡易的な重み付け
            
            results[d1["name"]]["wins"] += d1_wins
            results[d1["name"]]["total"] += (d1_wins + d2_wins)
            results[d2["name"]]["wins"] += d2_wins
            results[d2["name"]]["total"] += (d1_wins + d2_wins)
            
            win_rate = d1_wins / max(1, (d1_wins + d2_wins))
            results[d1["name"]]["matchups"][d2["name"]] = f"{win_rate:.1%}"
            results[d2["name"]]["matchups"][d1["name"]] = f"{1-win_rate:.1%}"

    # レポート作成
    sorted_res = sorted(results.items(), key=lambda x: x[1]["wins"] / max(1, x[1]["total"]), reverse=True)
    
    with open(TOURNAMENT_REPORT, "w", encoding="utf-8") as f:
        f.write("# Master Tournament Intelligence Report\n")
        f.write(f"Total Decks: {len(decks)} | Total Games: {sum(r['total'] for r in results.values()) // 2}\n\n")
        
        f.write("## 🏆 Deck Rankings\n\n")
        f.write("| Rank | Deck Name | Master Win Rate | Total Wins |\n")
        f.write("|---|---|---|---|\n")
        for rank, (name, info) in enumerate(sorted_res, 1):
            wr = info["wins"] / max(1, info["total"])
            f.write(f"| #{rank} | {name} | {wr:.2%} | {info['wins']} |\n")
        
        f.write("\n## 🃏 Card MVP Analysis (Top 15)\n")
        f.write("Which cards contributed most to victory?\n\n")
        f.write("| Card Name | Adoption Rate | Total Activations | Contribution Score |\n")
        f.write("|---|---|---|---|\n")
        
        sorted_cards = sorted(card_intel.items(), key=lambda x: x[1]["points"], reverse=True)
        for name, stats in sorted_cards[:15]:
            adoption = f"{stats['adoption']}/{len(decks)}"
            f.write(f"| {name} | {adoption} | {stats['activations']} | {stats['points']} |\n")

        f.write("\n## 📊 Detailed Matchup Matrix\n\n")
        header = "| Deck | " + " | ".join([f"#{i+1}" for i in range(len(decks))]) + " |\n"
        f.write(header)
        f.write("|---" * (len(decks) + 1) + "|\n")
        for i, (name, _) in enumerate(sorted_res):
            row = f"| {name} "
            for j, (other_name, _) in enumerate(sorted_res):
                if i == j: row += "| - "
                else: row += f"| {results[name]['matchups'].get(other_name, 'N/A')} "
            f.write(row + "|\n")

    print(f"Tournament Complete! Report saved to {TOURNAMENT_REPORT}")

if __name__ == "__main__":
    run_tournament()
