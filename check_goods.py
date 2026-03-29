import csv

goods = []
supporters = []
with open('data/master_card_db.csv', encoding='utf-8-sig') as f:
    for r in csv.reader(f):
        if len(r) < 3: continue
        if r[2] in ('Item', 'Trainer'):
            if any(kw in r[1] for kw in ['パッチ','雨','おふだ','ボール','サーチ','ドロー','エネルギー',
                                          'ポーション','ふしぎ','きず','くすり','博士','研究','リサーチ',
                                          'コスト','ほのお','みず','草','かみなり','フレイム','不思議']):
                goods.append((r[0], r[1], r[2]))

with open('data/master_card_db.csv', encoding='utf-8-sig') as f:
    for r in csv.reader(f):
        if len(r) < 3: continue
        if r[2] in ('Supporter',):
            supporters.append((r[0], r[1], r[2]))

print('=== エネ加速系グッズ ===')
for g in goods[:50]:
    print(f'  {g[1]} ({g[2]})')

# 全グッズ名リスト
all_items = []
with open('data/master_card_db.csv', encoding='utf-8-sig') as f:
    for r in csv.reader(f):
        if len(r) < 3: continue
        if r[2] in ('Item', 'Trainer', 'Supporter', 'Stadium'):
            all_items.append(r[1])
print(f'\n=== トレーナーズ総数: {len(all_items)} ===')
# フレイムパッチ・不思議な雨を検索
for name in all_items:
    if any(kw in name for kw in ['フレイム','パッチ','不思議','雨','カスミ','エリカ','ソクラテス','オーキド']):
        print(f'  {name}')
