import random

def generate_all_archetypes():
    # 軸となるポケモンの定義
    CORE_AXES = {
        "炎_リザードンX": { "axis_ex": ["リザードンex"], "sub_ex_pool": ["ファイヤーex", "リザードン"], "core_types": ["Fire"], "key_goods": ["レッドの挑戦", "フレイムパッチ"], "strategy": "aggro", "pin_mega": False },
        "雷_ライコウ": { "axis_ex": ["ライコウex"], "sub_ex_pool": ["ゼラオラex", "ミライドンex"], "core_types": ["Lightning"], "key_goods": ["プラスパワー", "エレキジェネレータ"], "strategy": "aggro-annihilation", "pin_mega": False },
        "水_スイクン": { "axis_ex": ["スイクンex"], "sub_ex_pool": ["ケルディオex", "パルキアex"], "core_types": ["Water"], "key_goods": ["カスミ", "アクアパッチ"], "strategy": "rush", "pin_mega": False },
        "水_スイクンセグレイブ": { "axis_ex": ["スイクンex"], "sub_ex_pool": ["セグレイブ", "セゴール", "セビエ"], "core_types": ["Water"], "key_goods": ["カスミ", "ふしぎなアメ"], "strategy": "combo-aggro", "pin_mega": False },
        "超_ミュウツー": { "axis_ex": ["ミュウツーex"], "sub_ex_pool": ["サーナイト", "キルリア", "ラルトス"], "core_types": ["Psychic"], "key_goods": ["サカキ"], "strategy": "control", "pin_mega": False },
        "龍悪_ギラダク": { "axis_ex": ["ギラティナex", "ダークライex"], "sub_ex_pool": ["アブソル", "サザンドラex"], "core_types": ["Dragon", "Darkness"], "key_goods": ["ねむり", "ふしぎなアメ"], "strategy": "combo", "pin_mega": False },
        "闘_ガブルカ": { "axis_ex": ["ガブリアスex", "ルカリオex"], "sub_ex_pool": ["ディグダ", "マッシブーンex"], "core_types": ["Fighting"], "key_goods": ["ナツメ"], "strategy": "anti-lightning", "pin_mega": False },
        "鋼_メルルギア": { "axis_ex": ["メルメタルex", "ルギアex"], "sub_ex_pool": ["アーケオスex"], "core_types": ["Metal", "Colorless"], "key_goods": ["きずぐすり"], "strategy": "tank", "pin_mega": False },
        "悪_ダークライ睡眠": { "axis_ex": ["ダークライex"], "sub_ex_pool": ["プリン", "プクリンex"], "core_types": ["Darkness", "Colorless"], "key_goods": ["ナツメ", "マーズ"], "strategy": "sleep-rng", "pin_mega": False },
        "超_ゲンガー": { "axis_ex": ["ゲンガーex"], "sub_ex_pool": ["ゴースト", "ゴース"], "core_types": ["Psychic"], "key_goods": ["ナツメ"], "strategy": "bench-snipe", "pin_mega": False },
        "草_フシギバナ": { "axis_ex": ["フシギバナex"], "sub_ex_pool": ["ドレディア", "エリカ"], "core_types": ["Grass"], "key_goods": ["エリカ"], "strategy": "tank", "pin_mega": False },
        "草_ナッシー": { "axis_ex": ["ナッシーex"], "sub_ex_pool": ["ドレディア", "タマタマ"], "core_types": ["Grass"], "key_goods": ["エリカ", "プラスパワー"], "strategy": "aggro-tank", "pin_mega": False },
    }
    
    VARIANT_PATTERNS = [
        {"name": "安定_V1", "sub_count": 2, "pin_mega": False, "goods_heavy": False},
        {"name": "グッズ偏重_V3", "sub_count": 2, "pin_mega": False, "goods_heavy": True},
        {"name": "究極_V6_アルティメット", "sub_count": 2, "pin_mega": True,  "goods_heavy": True},
    ]

    archetypes = {}
    for name, axis in CORE_AXES.items():
        for vp in VARIANT_PATTERNS:
            v_name = f"{name}_{vp['name']}"
            archetypes[v_name] = {
                "axis_ex": axis["axis_ex"],
                "sub_ex": random.sample(axis["sub_ex_pool"], min(len(axis["sub_ex_pool"]), vp["sub_count"])),
                "core_types": axis["core_types"],
                "key_goods": axis["key_goods"],
                "strategy": axis["strategy"],
                "pin_mega": axis.get("pin_mega", False) or vp["pin_mega"],
                "goods_heavy": vp["goods_heavy"],
            }
    return archetypes

ARCHETYPES = generate_all_archetypes()
