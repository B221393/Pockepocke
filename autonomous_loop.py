import json
import csv
import random
import os
import time
from datetime import datetime
from dataclasses import dataclass, field, asdict
from typing import Optional
from collections import defaultdict
from collections import defaultdict
import sys
import copy
import os

os.makedirs("gui", exist_ok=True)
os.makedirs("logs/autonomous", exist_ok=True)

CARD_REWARDS = defaultdict(float) # 個別カードの勝敗に基づく報酬（Q-value/Elo）
# ─────────────────────────────────────────
# CONFIGURATION v17 (GUI-LINKED ORACLE + META HOOKS)
# ─────────────────────────────────────────
DB_PATH = "data/master_card_db.csv"
LOG_DIR = "logs/autonomous"
GUI_DIR = "gui"
GUI_STATE_PATH = "gui/state.json"
GAMES_PER_MATCHUP = 50
UPDATE_INTERVAL_SEC = 5 # GUI更新は早めに

# --- Idea 1 & 2: Meta Hook Engine (Inspired by Claude Code Plugins) ---
class MetaHookEngine:
    @staticmethod
    def pre_action_hook(curr_player, proposed_action, eval_score):
        """[Idea 2: Hookify/Security-Guidance] Event Hook Auditing"""
        # アクション実行直前に介入し、異常な行動や非効率な手を検閲・ブロックする
        if curr_player.active and curr_player.active.energy >= 3 and "Energy" in proposed_action:
            return f"OVERRIDE: Energy over-attachment detected. Redirecting to attack."
        if eval_score < 20:
            return f"WARNING: Low win rate detected ({eval_score:.1f}%). Recommending defensive retreat."
        return f"Approved: {proposed_action}"

    @staticmethod
    def stop_hook(match_result, generation):
        """[Idea 1: Ralph Wiggum] Autonomous Intercept Loop"""
        # 終了シグナルをインターセプトし、デッキの自己変異を促してループを強制継続する
        mutation = f"Generation {generation} complete. Mutating logic based on result: {match_result}..."
        return mutation
# ----------------------------------------------------------------------


os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(GUI_DIR, exist_ok=True)

@dataclass
class LCard:
    id: str; name: str; card_type: str; pokemon_type: str = "Colorless"
    hp: int = 60; stage: int = 0; evolves_from: str = ""; dmg: int = 20; is_ex: bool = False
    
    @property
    def retreat_cost(self):
        return self.stage + 1 + (1 if self.is_ex else 0)

class Slot:
    def __init__(self, card: LCard):
        self.card = card; self.damage = 0; self.energy = 0.0; self.status = ""
        self.max_hp = card.hp # 恣意的なHP補正を撤廃し、完全なCSV純正値を適用
    @property
    def remaining(self): return self.max_hp - self.damage
    @property
    def alive(self): return self.remaining > 0
    
    def to_dict(self):
        return {
            "name": self.card.name,
            "hp": self.max_hp,
            "current_hp": self.max_hp - self.damage,
            "energy": self.energy,
            "is_ex": self.card.is_ex,
            "type": self.card.pokemon_type,
            "dmg": self.card.dmg,
            "status": self.status
        }

