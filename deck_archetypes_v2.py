"""
deck_archetypes_v2.py - 軸ベース×変種展開で200種類のデッキを定義
設計思想:
  - 軸(AXES): 20〜25種のコア戦略。勝ち筋＋主要ポケモンを定義。
  - 変種(VARIANTS): 各軸に対して、サブex・グッズ選択・枚数変化でバリエーションを自動生成。
  - ピン刺し: メガシンカやサブexを1枚だけ採用するパターンも含む。
  - フレイムパッチ: 炎軸には必ずグッズとして候補に入れる。
"""

# ─────────────────────────────────────────
# 軸（コアデッキ）定義
# ─────────────────────────────────────────
# axis_ex: 軸となるexポケモン名（2枚確保）
# sub_ex_pool: ピン刺し候補のexポケモン（このプールから1〜2枚選択）
# core_types: 主要エネルギータイプ
# key_goods: 軸に入れたいグッズ名（DBに存在するもの優先）
# strategy: 戦略タイプ
# pin_mega: メガシンカをピン刺し（1枚）で入れる可能性あり

AXES = {
    # ===== 炎軸 =====
    "炎軸_メガリザードンX": {
        "description": "メガリザードンX exの超火力が軸。フレイムパッチでエネ加速。",
        "axis_ex": ["メガリザードンXex"],
        "sub_ex_pool": ["エンテイex", "ウインディex", "ホウオウex", "リザードンex",
                        "メガリザードンYex", "ゴウカザルex", "ズガドーンex"],
        "core_types": ["Fire"],
        "key_goods": ["フレイムパッチ", "博士の研究", "ふしぎなアメ"],
        "strategy": "aggro",
        "pin_mega": True,
    },
    "炎軸_メガリザードンY": {
        "description": "メガリザードンY exのメガフレア180打点が軸。エンテイexのドロー加速で組む。",
        "axis_ex": ["メガリザードンYex"],
        "sub_ex_pool": ["エンテイex", "ウインディex", "ホウオウex", "リザードンex",
                        "メガリザードンXex", "ゴウカザルex"],
        "core_types": ["Fire"],
        "key_goods": ["フレイムパッチ", "博士の研究", "ふしぎなアメ"],
        "strategy": "aggro",
        "pin_mega": True,
    },
    "炎軸_メガバシャーモ": {
        "description": "メガバシャーモexが炎エネを自己回収しながら連打。フレイムパッチで補助。",
        "axis_ex": ["メガバシャーモex"],
        "sub_ex_pool": ["エンテイex", "ホウオウex", "リザードンex", "ウインディex", "ズガドーンex"],
        "core_types": ["Fire"],
        "key_goods": ["フレイムパッチ", "博士の研究"],
        "strategy": "aggro",
        "pin_mega": True,
    },
    "炎軸_エンテイ手札": {
        "description": "エンテイexのドロー加速でデッキを回しながら炎ポケ全般を起動する汎用炎軸。",
        "axis_ex": ["エンテイex"],
        "sub_ex_pool": ["メガリザードンXex", "メガリザードンYex", "ウインディex",
                        "ホウオウex", "リザードンex", "ゴウカザルex", "ズガドーンex", "グレンアルマex"],
        "core_types": ["Fire"],
        "key_goods": ["フレイムパッチ", "博士の研究", "ふしぎなアメ"],
        "strategy": "combo",
        "pin_mega": False,
    },

    # ===== 水軸 =====
    "水軸_スイクンゲッコウガ": {
        "description": "スイクンexの耐久＋ゲッコウガexのベンチ狙撃が軸。環境最上位。",
        "axis_ex": ["スイクンex", "ゲッコウガex"],
        "sub_ex_pool": ["フリーザーex", "パオジアンex", "カメックスex", "アローラキュウコンex"],
        "core_types": ["Water"],
        "key_goods": ["博士の研究", "カスミ", "モンスターボール"],
        "strategy": "snipe",
        "pin_mega": False,
    },
    "水軸_フリーザーカスミ": {
        "description": "カスミのコイントスエネ加速＋フリーザーex速攻。不思議な広場も採用。",
        "axis_ex": ["フリーザーex"],
        "sub_ex_pool": ["スイクンex", "ラプラスex", "パオジアンex", "ギャラドスex",
                        "メガギャラドスex", "カメックスex"],
        "core_types": ["Water"],
        "key_goods": ["カスミ", "博士の研究", "ふしぎな広場"],
        "strategy": "tempo",
        "pin_mega": False,
    },
    "水軸_パオジアン速攻": {
        "description": "パオジアンexの低エネ高火力で序盤から制圧する水最速デッキ。",
        "axis_ex": ["パオジアンex"],
        "sub_ex_pool": ["スイクンex", "フリーザーex", "ゲッコウガex", "ラプラスex",
                        "アローラキュウコンex", "メガギャラドスex"],
        "core_types": ["Water"],
        "key_goods": ["博士の研究", "カスミ", "モンスターボール"],
        "strategy": "aggro",
        "pin_mega": False,
    },
    "水軸_メガギャラドス": {
        "description": "コイキング→ギャラドス→メガギャラドスexへの進化で150打点爆発。",
        "axis_ex": ["メガギャラドスex"],
        "sub_ex_pool": ["スイクンex", "フリーザーex", "ラプラスex", "ギャラドスex"],
        "core_types": ["Water"],
        "key_goods": ["ふしぎなアメ", "博士の研究", "カスミ"],
        "strategy": "combo",
        "pin_mega": True,
    },

    # ===== 雷軸 =====
    "雷軸_メガライボルト": {
        "description": "メガライボルトexの速攻が軸。ピン刺しメガシンカで柔軟。",
        "axis_ex": ["メガライボルトex"],
        "sub_ex_pool": ["サンダースex", "ライチュウex", "ピカチュウex", "ライコウex",
                        "メガデンリュウex", "ランターンex", "ストリンダーex", "ハラバリーex"],
        "core_types": ["Lightning"],
        "key_goods": ["博士の研究", "モンスターボール"],
        "strategy": "aggro",
        "pin_mega": True,
    },
    "雷軸_サンダースex": {
        "description": "サンダースexのエレキコードエネ加速で雷全般を起動する雷コンボ軸。",
        "axis_ex": ["サンダースex"],
        "sub_ex_pool": ["メガライボルトex", "ライコウex", "ライチュウex", "ピカチュウex",
                        "パチリスex", "ハラバリーex", "メガデンリュウex"],
        "core_types": ["Lightning"],
        "key_goods": ["博士の研究", "ふしぎなアメ"],
        "strategy": "combo",
        "pin_mega": False,
    },

    # ===== 超軸 =====
    "超軸_ミュウツーサーナイト": {
        "description": "ミュウツーexのサイコドライブ＋メガサーナイトexの特性で非ex完封。環境上位。",
        "axis_ex": ["ミュウツーex"],
        "sub_ex_pool": ["メガサーナイトex", "ミュウex", "ゲンガーex", "メガゲンガーex",
                        "ネクロズマex", "クレセリアex", "ミミッキュex"],
        "core_types": ["Psychic"],
        "key_goods": ["博士の研究", "ふしぎなアメ", "モンスターボール"],
        "strategy": "control",
        "pin_mega": False,
    },
    "超軸_ミュウ完封": {
        "description": "ミュウexのしんぴのまもりで非exを完全シャットアウト。裏からミュウツーexが殴る。",
        "axis_ex": ["ミュウex", "ミュウツーex"],
        "sub_ex_pool": ["メガゲンガーex", "クレセリアex", "ミミッキュex", "ネクロズマex",
                        "ゲンガーex", "メガサーナイトex"],
        "core_types": ["Psychic"],
        "key_goods": ["博士の研究", "モンスターボール"],
        "strategy": "control",
        "pin_mega": False,
    },
    "超軸_メガゲンガー": {
        "description": "メガゲンガーexの全体ダメージ特性とたたりめで盤面全体を削るコントロール軸。",
        "axis_ex": ["メガゲンガーex"],
        "sub_ex_pool": ["ゲンガーex", "ミュウツーex", "ミュウex", "ムウマージex",
                        "クレセリアex", "ネクロズマex"],
        "core_types": ["Psychic"],
        "key_goods": ["博士の研究", "ふしぎなアメ"],
        "strategy": "control",
        "pin_mega": True,
    },

    # ===== 悪軸 =====
    "悪軸_サザンドラ狙撃": {
        "description": "サザンドラのダークパルスでベンチを削りながらメガアブソルexが詰める狙撃軸。",
        "axis_ex": ["メガアブソルex"],
        "sub_ex_pool": ["ダークライex", "ブラッキーex", "マニューラex", "クロバットex",
                        "アクジキングex", "ギラティナex", "パルデアドオーex"],
        "core_types": ["Darkness"],
        "key_goods": ["博士の研究", "モンスターボール"],
        "strategy": "snipe",
        "pin_mega": True,
    },
    "悪軸_ダークライ全体": {
        "description": "ダークライexのダークパルスでベンチ枚数×火力を上げながら全体圧力をかける悪軸。",
        "axis_ex": ["ダークライex"],
        "sub_ex_pool": ["メガアブソルex", "ブラッキーex", "マニューラex", "ギラティナex",
                        "アクジキングex", "パルデアドオーex", "クロバットex"],
        "core_types": ["Darkness"],
        "key_goods": ["博士の研究", "モンスターボール"],
        "strategy": "combo",
        "pin_mega": False,
    },

    # ===== 格闘軸 =====
    "闘軸_ルカリオ安定": {
        "description": "ルカリオexの安定した高火力で中盤以降を制圧する格闘安定軸。",
        "axis_ex": ["ルカリオex"],
        "sub_ex_pool": ["ガブリアスex", "マッシブーンex", "カイリキーex", "ガラガラex",
                        "ナゲツケサルex", "ドンファンex", "ケケンカニex", "ルガルガンex"],
        "core_types": ["Fighting"],
        "key_goods": ["博士の研究", "モンスターボール", "ふしぎなアメ"],
        "strategy": "aggro",
        "pin_mega": False,
    },
    "闘軸_ガブリアス打点": {
        "description": "ガブリアスexのドラゴンクロー80打点を軸に安定してポイントを取る。",
        "axis_ex": ["ガブリアスex"],
        "sub_ex_pool": ["ルカリオex", "マッシブーンex", "カイリキーex", "ドンファンex",
                        "ガラガラex", "ナゲツケサルex"],
        "core_types": ["Fighting"],
        "key_goods": ["博士の研究", "ふしぎなアメ"],
        "strategy": "aggro",
        "pin_mega": False,
    },

    # ===== 鋼軸 =====
    "鋼軸_ディアルガ時空": {
        "description": "ディアルガexのメタルブラストで鋼エネ枚数×打点を叩く鋼最強コンボ軸。",
        "axis_ex": ["ディアルガex"],
        "sub_ex_pool": ["パルキアex", "ソルガレオex", "メガハガネールex", "メルメタルex",
                        "メガハッサムex", "サーフゴーex", "ダイノーズex"],
        "core_types": ["Metal"],
        "key_goods": ["博士の研究", "ふしぎなアメ"],
        "strategy": "combo",
        "pin_mega": False,
    },
    "鋼軸_ソルガレオ展開": {
        "description": "ソルガレオexのエネなし展開特性で鋼超ポケモンを即起動するコンボ軸。",
        "axis_ex": ["ソルガレオex"],
        "sub_ex_pool": ["ネクロズマex", "ルナアーラex", "ディアルガex", "メガハガネールex",
                        "メルメタルex", "メガハッサムex", "サーフゴーex"],
        "core_types": ["Metal", "Psychic"],
        "key_goods": ["博士の研究", "ふしぎなアメ"],
        "strategy": "combo",
        "pin_mega": False,
    },

    # ===== ドラゴン軸 =====
    "龍軸_レックウザ": {
        "description": "レックウザexのエメラルドブレイクで超高打点を叩くドラゴン最強軸。",
        "axis_ex": ["レックウザex"],
        "sub_ex_pool": ["カイリューex", "ガブリアスex", "パルキアex", "ディアルガex",
                        "ギラティナex", "ウルトラネクロズマex", "メガラティオスex"],
        "core_types": ["Dragon"],
        "key_goods": ["博士の研究", "ふしぎなアメ"],
        "strategy": "aggro",
        "pin_mega": False,
    },
    "龍軸_カイリュー狙撃": {
        "description": "カイリューexのランスアタックで全体20ダメをまきながらポイントを取るドラゴン狙撃軸。",
        "axis_ex": ["カイリューex"],
        "sub_ex_pool": ["レックウザex", "ガブリアスex", "パルキアex", "ディアルガex",
                        "ギラティナex", "メガラティオスex"],
        "core_types": ["Dragon"],
        "key_goods": ["博士の研究", "ふしぎなアメ"],
        "strategy": "snipe",
        "pin_mega": False,
    },

    # ===== 無色・汎用軸 =====
    "無色軸_ルギア": {
        "description": "ルギアexのエネ加速で異なる属性のexを起動できる超汎用コンボ軸。",
        "axis_ex": ["ルギアex"],
        "sub_ex_pool": ["カビゴンex", "ハピナスex", "ケンタロスex", "メガガルーラex",
                        "ピジョットex", "メガピジョットex", "プクリンex"],
        "core_types": ["Colorless"],
        "key_goods": ["博士の研究", "モンスターボール", "ふしぎなアメ"],
        "strategy": "combo",
        "pin_mega": False,
    },
    "草軸_フシギバナどく": {
        "description": "フシギバナexのどく蓄積で相手を削りながら回復もするコントロール草軸。",
        "axis_ex": ["フシギバナex"],
        "sub_ex_pool": ["メガフシギバナex", "ミュウex", "マスカーニャex", "ジュナイパーex",
                        "セレビィex", "エルフーンex", "ナッシーex", "ワタッコex"],
        "core_types": ["Grass"],
        "key_goods": ["博士の研究", "ふしぎなアメ", "エリカ"],
        "strategy": "control",
        "pin_mega": True,
    },
}

