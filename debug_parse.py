import re

TYPE_MAP = {'草': 'Grass', '炎': 'Fire', '水': 'Water', '雷': 'Lightning', '超': 'Psychic', '闘': 'Fighting', '悪': 'Darkness', '鋼': 'Metal', '龍': 'Dragon', '無': 'Colorless'}

def parse_costs(cost_str):
    counts = {}
    for char in cost_str:
        eng_type = TYPE_MAP.get(char, 'Colorless')
        counts[eng_type] = counts.get(eng_type, 0) + 1
    return [f"{t}:{c}" for t, c in counts.items()]

card_str = "{id:'2573',n:'ストライク',c:'P',t:'草',r:'d1',aid:'549860',hp:'70',rt:'1',p:'53',o:['ba'],mv:[{n:'とんぼがえり',v:'10',p:10,c:'無',t:'このポケモンをベンチポケモンと入れ替える。'},],ver:[{id:'2661',r:'a1',p:'53'},],}"

mv_start = card_str.find('mv:[')
print(f"mv_start: {mv_start}")
if mv_start != -1:
    bracket_level = 0
    mv_end = -1
    for i in range(mv_start + 3, len(card_str)):
        if card_str[i] == '[': bracket_level += 1
        elif card_str[i] == ']':
            if bracket_level == 0:
                mv_end = i
                break
            bracket_level -= 1
    print(f"mv_end: {mv_end}")
    if mv_end != -1:
        mv_body = card_str[mv_start + 4 : mv_end]
        print(f"mv_body: {mv_body}")
        mv_objs = re.findall(r'\{(.*?)\}', mv_body, re.DOTALL)
        print(f"mv_objs count: {len(mv_objs)}")
        for m_obj in mv_objs:
            print(f"m_obj: {m_obj}")
            def get_m_field(key):
                m = re.search(rf"{key}:'([^']*)'", m_obj)
                if not m: m = re.search(rf'{key}:"([^"]*)"', m_obj)
                if not m: m = re.search(rf"{key}:([-?\w\d\.]+)", m_obj)
                return m.group(1) if m else None
            
            m_name = get_m_field('n')
            print(f"m_name: {m_name}")
            m_dmg = get_m_field('v')
            print(f"m_dmg raw: {m_dmg}")
            m_costs_raw = get_m_field('c')
            print(f"m_costs_raw: {m_costs_raw}")
            m_costs = parse_costs(m_costs_raw) if m_costs_raw else []
            print(f"m_costs: {m_costs}")
