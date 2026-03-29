import numpy as np
import pandas as pd

DECK_SIZE = 60
TRIALS = 10000
target = 4
supporter = 8
ball = 12

def simulate():
    # デッキ作成 (1: ターゲット, 2: サポート, 3: ボール, 0: その他)
    deck = ([1] * target) + ([2] * supporter) + ([3] * ball)
    deck += [0] * (DECK_SIZE - len(deck))
    np.random.shuffle(deck)
    
    # 手札7枚
    hand = deck[:7]
    # サイド6枚
    prizes = deck[7:13]
    
    # 解析
    has_target = 1 in hand
    can_setup = (1 in hand) or (3 in hand) # ターゲット直接か、ボールがあるか
    prize_count = list(prizes).count(1)
    
    return has_target, can_setup, prize_count

results = [simulate() for _ in range(TRIALS)]
df = pd.DataFrame(results, columns=['Hand', 'Setup', 'Prizes'])

print(f'--- Simulation Results ({TRIALS} trials) ---')
print(f'Probability of target in hand: {df["Hand"].mean()*100:.2f}%')
print(f'Probability of setup possible (Target or Ball): {df["Setup"].mean()*100:.2f}%')
print(f'Probability of at least 1 target in prizes: {(df["Prizes"] > 0).mean()*100:.2f}%')
print(f'Probability of all 4 targets in prizes (Game Over): {(df["Prizes"] == target).mean()*100:.2f}%')
print(f'Average number of targets in prizes: {df["Prizes"].mean():.2f}')