# ─────────────────────────────────────────
# 変種生成ルール（各軸から複数デッキを展開）
# ─────────────────────────────────────────
# 各軸に対して以下のパターンを展開:
#   V1: 軸ex×2 + サブex×2 + キーグッズ多め
#   V2: 軸ex×2 + サブex×1(ピン) + キーグッズ多め
#   V3: 軸ex×2 + サブex別1枚 + 汎用グッズ多め（別のサブex）
#   V4: 軸ex×2 + サブex×2(別の組) + 速攻グッズ
#   V5: 軸ex×2 + サブなし + 軸純正グッズ最大
#   V6: 軸ex×1(ピン) + サブex×2 + キーグッズ（サブメイン型）
#   V7: 軸ex×2 + サブex×2 + エリカ/カスミなどサポ厚め
#   V8: メガシンカ×1(ピン) + 軸ex×2 + サブex×1
# → 最大8バリアント × 22軸 = 176種 + 追加調整で200種

VARIANT_PATTERNS = [
    {"name": "標準2+2型",   "axis_count": 2, "sub_count": 2, "pin_mega": False, "goods_heavy": False},
    {"name": "ピンサブ型",   "axis_count": 2, "sub_count": 1, "pin_mega": False, "goods_heavy": True},
    {"name": "別サブ型",     "axis_count": 2, "sub_count": 1, "pin_mega": False, "goods_heavy": False, "sub_offset": 1},
    {"name": "速攻グッズ型", "axis_count": 2, "sub_count": 2, "pin_mega": False, "goods_heavy": False, "sub_offset": 2},
    {"name": "純正型",       "axis_count": 2, "sub_count": 0, "pin_mega": False, "goods_heavy": True},
    {"name": "サブメイン型", "axis_count": 1, "sub_count": 2, "pin_mega": True,  "goods_heavy": False},
    {"name": "サポ厚型",     "axis_count": 2, "sub_count": 2, "pin_mega": False, "goods_heavy": False, "support_heavy": True},
    {"name": "メガピン型",   "axis_count": 2, "sub_count": 1, "pin_mega": True,  "goods_heavy": False, "sub_offset": 3},
]


