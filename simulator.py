import csv
import random
import os
from dataclasses import dataclass, field
from typing import Optional

@dataclass
class Card:
    id: str
    name: str
    card_type: str 
    pokemon_type: str = "" 
    hp: int = 0
    stage: int = 0
    evolves_from: str = ""
    ability: str = ""
    effect: str = ""
    attacks: list["Attack"] = field(default_factory=list)
    weakness: str = ""

@dataclass
class Attack:
    name: str
    damage: int
    energy_cost: dict[str, int]
    effect: str = ""

class ActivePokemon:
    def __init__(self, card: Card):
        self.card = card
        self.damage = 0
        self.energy: dict[str, int] = {}
        self.status = "" 
        self.turn_played = 0

    @property
    def remaining_hp(self):
        return max(0, self.card.hp - self.damage)

    @property
    def is_knocked_out(self):
        return self.remaining_hp <= 0

    @property
    def is_ex(self):
        return "ex" in self.card.name.lower()

    def can_evolve(self, current_turn_count: int):
        return (current_turn_count - self.turn_played) >= 2

    def evolve(self, new_card: Card, current_turn_count: int):
        self.card = new_card
        self.turn_played = current_turn_count

class Player:
    def __init__(self, name: str, deck_cards: list[Card]):
        self.name = name
        self.deck = deck_cards[:]
        self.hand: list[Card] = []
        self.discard: list[Card] = []
        self.active: Optional[ActivePokemon] = None
        self.bench: list[ActivePokemon] = []
        self.energy_pool: dict[str, int] = {}
        self.points = 0
        self.energy_zone = self._init_energy_zone()
        self._supporter_played = False

    def _init_energy_zone(self) -> list[str]:
        types = set()
        for c in self.deck:
            if c.pokemon_type and c.pokemon_type != "Colorless":
                types.add(c.pokemon_type)
        return list(types) if types else ["Colorless"]

    def take_turn(self, opponent: "Player", game: "Game", rng: random.Random):
        if self.deck: self.hand.append(self.deck.pop(0))
        self._execute_strategic_moves(opponent, game, rng)

    def _execute_strategic_moves(self, opponent, game, rng):
        self._process_abilities(opponent, game, rng)
        
        # 回復アイテム
        if self.active and self.active.damage >= 20:
            for card in self.hand[:]:
                if "きずぐすり" in card.name or "エリカ" in card.name:
                    self.active.damage = max(0, self.active.damage - 20)
                    self.hand.remove(card); self.discard.append(card); break

        for card in self.hand[:]:
            if card.card_type == "Trainer": self._play_trainer_strategic(card, opponent, game, rng)
            elif card.card_type == "Pokemon": self._play_pokemon_strategic(card, opponent, game, rng)
        
        self._attach_energy_strategic(opponent)
        self._attack_strategic(opponent, game)

    def _play_trainer_strategic(self, card, opponent, game, rng):
        if "ナツメ" in card.name and not self._supporter_played:
            if opponent.bench:
                idx = rng.randrange(len(opponent.bench))
                opponent.active, opponent.bench[idx] = opponent.bench[idx], opponent.active
                self._supporter_played = True
                self.hand.remove(card); self.discard.append(card)
        elif "博士の研究" in card.name and not self._supporter_played:
            for _ in range(2): 
                if self.deck: self.hand.append(self.deck.pop(0))
            self._supporter_played = True
            self.hand.remove(card); self.discard.append(card)

    def _play_pokemon_strategic(self, card, opponent, game, rng):
        is_mega = "メガ" in card.name
        evolution_success = False
        if card.stage and card.stage > 0:
            for slot in ([self.active] if self.active else []) + self.bench:
                if slot.card.name == card.evolves_from and slot.can_evolve(game.turn_count):
                    slot.evolve(card, game.turn_count)
                    self.hand.remove(card); evolution_success = True; break
        
        if not evolution_success and (card.stage == 0 or is_mega):
            if not self.active:
                self.active = ActivePokemon(card); self.active.turn_played = game.turn_count
                self.hand.remove(card)
            elif len(self.bench) < 3:
                p_n = ActivePokemon(card); p_n.turn_played = game.turn_count
                self.bench.append(p_n); self.hand.remove(card)

    def _attach_energy_strategic(self, opponent):
        if not self.energy_pool: return
        target = self.active
        is_doomed = False
        if target:
            if target.remaining_hp <= 40: is_doomed = True
        
        if (not target or is_doomed) and self.bench:
            target = max(self.bench, key=lambda p: (p.card.stage, p.remaining_hp))

        if target:
            for etype, count in list(self.energy_pool.items()):
                if count > 0:
                    target.energy[etype] = target.energy.get(etype, 0) + 1
                    self.energy_pool[etype] -= 1
                    
                    # 🚀 [v6] ナイトメアオーラ
                    if (etype == "Darkness" or etype == "Dark") and "ダークライex" in target.card.name:
                        if opponent.active: opponent.active.damage += 20
                    break

    def _calculate_damage_reduction(self, target_slot, initial_dmg):
        reduction = 0
        text = str(target_slot.card.ability) + str(target_slot.card.effect)
        if "ダメージを-20" in text: reduction += 20
        if "ダメージを-30" in text: reduction += 30
        return max(0, initial_dmg - reduction)

    def _attack_strategic(self, opponent, game):
        if not self.active or not opponent.active: return
        if game.turn_count == 1: return
        if self.active.status == "sleep": return

        attack = self.active.card.attacks[0] if self.active.card.attacks else None
        if not attack: return
        
        if sum(self.active.energy.values()) < sum(attack.energy_cost.values()): return

        dmg = attack.damage
        if "ダークライ" in self.active.card.name and opponent.active.status == "sleep": dmg += 50
        if opponent.active.card.weakness == self.active.card.pokemon_type: dmg += 20
        dmg = opponent._calculate_damage_reduction(opponent.active, dmg)
        
        opponent.active.damage += dmg

        all_text = str(self.active.card.ability) + str(self.active.card.effect) + str(attack.effect)
        if "ねむりにする" in all_text: opponent.active.status = "sleep"
        elif "どくにする" in all_text: opponent.active.status = "poison"

        self._check_knockout(opponent.active, opponent)

    def _process_abilities(self, opponent, game, rng):
        all_slots = ([self.active] if self.active else []) + self.bench
        for p in all_slots:
            txt = str(p.card.ability)
            
            # 🚀 [v6] ブロークンスペース・ベロウ
            if "ブロークンスペース" in txt or "ギラティナex" in p.card.name:
                if p.energy.get("Psychic", 0) < 1:
                    p.energy["Psychic"] = p.energy.get("Psychic", 0) + 1

            if "やすらぎのかぜ" in txt or "状態異常にならない" in txt:
                for s in all_slots:
                    if s.energy: s.status = ""
            if "みずしゅりけん" in txt or "狙撃" in txt:
                opp_targets = ([opponent.active] if opponent.active else []) + opponent.bench
                if opp_targets:
                    t = next((o for o in opp_targets if o.remaining_hp <= 20), rng.choice(opp_targets))
                    t.damage += 20
                    self._check_knockout(t, opponent)

    def _check_knockout(self, target, owner):
        if target.is_knocked_out:
            self.points += (2 if target.is_ex else 1)
            if target == owner.active:
                owner.active = None
                if owner.bench: owner.active = owner.bench.pop(0)
            else: owner.bench.remove(target)

