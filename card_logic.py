import random

class CardLogic:
    @staticmethod
    def play_supporter(card_name, player, opponent, game, rng):
        """サポートカードの効果処理（ナツメ、アカギなど）"""
        if "ナツメ" in card_name:
            # 相手のベンチポケモンを強制的にバトル場へ（引きずり出し）
            if opponent.bench:
                idx = rng.randrange(len(opponent.bench))
                opponent.active, opponent.bench[idx] = opponent.bench[idx], opponent.active
                return True
        
        elif "アカギ" in card_name:
            # 相手のベンチを制限する（実装例：ベンチを山札に戻させる等）
            if len(opponent.bench) > 1:
                target = opponent.bench.pop()
                opponent.deck.append(target.card) # 簡易的に山札に戻す処理
                return True

        elif "博士の研究" in card_name:
            # 2枚ドロー
            for _ in range(2):
                if player.deck: player.hand.append(player.deck.pop(0))
            return True

        return False

    @staticmethod
    def play_item(card_name, player, opponent, game, rng):
        """グッズカードの効果処理（きずぐすり、レッドカードなど）"""
        if "きずぐすり" in card_name or "エリカ" in card_name:
            if player.active and player.active.damage >= 20:
                player.active.damage = max(0, player.active.damage - 20)
                return True
        
        elif "モンスターボール" in card_name:
            # 山札からたねポケモンをランダムに手札へ
            basics = [c for c in player.deck if c.card_type == "Pokemon" and c.stage == 0]
            if basics:
                target = rng.choice(basics)
                player.deck.remove(target)
                player.hand.append(target)
                return True
        
        return False

    @staticmethod
    def apply_ability(ability_name, pokemon_p, player, opponent, game, rng):
        """特性の効果処理（みずしゅりけん等）"""
        if "みずしゅりけん" in ability_name or "狙撃" in ability_name:
            opp_targets = ([opponent.active] if opponent.active else []) + opponent.bench
            if opp_targets:
                # 最もHPが低い敵を狙う
                target = min(opp_targets, key=lambda p: p.remaining_hp)
                target.damage += 20
                return True
        return False
