import random

class CardLogic:
    @staticmethod
    def play_supporter(card_name, player, opponent, game, rng):
        """サポートカードの効果処理（ナツメ、アカギなど）"""
        success = False
        if "ナツメ" in card_name:
            if opponent.bench:
                idx = rng.randrange(len(opponent.bench))
                opponent.active, opponent.bench[idx] = opponent.bench[idx], opponent.active
                success = True
        
        elif "アカギ" in card_name:
            if len(opponent.bench) > 1:
                target = opponent.bench.pop()
                opponent.deck.append(target.card)
                success = True

        elif "博士の研究" in card_name:
            for _ in range(2):
                if player.deck: player.hand.append(player.deck.pop(0))
            success = True

        if success:
            player.record_activation(card_name)
        return success

    @staticmethod
    def play_item(card_name, player, opponent, game, rng):
        """グッズカードの効果処理（きずぐすり、モンスターボールなど）"""
        success = False
        if "きずぐすり" in card_name or "エリカ" in card_name:
            if player.active and player.active.damage >= 20:
                player.active.damage = max(0, player.active.damage - 20)
                success = True
        
        elif "モンスターボール" in card_name:
            basics = [c for c in player.deck if c.card_type == "Pokemon" and c.stage == 0]
            if basics:
                target = rng.choice(basics)
                player.deck.remove(target)
                player.hand.append(target)
                success = True
        
        if success:
            player.record_activation(card_name)
        return success

    @staticmethod
    def apply_ability(ability_name, pokemon_p, player, opponent, game, rng):
        """特性の効果処理（みずしゅりけん等）"""
        if "みずしゅりけん" in ability_name or "狙撃" in ability_name:
            opp_targets = ([opponent.active] if opponent.active else []) + opponent.bench
            if opp_targets:
                target = min(opp_targets, key=lambda p: p.remaining_hp)
                target.damage += 20
                player.record_activation(f"特性: {ability_name}")
                return True
        return False