class OracleAI:
    EVAL_WEIGHTS = {
        'pts_diff': 15.0, 'hp_diff': 0.05, 'energy_diff': 3.0,
        'hand_adv': 1.5, 'bench_adv': 2.0, 'lookahead': 0.1,
        'knockout_reward': 20.0, 'playing_bonus': 5.0
    }

    @staticmethod
    def get_attack_dmg(card: LCard, rng: random.Random):
        # 個別カードへの過大評価（ハードコーディング）を撤廃し、純粋なカードダメージのみを返す
        # 特殊なテキスト（コイントス等）は今後パースするが、現在は全てベースダメージを尊重
        return card.dmg

    @classmethod
    def calculate_eval_score(cls, player: "ArchPlayer", opp: "ArchPlayer"):
        """[v18] DYNAMIC EVALUATION: Coefficients dynamically adapt for optimization."""
        my_hp = sum(s.remaining for s in [player.active] + player.bench if s)
        opp_hp = sum(s.remaining for s in [opp.active] + opp.bench if s)
        my_pts = player.points; opp_pts = opp.points
        
        my_lookahead = player.active.card.dmg if player.active and player.active.energy >= 1 else 0
        opp_lookahead = opp.active.card.dmg if opp.active and opp.active.energy >= 1 else 0
        
        my_energy = sum(s.energy for s in [player.active] + player.bench if s)
        opp_energy = sum(s.energy for s in [opp.active] + opp.bench if s)
        my_hand_adv = len(player.hand) - len(opp.hand)
        my_bench_adv = len(player.bench) - len(opp.bench)
        
        score = 50 + (my_pts - opp_pts) * cls.EVAL_WEIGHTS['pts_diff'] \
                   + (my_hp - opp_hp) * cls.EVAL_WEIGHTS['hp_diff'] \
                   + (my_energy - opp_energy) * cls.EVAL_WEIGHTS['energy_diff'] \
                   + (my_hand_adv) * cls.EVAL_WEIGHTS['hand_adv'] \
                   + (my_bench_adv) * cls.EVAL_WEIGHTS['bench_adv'] \
                   + (my_lookahead - opp_lookahead) * cls.EVAL_WEIGHTS['lookahead']
                   
        # とどめを刺す報酬 (Finishing Blow Reward)
        if opp.active and my_lookahead >= opp.active.remaining:
            score += cls.EVAL_WEIGHTS['knockout_reward']
            
        return max(5.0, min(95.0, float(score)))

class ArchPlayer:
    def __init__(self, name: str, cards: list[LCard]):
        self.name = name; self.deck = cards[:]; self.hand = []; self.active = None; self.bench = []; self.points = 0
        self.best_move_log = "Initializing..."

    def setup(self, rng: random.Random):
        rng.shuffle(self.deck)
        self.hand = [self.deck.pop(0) for _ in range(7)] # 引き直しがないように多めに引く
        pokes = [c for c in self.hand if c.card_type == "Pokemon" and c.stage == 0]
        if pokes:
            best = max(pokes, key=lambda c: c.hp)
            self.active = Slot(best); self.hand.remove(best)
            for c in pokes:
                if c != best and len(self.bench) < 3:
                    self.bench.append(Slot(c))
                    self.hand.remove(c)

    def to_dict(self):
        return {
            "name": self.name, "points": self.points,
            "active": self.active.to_dict() if self.active else None,
            "bench": [s.to_dict() for s in self.bench if s],
            "hand_count": len(self.hand),
            "deck_count": len(self.deck),
            "best_move": self.best_move_log
        }

def save_gui_state(p1, p2, eval_score):
    state = {
        "p1": p1.to_dict(), "p2": p2.to_dict(),
        "evaluation": eval_score, "timestamp": time.time()
    }
    with open(GUI_STATE_PATH, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False)

