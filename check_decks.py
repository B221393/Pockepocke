import json
from pathlib import Path
from simulator import load_deck_from_json

def check_decks():
    selected_decks = []
    meta_dir = Path("decks/archetypes")
    archetype_folders = ["energy_accel", "evolve_power", "hand_dest", "sleep", "gimmick"]
    for folder in archetype_folders:
        path = meta_dir / folder
        if path.exists():
            files = list(path.glob("*.json"))
            if files:
                best = sorted(files, key=lambda x: x.name, reverse=True)[0]
                selected_decks.append(best)

    exp_dir = Path("decks/experimental")
    if exp_dir.exists():
        selected_decks.extend(list(exp_dir.glob("*.json")))

    ex_dir = Path("decks/ex_axes")
    if ex_dir.exists():
        for d in ex_dir.glob("**/standard_axis.json"):
            if len(selected_decks) < 20:
                if d not in selected_decks:
                    selected_decks.append(d)

    unique_paths = list(dict.fromkeys(selected_decks))[:20]
    
    print(f"Checking {len(unique_paths)} decks...")
    for p in unique_paths:
        try:
            cards = load_deck_from_json(p)
            print(f"[OK] {p}: {len(cards)} cards")
        except Exception as e:
            print(f"[ERR] {p}: {e}")

if __name__ == "__main__":
    check_decks()
