import re
import json
from pathlib import Path

def extract_json_from_html():
    html_path = Path("data/page_full_source.html")
    with open(html_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # window.wmt.pokemonDatas=[...] を探す
    match = re.search(r"window\.wmt\.pokemonDatas\s*=\s*(\[.*?\]);", content, re.DOTALL)
    if match:
        json_str = match.group(1)
        # JavaScriptのリテラル（シングルクォート等）をJSON形式に簡易修正
        # 今回は幸い、取得したデータは有効なJSONに近い形式のはず
        try:
            data = json.loads(json_str)
            with open("data/raw_gamewith_data.json", "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False)
            print(f"JSON抽出成功: {len(data)} 枚のカード")
            return True
        except Exception as e:
            print(f"JSONパースエラー: {e}")
            # エラー時に内容を確認するためのデバッグ
            with open("data/error_match.txt", "w", encoding="utf-8") as f:
                f.write(json_str[:1000])
            return False
    else:
        print("pokemonDatasが見つかりませんでした。")
        return False

if __name__ == "__main__":
    extract_json_from_html()
