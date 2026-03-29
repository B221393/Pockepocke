
import json
import csv
import random
from simulator import load_master_db, Card, Player, Game, ActivePokemon

# Paths
DB_PATH = "data/master_card_db.csv"
CHAMPION_DECK_PATH = "decks/generated/雷_ライコウ_2ex_V4_グッズ偏重_ピンサブ.json"
META_CSV_PATH = "data/gamewith_decks.csv"

def load_deck_from_json(path, master_db):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    name_to_card = {c.name: c for c in master_db.values()}
    cards = []
    for cname in data["deck_composition"]:
        if cname in name_to_card: cards.append(name_to_card[cname])
        else: cards.append(Card(id="dummy", name=cname, card_type="Pokemon", hp=60, stage=0))
    return {"name": data["name"], "cards": cards}

def load_meta_decks(path, master_db):
    decks = []
    with open(path, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # 簡略化：CSVに枚数データがない場合があるため、典型的な構成をシミュレート
            # ここでは名前だけ抽出
            decks.append({"name": row["デッキ名"], "tier": row["ティア"]})
    return decks

def run_benchmark():
    master_db = load_master_db(DB_PATH)
    champion = load_deck_from_json(CHAMPION_DECK_PATH, master_db)
    
    # 比較対象: Sランクデッキ（GameWithデータ）
    # 実際にはCSVから詳細なリストが復元できない場合が多いため、
    # 代表的なSランクの「軸」から適当な安定デッキを生成して対戦
    from deck_archetypes import ARCHETYPES, generate_all_archetypes
    from autonomous_loop import build_archetype_deck
    
    rng = random.Random(42)
    meta_archs = {
        "ミュウツーex (Meta S)": ARCHETYPES["超_ミュウツ_サナ_V1_安定_サブ2枚"],
        "ピカチュウex (Meta S)": ARCHETYPES["雷_ピカライ_進化_V1_安定_サブ2枚"],
        "フシギバナex (Meta S)": ARCHETYPES["草_フシギバ_どく_V1_安定_サブ2枚"]
    }
    
    print(f"=== Final Benchmark: Champion vs Real World Meta (S-Tier) ===")
    print(f"Champion: {champion['name']}\n")
    
    all_cards = list(master_db.values())
    import autonomous_loop
    # LCardに変換
    l_cards = []
    for c in all_cards:
        l_cards.append(autonomous_loop.LCard(id=c.id, name=c.name, card_type=c.card_type, 
                                             pokemon_type=c.pokemon_type or "Colorless", 
                                             hp=c.hp or 60, stage=c.stage or 0))

    for meta_name, cfg in meta_archs.items():
        # メタデッキの生成
        meta_deck_lcards = build_archetype_deck(meta_name, cfg, l_cards, rng)
        # Cardオブジェクトに戻す
        meta_deck_cards = []
        for lc in meta_deck_lcards:
            meta_deck_cards.append(master_db.get(lc.id) or Card(id=lc.id, name=lc.name, card_type=lc.card_type))
            
        wins = 0
        trials = 100
        for _ in range(trials):
            p1 = Player(champion["name"], champion["cards"])
            p2 = Player(meta_name, meta_deck_cards)
            game = Game(p1, p2)
            if game.play(rng) == "p1": wins += 1
        
        print(f"vs {meta_name:.<25} WR: {wins/trials:.1%}")

if __name__ == "__main__":
    run_benchmark()
