import json
import re
import csv
import os

TYPE_MAP = {
    '草': 'Grass',
    '炎': 'Fire',
    '水': 'Water',
    '雷': 'Lightning',
    '超': 'Psychic',
    '闘': 'Fighting',
    '悪': 'Darkness',
    '鋼': 'Metal',
    '龍': 'Dragon',
    '無': 'Colorless'
}

def parse_costs(cost_str):
    costs = []
    # Count occurrences of each character
    counts = {}
    for char in cost_str:
        eng_type = TYPE_MAP.get(char, 'Colorless')
        counts[eng_type] = counts.get(eng_type, 0) + 1
    
    for t, c in counts.items():
        costs.append(f"{t}:{c}")
    return costs

def main():
    input_path = r"C:\Users\Yuto\Desktop\app\pokepokealldata.txt"
    output_path = r"C:\Users\Yuto\Desktop\app\apps\prototypes\pockepocke\data\master_card_db.csv"
    
    if not os.path.exists(input_path):
        print(f"File not found: {input_path}")
        return

    with open(input_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Find the massive array window.wmt.pokemonDatas=[...];
    start_str = "window.wmt.pokemonDatas=["
    start_idx = content.find(start_str)
    if start_idx == -1:
        print("Could not find pokemonDatas")
        return
        
    # Extract the block between [ and ];
    body = content[start_idx + len(start_str) : content.rfind("];")]
    
    # Split the body by ',{id:' to get each card. 
    # Use a lookahead to keep the {id: part.
    cards = re.split(r',(?=\{id:)', body)
    
    cards_to_save = []
    seen_combinations = set()

    # Tracking for evolution links
    recent_basic = ""
    recent_s1 = ""
    
    for card_str in cards:
        # Extract fields using regex for robustness
        def get_field(key, default=''):
            m = re.search(rf"{key}:'([^']*)'", card_str)
            if not m: m = re.search(rf'{key}:"([^"]*)"', card_str)
            if not m: m = re.search(rf"{key}:([-?\w\d\.]+)", card_str)
            return m.group(1) if m else default

        cid = get_field('id')
        name = get_field('n')
        if not name or len(name) < 2: continue
            
        hp = get_field('hp', '0')
        card_type_raw = get_field('t')
        card_type = TYPE_MAP.get(card_type_raw, 'Colorless')
        
        # PokePoke specific card categories (P=Pokemon, T=Trainer)
        cat_raw = get_field('c')
        ptype = 'Pokemon' if cat_raw == 'P' else 'Trainer'
        
        # Determine stage
        o_match = re.search(r"o:\[(.*?)\]", card_str)
        o_val = o_match.group(1) if o_match else ""
        stage = 0
        if "'s1'" in o_val: stage = 1
        elif "'s2'" in o_val: stage = 2
        
        # Evolution Logic (Sequential Heuristic)
        evolves_from = ""
        if ptype == 'Pokemon':
            if stage == 0:
                recent_basic = name
                recent_s1 = "" # New line
            elif stage == 1:
                evolves_from = recent_basic
                recent_s1 = name
            elif stage == 2:
                evolves_from = recent_s1
        
        # Ability
        ab_match = re.search(r"ab:\{n:'([^']*)',t:'([^']*)'\}", card_str)
        if ab_match:
            ability_name = ab_match.group(1)
            ability_text = ab_match.group(2)
            ability = f"{ability_name}: {ability_text}"
        else:
            ab_n_only = re.search(r"ab:\{n:'([^']*)'", card_str)
            ability = ab_n_only.group(1) if ab_n_only else ""
        
        # Card Text (for item/supporter effects)
        card_effect_text = get_field('txt')

        # Extract moves: mv:[{...},...]
        mv_match = re.search(r'mv:\[(.*?)\]', card_str, re.DOTALL)
        move_info = []
        if mv_match:
            mv_body = mv_match.group(1)
            mv_objs = re.findall(r'\{(.*?)\}', mv_body, re.DOTALL)
            for m_obj in mv_objs:
                def get_m_field(key, default=''):
                    m = re.search(rf"{key}:'([^']*)'", m_obj)
                    if not m: m = re.search(rf'{key}:"([^"]*)"', m_obj)
                    if not m: m = re.search(rf"{key}:([-?\w\d\.]+)", m_obj)
                    return m.group(1) if m else default
                m_name = get_m_field('n')
                if not m_name: continue
                
                m_dmg_raw = get_m_field('v', '0')
                m_dmg = re.sub(r'[^\d]', '', m_dmg_raw)
                if not m_dmg or m_dmg == '0': m_dmg = re.sub(r'[^\d]', '', get_m_field('p', '0'))
                if not m_dmg: m_dmg = '0'
                
                m_costs_raw = get_m_field('c', '')
                m_costs = tuple(parse_costs(m_costs_raw))
                
                # Move Effect Logic mapping
                m_effect_text = get_m_field('t')
                m_effect_tag = ""
                if "ベンチポケモン" in m_effect_text and "数" in m_effect_text:
                    if "×20" in m_effect_text: m_effect_tag = "bench_proportional_20"
                    elif "×30" in m_effect_text: m_effect_tag = "bench_proportional_30"
                elif "ポイント" in m_effect_text and "数" in m_effect_text:
                    if "×30" in m_effect_text: m_effect_tag = "point_proportional_30"
                
                # Combine info for CSV
                move_info.append((m_name, m_dmg, m_effect_tag, m_costs))
        
        # Unique check
        combo = (name, hp, card_type, tuple(move_info))
        if combo in seen_combinations:
            continue
        seen_combinations.add(combo)
        
        # Row format: cid, name, ptype, ctype, hp, stage, evolves_from, ability, effect, at1_name, at1_dmg, at1_effect, at1_costs...
        row = [cid, name, ptype, card_type, hp, stage, evolves_from, ability, card_effect_text]
        for m_name, m_dmg, m_effect_tag, m_costs in move_info:
            row.append(m_name)
            row.append(m_dmg)
            row.append(m_effect_tag)
            row.extend(m_costs)
        
        cards_to_save.append(row)

    # Write to CSV
    with open(output_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        for row in cards_to_save:
            writer.writerow(row)

    print(f"Successfully converted {len(cards_to_save)} unique cards to CSV.")

if __name__ == "__main__":
    main()
