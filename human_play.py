import json
import csv
import random
import os
import time

from autonomous_loop import DB_PATH, LOG_DIR, GUI_DIR, GUI_STATE_PATH, LCard, Slot, OracleAI, ArchPlayer, save_gui_state, MetaHookEngine

def human_vs_ai_loop():
    from deck_archetypes import ARCHETYPES

    db = {}; raw_cards = []
    with open(DB_PATH, encoding='utf-8') as f:
        for r in csv.reader(f):
            if len(r)<5: continue
            evolves_from = r[6] if len(r)>6 and r[6].strip() else None
            c = LCard(
                id=r[0], name=r[1], card_type=r[2], pokemon_type=r[3], 
                hp=int(r[4]) if r[4].isdigit() else 60, 
                stage=int(r[5]) if r[5].isdigit() else 0, 
                dmg=int(r[10])//2 if len(r)>10 and r[10].isdigit() else 20, 
                is_ex="ex" in r[1].lower(),
                evolves_from=evolves_from
            )
            db[c.id] = c; raw_cards.append(c)

    p1_n = "炎_リザードンX_究極_V6_アルティメット"
    p2_n = "草_ナッシー_安定_V1"
    p1_d = ARCHETYPES[p1_n]
    p2_d = ARCHETYPES[p2_n]

    def build_deck_from_archetype(arch, r_cards, d_base, rnd):
        d = []
        target_names = arch.get("axis_ex", []) + arch.get("sub_ex", [])
        
        def add_evolution_chain(poke_name):
            c = next((c for c in r_cards if c.name == poke_name), None)
            if c:
                d.extend([c, c])
                curr = c
                while curr and curr.evolves_from:
                    prev_name = curr.evolves_from
                    prev = next((p for p in r_cards if p.name == prev_name), None)
                    if prev: d.extend([prev, prev])
                    curr = prev

        for name in target_names:
            add_evolution_chain(name)
            
        valid_fillers = [c for c in r_cards if c.pokemon_type in arch.get("core_types", []) and c.card_type == "Pokemon" and c.stage == 0]
        if not valid_fillers: valid_fillers = [c for c in r_cards if c.card_type == "Pokemon" and c.stage == 0]
        
        while len(d) < 20: d.append(rnd.choice(valid_fillers))
        return d[:20]

    print(f"=== HUMAN vs AI (ORACLE GUI BRIDGE) ===")
    rng = random.Random()
    
    p1_deck = build_deck_from_archetype(p1_d, raw_cards, db, rng)
    p2_deck = build_deck_from_archetype(p2_d, raw_cards, db, rng)
    
    p1 = ArchPlayer(p1_n + " [HUMAN]", p1_deck)
    p2 = ArchPlayer(p2_n + " [AI]", p2_deck)
    
    p1.setup(rng)
    p2.setup(rng)
    
    # GUI初期化用
    eval_score = OracleAI.calculate_eval_score(p1, p2)
    save_gui_state(p1, p2, eval_score)
    
    for t in range(50):
        curr, other = (p1, p2) if t % 2 == 0 else (p2, p1)
        
        if curr == p1:
            print(f"\n------------------------------")
            print(f">>> YOUR TURN (Turn {(t//2)+1}) <<<")
            
            if p1.deck:
                drawn = p1.deck.pop(0)
                p1.hand.append(drawn)
                print(f"ドローしました: {drawn.name} (残りデッキ: {len(p1.deck)}枚)")

            save_gui_state(p1, p2, OracleAI.calculate_eval_score(p1, p2))
            
            print("1: エネをつける (Energy +1)")
            print("2: そのまま攻撃する (Attack)")
            print("3: 降参する (Surrender)")
            
            action = ""
            while action not in ["1", "2", "3"]:
                action = input("行動を選択してください (1-3): ")
            
            p1.best_move_log = ""
            if action == "1":
                if p1.active:
                    p1.active.energy += 1.0
                    p1.best_move_log = f"[HUMAN ACTION] Attached Energy. Total={p1.active.energy}"
            elif action == "2":
                p1.best_move_log = "[HUMAN ACTION] Chose to Attack directly!"
            elif action == "3":
                print(">>> あなたは降参した。")
                break
                
            if p1.active and other.active:
                dmg = OracleAI.get_attack_dmg(p1.active.card, rng)
                other.active.damage += dmg
                p1.best_move_log += f" | Dealt {dmg} DMG to {other.active.card.name}"
                print(p1.best_move_log)
                
        else:
            print(f"\n------------------------------")
            print(f">>> AI TURN (Turn {(t//2)+1}) <<<")
            time.sleep(1)
            
            if p2.deck: p2.hand.append(p2.deck.pop(0))
            if p2.active:
                eval_score = OracleAI.calculate_eval_score(p1, p2)
                proposed = f"Attaching Energy to {p2.active.card.name}"
                audit = MetaHookEngine.pre_action_hook(p2, proposed, eval_score)
                
                if "OVERRIDE:" not in audit:
                    p2.active.energy += 1.0
                    
                p2.best_move_log = f"[AI] {audit}"
                print(p2.best_move_log)
                
                dmg = OracleAI.get_attack_dmg(p2.active.card, rng)
                if other.active:
                    other.active.damage += dmg

        if other.active and not other.active.alive:
            curr.points += 2 if other.active.card.is_ex else 1
            other.active = None
            if other.bench: other.active = other.bench.pop(0)
            
        save_gui_state(p1, p2, OracleAI.calculate_eval_score(p1, p2))
        
        if p1.points >= 3 or p2.points >= 3:
            winner = "HUMAN" if p1.points >= 3 else "AI"
            print(f"\n[Match Ended] Winner: {winner}")
            with open("gui/history.log", "a", encoding="utf-8") as f:
                f.write(f"HUMAN vs AI | Winner: {winner} | P1 Pts: {p1.points} - P2 Pts: {p2.points}\n")
            break

if __name__ == "__main__":
    human_vs_ai_loop()
