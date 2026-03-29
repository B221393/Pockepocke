# Pockepocke

ポケモンカードゲーム ポケポケの最強デッキをシミュレーションで決めます。

## 概要

YouTube最新環境デッキおよび **GameWith** のデッキティアリストデータをもとに、Pythonプログラムによって自動対戦（モンテカルロシミュレーション）を行い、以下の指標を算出します。

- **勝率**（有効試合中の各デッキの勝利割合）
- **手札事故率**（初期手札にたねポケモンが1枚もない確率）

## GameWith データ連携ワークフロー

最新のメタ情報を [GameWith デッキ一覧](https://gamewith.jp/pokemon-tcg-pocket/463660) から取得してシミュレーションに活用できます。

### ① カードデータ取得（全カードリスト）

[GameWith 全カードリスト](https://gamewith.jp/pokemon-tcg-pocket/462535) から 2679 種類のポケモンカード情報を取得できます。

```bash
pip install requests beautifulsoup4
python fetch_all_cards.py
# → data/all_cards.csv に保存（上書き）

# 既存データを保持しつつ新規カードを追加する場合
python fetch_all_cards.py --merge
```

オプション:
- `--url URL`     スクレイピング対象 URL（デフォルト: https://gamewith.jp/pokemon-tcg-pocket/462535）
- `--out PATH`    出力 CSV パス（デフォルト: data/all_cards.csv）
- `--timeout N`   HTTP タイムアウト秒数（デフォルト: 15）
- `--merge`       既存 CSV の内容と統合する（デフォルト: 上書き）

### ② デッキ強さランキング取得（スクレイピング）

```bash
pip install requests beautifulsoup4
python fetch_gamewith.py
# → data/gamewith_decks.csv に保存
```

`data/gamewith_decks.csv` には既に代表的な最新環境デッキデータが同梱されているため、スクレイピングなしでもすぐにシミュレーション可能です。

### ③ GameWith データでシミュレーション

```bash
# Sランクデッキ同士を10000回対戦
python simulate_from_csv.py --tier S -n 10000

# 使用率上位8デッキの総当たり、結果をCSVに保存
python simulate_from_csv.py --top 8 -n 1000 --output results/simulation_results.csv

# 全デッキの総当たり（乱数シード指定）
python simulate_from_csv.py -n 2000 --seed 42
```

### ④ 出力例

```
データソース: data/gamewith_decks.csv  (3 デッキ)
対戦組み合わせ: 3 件  各 1000 試合

=== ミュウツーexデッキ vs メガリザードンX/Yデッキ ===
総試合数: 1000  有効試合数: 820
[ミュウツーexデッキ]  勝利: 420  勝率: 51.2%  手札事故率: 5.6%
[メガリザードンX/Yデッキ]  勝利: 400  勝率: 48.8%  手札事故率: 11.4%
引き分け: 0

■ デッキ総合勝率ランキング（全対戦の平均）
  順位  デッキ名                         ティア  平均勝率   使用率
   1  メガリザードンX/Yデッキ               S    64.0%   16.2%
   2  ミュウツーexデッキ                   S    54.0%   18.5%
   3  ピカチュウexデッキ                   S    29.0%   14.3%
```

## 収録デッキ

### YouTube デッキ（JSON形式）

| ファイル | デッキ名 | 参考動画 |
|---------|---------|---------|
| `decks/mega_heracross_deck.json` | メガハッサムexデッキ | [YouTube](https://www.youtube.com/watch?v=u1lM4JXj9Ww) |
| `decks/darkrai_altaria_deck.json` | ダークライ×チルタリス「ねむり」コントロールデッキ | [YouTube](https://www.youtube.com/watch?v=iSg-l39xNk4) |
| `decks/mega_charizard_deck.json` | メガリザードンX / メガリザードンYデッキ | [YouTube](https://www.youtube.com/watch?v=VI8PafzBvPE) |

### GameWith メタデータ（CSV形式）

`data/gamewith_decks.csv` に15種類のデッキデータを収録（ティア・使用率・勝率・HP・ダメージ等）。
[`fetch_gamewith.py`](#gameWith-データ連携ワークフロー) で最新データに更新できます。

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
├── data/
│   ├── all_cards.csv                  # 全カードデータ (ポケポケ収録カード一覧)
│   └── gamewith_decks.csv             # GameWith メタデッキデータ (15件)
├── decks/
│   ├── mega_heracross_deck.json       # メガハッサムexデッキ (20枚)
│   ├── darkrai_altaria_deck.json      # ダークライ×チルタリスデッキ (20枚)
│   └── mega_charizard_deck.json       # メガリザードンX/Yデッキ (20枚)
├── fetch_all_cards.py                 # GameWith 全カードリスト スクレイパー
├── fetch_gamewith.py                  # GameWith デッキティアリスト スクレイパー
├── simulate_from_csv.py               # CSV データを使ったシミュレーター
├── simulator.py                       # コアシミュレーターロジック
├── run_simulation.py                  # JSON デッキ用 CLI
└── tests/
    ├── test_fetch_all_cards.py        # 全カードスクレイパー テスト (34件)
    ├── test_simulator.py              # コアシミュレーター テスト (33件)
    └── test_simulate_from_csv.py      # CSV シミュレーター テスト (14件)
```

## ゲームルール（ポケポケ準拠）

- デッキ枚数: **20枚**（同名カード最大2枚）
- 初期手札: **5枚**
- エネルギーゾーンから毎ターン**1エネルギー**補給（デッキにエネルギーカードなし）
- バトル場1体 + ベンチ最大**3体**
- 相手ポケモンを**3体**倒したプレイヤーの勝利
- 手札事故: 初期手札にたねポケモンが1枚もない状態
