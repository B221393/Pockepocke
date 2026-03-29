"""
card_traits.py - カード個別の特殊特性テーブル
状態異常無効・特定ダメージ耐性などをカードIDベースで管理
"""

# 状態異常が一切効かないカード（どく・まひ・ねむり）
STATUS_IMMUNE = {
    # メガシンカ系 (特性: 意志の鎧)
    "2564",  # メガリザードンX ex
    "2565",  # メガリザードンY ex
    # 鋼タイプ全般（簡易: 一部のみ）
    "メタグロスex", "コバルオンex",
}

# 特定ダメージ減算カード（ex特性・特殊ボディ）
DAMAGE_REDUCTION = {
    # カード名ベース（ID確定後にIDに変換可）
    "ミュウex": 30,      # しんぴのまもり（非exからのダメ無効）
    "イシヘンジン": 20,  # 岩壁体
    "コダックex": 10,
}

# 非exからのダメージを無効化するカード（しんぴのまもり系）
NON_EX_IMMUNE = {
    "ミュウex",
    "ハピナスex",
}

# 毒ダメージ量（デフォルト10、強化版は20）
POISON_DAMAGE = {
    "default": 10,
    "強化版どく": 20,
}

# 麻痺の持続ターン数
PARALYSIS_TURNS = 1  # ポケポケルール: 相手の番1回のみ

# 壁として機能するカード（「ふとうのつるぎ」等: きぜつしてもサイドを渡さない）
NO_PRIZE_ON_KO = {
    # 現状ポケポケではなし（将来実装用）
}

# コイントス必須ワザを持つカード（外れがあるのでリスクあり）
COIN_FLIP_ATTACKS = {
    "サンダース": True,
    "ビリリダマ": True,
    "ゲンガーex": True,
}

def is_status_immune(card_name: str, card_id: str = "") -> bool:
    return card_id in STATUS_IMMUNE or card_name in STATUS_IMMUNE

def get_damage_reduction(card_name: str, attacker_is_ex: bool) -> int:
    if card_name in NON_EX_IMMUNE and not attacker_is_ex:
        return 9999  # 実質無効化
    return DAMAGE_REDUCTION.get(card_name, 0)
