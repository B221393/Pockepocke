import csv

names = set()
with open('data/master_card_db.csv', encoding='utf-8-sig') as f:
    for r in csv.reader(f):
        if len(r) > 2 and r[2] == 'Pokemon':
            names.add(r[1])

check = [
    'メガライボルトex','スイクンex','ゲッコウガ','ミュウツーex','サーナイト','フリーザーex',
    'サザンドラ','メガアブソル','ガラガラ','メガリザードンXex','メガリザードンYex','ギラティナ',
    'メガチルタリアex','メガシザリガーex','メガガーデヴォワールex','ルギアex','ルナアーラex',
    'ソルガレオex','ドラパルトex','ミライドンex','コライドンex','テツノカイナex','ハバタクカミex',
    'ディンルーex','メガルカリオex','ウーラオスex','ギャラドスex','カイリューex','パルキアex',
    'ディアルガex','レックウザex','ガブリアスex','ルカリオex','ブラッキーex','ゲンガーex',
    'フシギバナex','カメックスex','ピカチュウex','サンダースex','ケンタロスex','カビゴン',
    'ミュウex','ムゲンダイナex','オノノクス','ライコウex','エンテイex','ホウオウex',
    'パルキアex','バドレックスex','ネクロズマex','ジラーチ',
]

print('=== ポケポケDBに存在するかチェック ===')
found_list = []
missing_list = []
for n in check:
    found = any(n in x for x in names)
    if found:
        found_list.append(n)
    else:
        missing_list.append(n)
    print(f'  {"OK" if found else "NG"} {n}')

print(f'\n存在: {len(found_list)}件 / 不在: {len(missing_list)}件')
print(f'\n収録ポケモン総数: {len(names)}')

# exポケモン一覧
ex_list = sorted([n for n in names if 'ex' in n.lower()])
print(f'\n=== 収録exポケモン一覧 ===')
for n in ex_list:
    print(f'  {n}')
