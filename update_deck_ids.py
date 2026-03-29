import csv
import json
import os

# Load old ID -> Name mapping
old_id_to_name = {}
with open(r"C:\Users\Yuto\Desktop\app\apps\prototypes\pockepocke\data\card_db.csv", encoding="utf-8-sig") as f:
    reader = csv.DictReader(f)
    for row in reader:
        old_id_to_name[row['id']] = row['name']

# Load Name -> New ID mapping
name_to_new_id = {}
with open(r"C:\Users\Yuto\Desktop\app\apps\prototypes\pockepocke\data\master_card_db.csv", encoding="utf-8-sig") as f:
    reader = csv.reader(f)
    for row in reader:
        if not row: continue
        new_id = row[0]
        name = row[1]
        # Keep the latest ID for a name if there are multiple?
        # GameWith IDs seem unique per card variant. 
        # We'll just take the first one we find.
        if name not in name_to_new_id:
            name_to_new_id[name] = new_id

def update_deck(path):
    if not os.path.exists(path): return
    with open(path, 'r', encoding='utf-8') as f:
        deck = json.load(f)
    
    new_cards = []
    for cid in deck['cards']:
        name = old_id_to_name.get(cid)
        if name and name in name_to_new_id:
            new_cards.append(name_to_new_id[name])
        else:
            # If not found, maybe name is different? 
            # E.g. "オドリドリ (雷)" vs "オドリドリ"
            # Try fuzzy match?
            found = False
            if name:
                base_name = name.split(' ')[0]
                if base_name in name_to_new_id:
                    new_cards.append(name_to_new_id[base_name])
                    found = True
            
            if not found:
                print(f"Warning: Could not map old ID {cid} (Name: {name}) to new database.")
                # Keep old ID (will fail later but at least we see)
                new_cards.append(cid)
    
    deck['cards'] = new_cards
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(deck, f, ensure_ascii=False, indent=2)
    print(f"Updated {path}")

# Update target decks
update_deck(r"C:\Users\Yuto\Desktop\app\apps\prototypes\pockepocke\decks\meta\ultimate_haxorus_deck.json")
update_deck(r"C:\Users\Yuto\Desktop\app\apps\prototypes\pockepocke\decks\lightning_rush_deck.json")
