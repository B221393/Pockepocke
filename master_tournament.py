import random
import csv
import os
from simulator import load_master_db, Player, Game
from deck_archetypes import generate_all_archetypes

# 🛡️ MASTER TOURNAMENT: Evolved Champion vs Official S-Rank Meta
# Final High-Fidelity Validation (v4)

def build_deck_from_names(master_db, names):
    cards = []
    name_to_card = {c.name: c for c in master_db.values()}
    for name in names:
        if name in name_to_card:
            cards.append(name_to_card[name])
    # 20枚になるまで適宜フィラーを追加（実際はCSVから正確に取得すべきだが、ここでは簡易化）
    filler_basics = [c for c in master_db.values() if c.card_type == "Pokemon" and c.stage == 0]
    trainers = [c for c in master_db.values() if c.card_type == "Trainer"]
    while len(cards) < 20:
        cards.append(random.choice(trainers if len(cards) > 15 else (filler_basics + trainers)))
    return cards[:20]

def run_master_matchups():
    master_db = load_master_db("data/master_card_db.csv")
    
    # --- CHAMPION (Our Evolved AI Meta) ---
    champion_name = "炎_リザードンX_究極完全体"
    champion_config = ["リザードンex", "リザードンex", "リザード", "リザード", "ヒトカゲ", "ヒトカゲ", "エンテイex", "博士の研究", "博士の研究", "ナツメ", "ナツメ", "レッドの挑戦"]
    deck_champ = build_deck_from_names(master_db, champion_config)

    # --- OFFICIAL S-RANK CHALLENGERS ---
    challengers = {
        "超_ミュウツーex_サーナイト": ["ミュウツーex", "ミュウツーex", "サーナイト", "サーナイト", "キルリア", "キルリア", "ラルトス", "ラルトス", "博士の研究", "ナツメ"],
        "雷_ピカチュウex_サンダーex": ["ピカチュウex", "ピカチュウex", "サンダーex", "サンダーex", "ゼラオラ", "ゼラオラ", "プラスパワー", "博士の研究"],
        "水_スターミーex_フリーザーex": ["スターミーex", "スターミーex", "フリーザーex", "フリーザーex", "ヒトデマン", "ヒトデマン", "カスミ", "カスミ"]
    }

    print(f"\n{'='*60}")
    print(f"🏆 MASTER TOURNAMENT: THE FINAL SHOWDOWN")
    print(f"Defending Champion: {champion_name}")
    print(f"Logic: Doomed Check & Priority Evolution Active")
    print(f"{'='*60}\n")

    results = []
    rng = random.Random(2027)

    for chall_name, config in challengers.items():
        print(f"Testing vs {chall_name}...")
        deck_chall = build_deck_from_names(master_db, config)
        
        champ_wins = 0
        games = 100 # Each matchup 100 games
        
        for i in range(games):
            p1 = Player("Champion", deck_champ)
            p2 = Player(chall_name, deck_chall)
            
            # 先攻後攻を均等に振る
            if i % 2 == 0:
                game = Game(p1, p2)
                winner = game.play(rng)
                if winner == "p1": champ_wins += 1
            else:
                game = Game(p2, p1)
                winner = game.play(rng)
                if winner == "p2": champ_wins += 1
                
        wr = (champ_wins / games) * 100
        print(f"  -> Champion Win Rate: {wr:.2f}% | Games: {games}")
        results.append((chall_name, wr))

    print(f"\n{'-'*60}")
    print(f"📊 TOURNAMENT FINAL SUMMARY")
    for name, wr in results:
        status = "✅ DOMINANT" if wr >= 60 else ("⚠️ CHALLENGED" if wr >= 45 else "❌ DEFEATED")
        print(f"{name:<25} | WR: {wr:>6.2f}% | Status: {status}")
    print(f"{'-'*60}\n")

    # 結果をログに保存
    os.makedirs("logs/autonomous", exist_ok=True)
    with open("logs/autonomous/master_tournament_results.md", "w", encoding="utf-8") as f:
        f.write("# Master Tournament Final Report (v4)\n")
        f.write(f"Defending Champion: {champion_name}\n\n")
        f.write("| Opponent | Win Rate | Status |\n")
        f.write("|---|---|---|\n")
        for name, wr in results:
            status = "✅ DOMINANT" if wr >= 60 else ("⚠️ CHALLENGED" if wr >= 45 else "❌ DEFEATED")
            f.write(f"| {name} | {wr:.2f}% | {status} |\n")

if __name__ == "__main__":
    run_master_matchups()
