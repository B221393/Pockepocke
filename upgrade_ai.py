import re
from pathlib import Path

# simulator.pyのAIロジックを「すごいAI（先読み・脅威判定）」に書き換えるパッチスクリプト

def upgrade_simulator_ai():
    sim_path = Path("simulator.py")
    with open(sim_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. take_turn の高度化 (致死予測とエネ管理)
    new_take_turn = """    def take_turn(self, opponent: "Player", rng: random.Random) -> Optional[str]:
        self._supporter_played = False
        self.supporter_damage_boost = 0 
        self.iris_active = False 
        if self.deck:
            self.draw(1)
        
        # エネルギー生成
        types_in_deck = list(set(c.pokemon_type for c in (self.deck + self.hand + self.discard) if c.pokemon_type and c.pokemon_type != "-"))
        if types_in_deck:
            etype = rng.choice(types_in_deck)
            self.energy_pool[etype] = self.energy_pool.get(etype, 0) + 1
        
        self._use_abilities(opponent, rng)

        # --- すごいAI: 脅威予測と生存戦略 ---
        imminent_death = False
        if self.active and opponent.active:
            opp_attack = opponent.active.best_attack
            if opp_attack:
                expected_dmg = opp_attack.damage
                if self.active.card.weakness == opponent.active.card.pokemon_type:
                    expected_dmg += 20
                if expected_dmg >= self.active.remaining_hp:
                    imminent_death = True
                    self.log(f"AI Prediction: {self.active.card.name} will likely be KO'd next turn by {opponent.active.card.name}.")

        # 勝ち筋の計算
        if self.active and opponent.active:
            attack = self.active.best_attack
            if attack:
                dmg = attack.damage + self.active.extra_damage
                if opponent.active.card.weakness == self.active.card.pokemon_type:
                    dmg += 20
                
                will_ko = dmg >= opponent.active.remaining_hp
                pts = 2 if opponent.active.is_ex else 1
                iris_card = next((c for c in self.hand if c.effect == "iris_point_boost"), None)
                if iris_card and will_ko and (self.points + pts + 1 >= WIN_POINTS):
                    self.log(f"Strategy: LETHAL! Using Iris on {opponent.active.card.name} ({self.points} -> {self.points + pts + 1})")
                    self._apply_supporter(iris_card, rng, opponent)
                    self.hand.remove(iris_card)
                    self.discard.append(iris_card)
                    self._supporter_played = True

        # 入れ替え戦略（致死予測に基づく）
        if self.active and self.bench:
            should_switch = False
            if self.active.status == "sleep":
                should_switch = True
            elif imminent_death and not self.active.is_ex and any(b.is_ex for b in self.bench):
                # 非exが倒されそうな時、後ろに強力なexがいれば壁として見捨てる（入れ替えない）選択も
                pass
            elif imminent_death and self.active.is_ex:
                # exが倒されそうな時は絶対に逃がす（ポイントを2点取られるのを防ぐ）
                self.log("Strategy: EVASION! Switching EX Pokemon to prevent 2-point loss.")
                should_switch = True
            elif self.active.remaining_hp <= 30:
                should_switch = True
            
            if should_switch:
                self._switch_pokemon()

        self._play_trainers(rng, opponent)
        self._evolve_pokemon()
        self._place_basics_to_bench()
        
        # --- すごいAI: エネルギー分散投資 ---
        if self.energy_pool:
            if imminent_death and self.bench:
                # 倒されそうな場合、バトル場ではなくベンチのエースを育てる
                target = max(self.bench, key=lambda ap: (ap.card.hp or 0) * (2 if ap.is_ex else 1))
                for etype, count in self.energy_pool.items():
                    target.energy[etype] = target.energy.get(etype, 0) + count
                self.log(f"Strategy: Hedging! Attaching energy to bench {target.card.name} instead of doomed active.")
                self.energy_pool = {}
            else:
                self._attach_energy()

        return self._attack(opponent, rng)"""

    # 2. _choose_best_supporter の高度化 (脅威排除)
    new_choose_supporter = """    def _choose_best_supporter(self, opponent: Optional["Player"], rng: random.Random) -> Optional[Card]:
        supporters = [c for c in self.hand if c.card_type == "Supporter"]
        if not supporters: return None
        if not opponent or not opponent.active: return supporters[0]

        # 1. サカキ (boost_damage_20): 倒せるなら使う
        if any(c.effect == "boost_damage_20" for c in supporters):
            attack = self.active.best_attack if self.active else None
            if attack:
                dmg = attack.damage + self.active.extra_damage
                if dmg < opponent.active.remaining_hp <= (dmg + 20):
                    return next(c for c in supporters if c.effect == "boost_damage_20")

        # 2. ナツメ (switch_opponent_active): 脅威排除ロジック
        if any(c.effect == "switch_opponent_active" for c in supporters):
            if opponent.bench:
                # 相手のベンチに育ちかけのEXがいる、または倒しやすい手負いがいる場合
                vulnerable_ex = [b for b in opponent.bench if b.is_ex and b.remaining_hp <= (self.active.best_attack.damage if self.active and self.active.best_attack else 0)]
                if vulnerable_ex:
                    self.log("Strategy: THREAT ELIMINATION! Using Boss's Orders on vulnerable EX.")
                    return next(c for c in supporters if c.effect == "switch_opponent_active")

        # 3. ものまねむすめ (draw_until_opponent_hand_size): 手札差が3枚以上なら爆アド
        copycat = next((c for c in supporters if c.effect == "draw_until_opponent_hand_size"), None)
        if copycat and len(opponent.hand) - len(self.hand) >= 3:
            self.log("Strategy: Value! Using Copycat to draw massive cards.")
            return copycat

        # 4. 博士の研究 (draw_3)
        research = next((c for c in supporters if c.effect == "draw_3"), None)
        if research and len(self.hand) < 4: 
            return research

        # 5. マーズ (mars_hand_discard): 相手の手札が多い時に妨害
        mars = next((c for c in supporters if c.effect == "mars_hand_discard"), None)
        if mars and len(opponent.hand) >= 4:
            return mars

        return supporters[0]"""

    # 正規表現で置換
    content = re.sub(r'    def take_turn\(self, opponent: "Player", rng: random\.Random\) -> Optional\[str\]:.*?(?=    def _use_abilities)', new_take_turn + "\n\n", content, flags=re.DOTALL)
    content = re.sub(r'    def _choose_best_supporter\(self, opponent: Optional\["Player"\], rng: random\.Random\) -> Optional\[Card\]:.*?(?=    def _apply_item)', new_choose_supporter + "\n\n", content, flags=re.DOTALL)

    with open(sim_path, "w", encoding="utf-8") as f:
        f.write(content)
    print("AI Upgraded to Advanced Heuristics.")

if __name__ == "__main__":
    upgrade_simulator_ai()