def generate_all_archetypes():
    """AXES × VARIANT_PATTERNS から200種類超のアーキタイプを動的生成して返す"""
    archetypes = {}
    for axis_name, axis in AXES.items():
        for vi, vp in enumerate(VARIANT_PATTERNS):
            key = f"{axis_name}_V{vi+1}_{vp['name']}"
            sub_pool = axis["sub_ex_pool"]
            # サブexの選択オフセット（違うexを試す）
            offset = vp.get("sub_offset", 0)
            # サブex選択
            sub_count = min(vp["sub_count"], len(sub_pool))
            subs = []
            for si in range(sub_count):
                idx = (offset + si) % len(sub_pool)
                subs.append(sub_pool[idx])

            archetypes[key] = {
                "description": f"{axis['description']} [{vp['name']}]",
                "axis_ex": axis["axis_ex"],
                "sub_ex": subs,
                "axis_ex_count": vp["axis_count"],
                "core_types": axis["core_types"],
                "key_goods": axis["key_goods"],
                "strategy": axis["strategy"],
                "pin_mega": vp.get("pin_mega", False) and axis.get("pin_mega", False),
                "goods_heavy": vp.get("goods_heavy", False),
            }
    return archetypes


# 外部から使う用のフル辞書
ARCHETYPES = generate_all_archetypes()

if __name__ == "__main__":
    arch = generate_all_archetypes()
    print(f"生成デッキ数: {len(arch)}")
    from collections import Counter
    strats = Counter(v["strategy"] for v in arch.values())
    print(f"戦略分布: {dict(strats)}")
    print("\n=== 全デッキ一覧 ===")
    for k in list(arch.keys()):
        print(f"  {k}")