def autonomous_gui_loop():
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
                # //2などのダメージデバフを撤廃し、完全な正数値を代入
                dmg=int(r[10]) if len(r)>10 and r[10].isdigit() else 20, 
                is_ex="ex" in r[1].lower(),
                evolves_from=evolves_from
            )
            db[c.id] = c; raw_cards.append(c)

    # 注目マッチ（GUIで監視する一戦）の準備
    p1_n = "炎_リザードンX_究極_V6_アルティメット"; p2_n = "草_ナッシー_安定_V1"
    p1_d = ARCHETYPES[p1_n]; p2_d = ARCHETYPES[p2_n]
    
    def build_deck_from_archetype(arch, r_cards, d_base, rnd):
        d = []
        target_names = arch.get("axis_ex", []) + arch.get("sub_ex", [])
        
        # 必要な進化ラインをすべて追加する関数
        def add_evolution_chain(poke_name):
            c = next((c for c in r_cards if c.name == poke_name), None)
            if c:
                d.extend([c, c]) # メインの進化後ポケモンを2枚
                # 進化元（たね、1進化）を辿ってデッキに追加する
                curr = c
                while curr and getattr(curr, 'evolves_from', None):
                    prev_name = curr.evolves_from
                    prev = next((p for p in r_cards if p.name == prev_name), None)
                    if prev:
                        d.extend([prev, prev]) # 進化元も2枚ずつ
                    curr = prev

        for name in target_names:
            add_evolution_chain(name)
            
        # 必須級トレーナー（博士の研究、マーズの代用としての汎用妨害やドローなど）を積極採用
        core_trainers = [c for c in r_cards if c.card_type == "Trainer" and ("博士" in c.name or "マーズ" in c.name or "レター" in c.name or "メンテナンス" in c.name)]
        for ct in core_trainers:
            if len(d) < 20: d.append(ct)
            
        # 残りの枠をタイプ一致の「たねポケモン(Stage0)」と「汎用トレーナー」で埋める
        # 特定ポケモンの専用サポート（シロナ＝ガブリアス専用）は汎用プールから除外
        restricted_trainers = {"シロナ": "ガブリアス"}
        trainers = [
            c for c in r_cards 
            if c.card_type == "Trainer" 
            and (c.name not in restricted_trainers or any(restricted_trainers[c.name] in t for t in target_names))
        ]
        valid_fillers = [c for c in r_cards if c.pokemon_type in arch.get("core_types", []) and c.card_type == "Pokemon" and c.stage == 0]
        if not valid_fillers: valid_fillers = [c for c in r_cards if c.card_type == "Pokemon" and c.stage == 0]
        
        while len(d) < 20:
            pool = valid_fillers + trainers
            # カード個別の報酬（勝率評価）に基づく重み付きランダムピック（0ダメージの壁役等も実績に応じて選出増）
            weights = [max(1.0, 10.0 + CARD_REWARDS.get(c.name, 0.0)) for c in pool]
            chosen = rng.choices(pool, weights=weights, k=1)[0]
            d.append(chosen)
            
        return d[:20]

    print(f"=== ORACLE GUI LOOP v17 (Live Bridge) START ===")
    rng = random.Random()
    generation = 1
    
    # ---------------------------------------------------------
    # メタ環境のシミュレーション（100デッキ・1万人想定）
    # ---------------------------------------------------------
    @dataclass
    class MetaDeck:
        id: int
        name: str
        cards: list
        popularity: int # 流行度 (プレイヤー数)
        wins: int = 0

    meta_pool = []
    
    from deck_archetypes import ARCHETYPES
    arch_keys = list(ARCHETYPES.keys())
    
    print("Building 10,000 Meta variations (1,000,000 players)... this may take a moment.")
    for i in range(10000):
        base_name = rng.choice(arch_keys)
        arch_data = ARCHETYPES[base_name]
        d = build_deck_from_archetype(arch_data, raw_cards, db, rng)
        meta_pool.append(MetaDeck(id=i, name=f"{base_name}_Var{i}", cards=d, popularity=100))

    while True:
        # 勝率(流行度)に応じたマッチメイキング（同デッキ対決・亜種対決も発生）
        weights = [max(1, md.popularity) for md in meta_pool]
        d1, d2 = rng.choices(meta_pool, weights=weights, k=2)
        
        c1 = ArchPlayer(d1.name, d1.cards)
        c2 = ArchPlayer(d2.name, d2.cards)
        c1.setup(rng); c2.setup(rng)
        
        # 先攻後攻を完全にランダム化
        first_p1 = rng.choice([True, False])
        p1_turn_idx, p2_turn_idx = (0, 1) if first_p1 else (1, 0)
        
        for t in range(45):
            curr, other = (c1, c2) if t % 2 == p1_turn_idx else (c2, c1)
            
            # 状態異常「ねむり」(Sleep RNG)の手番開始時判定
            if curr.active and curr.active.status == "Sleep":
                if rng.random() < 0.5:
                    curr.active.status = "" # コイン表：起きた
                    curr.best_move_log = "[WOKE UP] Status recovered!"
                else:
                    curr.best_move_log = "[ZZZ] Fast asleep... Turn skipped."
                    final_eval = OracleAI.calculate_eval_score(c1, c2)
                    save_gui_state(c1, c2, final_eval)
                    # time.sleep(2) # GUIデモ用のスリープを解除（Colab等での超高速計算用）
                    continue
            
            if curr.active:
                best_score = -9999
                best_action = ("Attach->Active", curr.active)
                base_score = OracleAI.calculate_eval_score(c1, c2)
                
                score_act = base_score + OracleAI.EVAL_WEIGHTS['energy_diff'] + OracleAI.EVAL_WEIGHTS['playing_bonus']
                if score_act > best_score:
                    best_score = score_act; best_action = ("Attach->Active", curr.active)
                    
                for b in curr.bench:
                    score_b = base_score + (OracleAI.EVAL_WEIGHTS['energy_diff'] * 0.9) + OracleAI.EVAL_WEIGHTS['playing_bonus']
                    if score_b > best_score:
                        best_score = score_b; best_action = ("Attach->Bench", b)
                
                if curr.bench and curr.active.energy >= curr.active.card.retreat_cost:
                    original_active = curr.active
                    cushion = curr.bench[0]
                    original_active.energy -= original_active.card.retreat_cost
                    curr.active = cushion
                    curr.bench[0] = original_active
                    sim_score = OracleAI.calculate_eval_score(c1, c2) + OracleAI.EVAL_WEIGHTS['playing_bonus']
                    curr.bench[0] = cushion
                    curr.active = original_active
                    curr.active.energy += curr.active.card.retreat_cost
                    if sim_score > best_score:
                        best_score = sim_score; best_action = ("Retreat", cushion)
                        
                for c in curr.hand:
                    if c.card_type == "Trainer":
                        # トレーナーを使った際の仮想的アドバンテージ
                        win_bonus = min(2.0, CARD_REWARDS.get(c.name, 0.0) * 0.1) # プラス実績のあるカードは更に使われやすくなる
                        score_train = base_score + OracleAI.EVAL_WEIGHTS['hand_adv'] * 3.0 + win_bonus
                        if score_train > best_score:
                            best_score = score_train; best_action = ("Play->Trainer", c)

                action_type, target = best_action
                
                if action_type == "Attach->Active":
                    curr.active.energy += 1.0
                    act_log = f"Attached Energy to Active {curr.active.card.name}"
                elif action_type == "Attach->Bench":
                    target.energy += 1.0
                    act_log = f"Attached Energy to Bench {target.card.name}"
                elif action_type == "Retreat":
                    curr.active.energy -= curr.active.card.retreat_cost
                    curr.bench.append(curr.active)
                    curr.active = curr.bench.pop(curr.bench.index(target))
                    act_log = f"Cushion Retreat -> Out: {target.card.name}"
                elif action_type == "Play->Trainer":
                    curr.hand.remove(target)
                    act_log = f"Played Setup Trainer: {target.name}"

                curr.best_move_log = f"[OPTIMAL PLAY] {act_log} | Expected Win: {best_score:.1f}%"
                
                final_eval = OracleAI.calculate_eval_score(c1, c2)
                save_gui_state(c1, c2, final_eval)
                # time.sleep(2) # GUIデモ用のスリープを解除（Colab等での超高速計算用）
                
                dmg = OracleAI.get_attack_dmg(curr.active.card, rng)
                if other.active:
                    other.active.damage += dmg
                    
                    # 原作効果に寄せた理不尽な強制状態異常・ダメージ処理は環境を歪めるため撤廃（カード本来のスタッツとプレイングで純粋なメタを回す）
            
            if other.active and not other.active.alive:
                pts = 1
                if "メガ" in other.active.card.name: pts = 3
                elif other.active.card.is_ex: pts = 2
                curr.points += pts
                
                other.active = None
                if other.bench: other.active = other.bench.pop(0)
            
            if c1.points >= 3 or c2.points >= 3: break
        
        # 勝敗とメタ分布の更新
        winner_c = c1 if c1.points >= 3 else c2
        win_deck = d1 if c1.points >= 3 else d2
        lose_deck = d2 if c1.points >= 3 else d1
        
        win_deck.wins += 1
        
        # 10%にあたるプレイヤーが勝った流派に移る (100万人想定でのメタの波)
        transfer = min(lose_deck.popularity, max(20, int(lose_deck.popularity * 0.1)))
        win_deck.popularity += transfer
        lose_deck.popularity -= transfer
        
        # 完全に淘汰されたマイナーチェンジは、半分は流行りのコピー、半分は流行りの『メタ（弱点カウンター）』として蘇る
        if lose_deck.popularity <= 0:
            # 「最低1デッキは残るように（種族保護）」: 絶滅したアーキタイプがないかチェック
            active_archs = set()
            for m in meta_pool:
                if m.popularity > 0:
                    import re
                    match = re.match(r"(.*?_.*?_.*?)_Var", m.name)
                    if match: active_archs.add(match.group(1))
            
            extinct_archs = [k for k in ARCHETYPES.keys() if k not in active_archs]
            
            if extinct_archs:
                # 絶滅したデッキがあれば、それを強制的に復活させて環境の多様性を保護
                arch_key = extinct_archs[0]
                arch_data = ARCHETYPES[arch_key]
                top_meta = max(meta_pool, key=lambda m: m.popularity)
            else:
                top_meta = max(meta_pool, key=lambda m: m.popularity)
                import re
                m = re.match(r"(.*?_.*?_.*?)_Var", top_meta.name)
                top_key = m.group(1) if m else list(ARCHETYPES.keys())[0]
                top_arch_data = ARCHETYPES.get(top_key, ARCHETYPES[list(ARCHETYPES.keys())[0]])
                
                # 50%のユーザーは「トップメタを使う」、50%は「トップメタを対策するメタデッキを使う」
                if rng.random() < 0.5:
                    arch_key = top_key
                    arch_data = top_arch_data
                else:
                    top_types = top_arch_data.get("core_types", [])
                    weakness_map = {"Fire": "Water", "Water": "Lightning", "Lightning": "Fighting", "Fighting": "Psychic", "Psychic": "Darkness", "Darkness": "Fighting", "Grass": "Fire", "Metal": "Fire"}
                    counter_types = [weakness_map.get(t) for t in top_types if weakness_map.get(t)]
                    counter_arch_keys = [k for k, v in ARCHETYPES.items() if any(ct in v.get("core_types", []) for ct in counter_types)]
                    
                    if counter_arch_keys:
                        arch_key = rng.choice(counter_arch_keys)
                        arch_data = ARCHETYPES[arch_key]
                    else: 
                        arch_key = rng.choice(list(ARCHETYPES.keys()))
                        arch_data = ARCHETYPES[arch_key]
            
            lose_deck.cards = build_deck_from_archetype(arch_data, raw_cards, db, rng)
            lose_deck.name = f"{arch_key}_Var{rng.randint(10000, 99999)}"
            lose_deck.popularity = 100 # 新規アーキタイプに100人が参入
            top_meta.popularity -= 100
            lose_deck.wins = 0

        winner = 'P1' if c1.points >= 3 else 'P2'
        print(f"[Match Ended] Winner: {winner} ({winner_c.name}). Popularity Win: {win_deck.popularity}, Lose: {lose_deck.popularity}")
        
        with open("gui/history.log", "a", encoding="utf-8") as f:
            f.write(f"Gen {generation} | Meta Shift: {win_deck.name}({win_deck.popularity} users) over {lose_deck.name}({lose_deck.popularity} users)\n")
            
        try:
            with open("logs/autonomous/top_decks.json", "r", encoding="utf-8") as tf:
                top_decks = json.load(tf)
        except: top_decks = []
        top_decks.append({"gen": generation, "winner": winner_c.name, "popularity": win_deck.popularity, "cards": [c.name for c in win_deck.cards]})
        if len(top_decks) > 10: top_decks.pop(0)
        with open("logs/autonomous/top_decks.json", "w", encoding="utf-8") as tf:
            json.dump(top_decks, tf, ensure_ascii=False, indent=2)
            
        with open("logs/autonomous/rewards.json", "a", encoding="utf-8") as rf:
            # 各デッキの構成カードに直接「勝利報酬(+1)」と「敗北の逆報酬(-1)」を与える強化学習
            for c in win_deck.cards: CARD_REWARDS[c.name] += 1.0
            for c in lose_deck.cards: CARD_REWARDS[c.name] -= 1.0
            
            # 現在のカード評価ランキングをログへ
            sorted_rewards = sorted(CARD_REWARDS.items(), key=lambda x: x[1], reverse=True)
            rf.write(json.dumps({"gen": generation, "winner_name": winner_c.name, "top_5_cards": sorted_rewards[:5], "worst_5_cards": sorted_rewards[-5:]}) + "\n")

        for k in OracleAI.EVAL_WEIGHTS:
            OracleAI.EVAL_WEIGHTS[k] *= rng.uniform(0.9, 1.1)
            
        mutation_idea = MetaHookEngine.stop_hook(f"Meta shifted towards {win_deck.name}", generation)
        generation += 1
        time.sleep(3)

if __name__ == "__main__":
    autonomous_gui_loop()
