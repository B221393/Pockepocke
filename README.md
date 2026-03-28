# Pockepocke

ポケモンカードゲーム ポケポケの最強デッキをシミュレーションで決めます。

## 概要

YouTube最新環境デッキのデータをもとに、Pythonプログラムによって自動対戦（モンテカルロシミュレーション）を行い、以下の指標を算出します。

- **勝率**（有効試合中の各デッキの勝利割合）
- **手札事故率**（初期手札にたねポケモンが1枚もない確率）

## 収録デッキ

| ファイル | デッキ名 | 参考動画 |
|---------|---------|---------|
| `decks/mega_heracross_deck.json` | メガハッサムexデッキ | [YouTube](https://www.youtube.com/watch?v=u1lM4JXj9Ww) |
| `decks/darkrai_altaria_deck.json` | ダークライ×チルタリス「ねむり」コントロールデッキ | [YouTube](https://www.youtube.com/watch?v=iSg-l39xNk4) |
| `decks/mega_charizard_deck.json` | メガリザードンX / メガリザードンYデッキ | [YouTube](https://www.youtube.com/watch?v=VI8PafzBvPE) |

## 使い方

### 必要環境

- Python 3.10 以上

### 実行方法

```bash
# 全デッキの総当たり対戦（デフォルト: 各1000試合）
python run_simulation.py

# 試合数を指定して実行
python run_simulation.py -n 10000

# 特定の2デッキを対戦させる
python run_simulation.py \
  --deck1 decks/mega_charizard_deck.json \
  --deck2 decks/darkrai_altaria_deck.json \
  -n 5000

# 再現性のある結果を得る（乱数シード指定）
python run_simulation.py --all -n 1000 --seed 42
```

### 出力例

```
シミュレーション開始: 各対戦 1000 試合

=== メガハッサムexデッキ vs ダークライ×チルタリス「ねむり」コントロールデッキ ===
総試合数: 1000  有効試合数: 766
[メガハッサムexデッキ]  勝利: 482  勝率: 62.9%  手札事故率: 10.9%
[ダークライ×チルタリス「ねむり」コントロールデッキ]  勝利: 284  勝率: 37.1%  手札事故率: 13.2%
引き分け: 0
```

## テスト実行

```bash
pip install pytest
python -m pytest tests/ -v
```

## ファイル構成

```
Pockepocke/
├── decks/
│   ├── mega_heracross_deck.json      # メガハッサムexデッキ (20枚)
│   ├── darkrai_altaria_deck.json     # ダークライ×チルタリスデッキ (20枚)
│   └── mega_charizard_deck.json      # メガリザードンX/Yデッキ (20枚)
├── simulator.py                       # コアシミュレーターロジック
├── run_simulation.py                  # CLIエントリーポイント
└── tests/
    └── test_simulator.py              # ユニットテスト (33件)
```

## ゲームルール（ポケポケ準拠）

- デッキ枚数: **20枚**（同名カード最大2枚）
- 初期手札: **5枚**
- エネルギーゾーンから毎ターン**1エネルギー**補給（デッキにエネルギーカードなし）
- バトル場1体 + ベンチ最大**3体**
- 相手ポケモンを**3体**倒したプレイヤーの勝利
- 手札事故: 初期手札にたねポケモンが1枚もない状態