def load_master_db(path):
    db = {}
    with open(path, encoding='utf-8') as f:
        reader = csv.reader(f)
        for row in reader:
            if not row or len(row) < 5: continue
            cid = row[0]
            attacks = [Attack(name=row[9], damage=int(row[10]), energy_cost={"Colorless": 1})] if len(row) > 10 and row[10].isdigit() else []
            db[cid] = Card(id=cid, name=row[1], card_type=row[2], pokemon_type=row[3], 
                         hp=int(row[4]) if row[4].isdigit() else 60, stage=int(row[5]) if row[5].isdigit() else 0,
                         evolves_from=row[6], ability=row[7], effect=row[8], attacks=attacks, weakness=row[15] if len(row)>15 else "")
    return db

class Game:
    def __init__(self, p1: Player, p2: Player):
        self.p1 = p1; self.p2 = p2; self.turn_count = 0
    def play(self, rng: random.Random) -> str:
        for p in [self.p1, self.p2]:
            rng.shuffle(p.deck)
            p.hand = [p.deck.pop(0) for _ in range(5)]
            for c in p.hand[:]:
                if c.card_type == "Pokemon" and c.stage == 0:
                    p.active = ActivePokemon(c); p.hand.remove(c); break
        while self.turn_count < 50:
            self.turn_count += 1
            curr, other = (self.p1, self.p2) if self.turn_count % 2 else (self.p2, self.p1)
            etype = rng.choice(curr.energy_zone)
            curr.energy_pool[etype] = curr.energy_pool.get(etype, 0) + 1
            curr.take_turn(other, self, rng)
            if curr.points >= 3: return "p1" if curr == self.p1 else "p2"
            if not other.active and not other.bench: return "p1" if curr == self.p1 else "p2"
        return "draw"
