import base64
import json
import zipfile
import os

zip_path = "colab_temp.zip"
with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
    z.write("autonomous_loop.py")
    z.write("deck_archetypes.py")
    if os.path.exists("data/master_card_db.csv"):
        z.write("data/master_card_db.csv")

with open(zip_path, "rb") as f:
    b64_data = base64.b64encode(f.read()).decode("utf-8")

os.remove(zip_path)

notebook = {
  "cells": [
    {
      "cell_type": "markdown",
      "metadata": {},
      "source": [
        "# 完全自動・ワンクリック Colab ランナー\n",
        "このノートブックには、お使いのローカルPC上のPythonコード本体とデータが埋め込まれています。\n",
        "**注意**: 新たにGoogle Driveのマウント機能が追加されました。実行時にドライブへのアクセス許可を求められますが、これはデータを永続化（MyDrive/Pockepocke_MetaSimulator に保存）するためです。\n",
        "VSCodeからColabカーネルに接続して、すべてのセルを実行するだけで自動的に展開されて計算が開始されます！"
      ]
    },
    {
      "cell_type": "code",
      "execution_count": None,
      "metadata": {},
      "outputs": [],
      "source": [
        "import base64\n",
        "import zipfile\n",
        "import os\n",
        "try:\n",
        "    from google.colab import drive\n",
        "    drive.mount('/content/drive')\n",
        "    work_dir = '/content/drive/MyDrive/Pockepocke_MetaSimulator'\n",
        "    os.makedirs(work_dir, exist_ok=True)\n",
        "    os.chdir(work_dir)\n",
        "    print('Google Driveにマウントし、作業ディレクトリを移動しました。:', work_dir)\n",
        "except Exception as e:\n",
        "    print('Colab環境ではないか、マウントに失敗しました。ローカル一時領域を使用します。', e)\n",
        "\n",
        "b64_string = '" + b64_data + "'\n",
        "zip_path = 'colab_temp.zip'\n",
        "\n",
        "with open(zip_path, 'wb') as f:\n",
        "    f.write(base64.b64decode(b64_string))\n",
        "\n",
        "with zipfile.ZipFile(zip_path, 'r') as z:\n",
        "    z.extractall('.')\n",
        "os.remove(zip_path)\n",
        "\n",
        "os.makedirs('gui', exist_ok=True)\n",
        "os.makedirs('logs/autonomous', exist_ok=True)\n",
        "print('【完了】スクリプトとデータが展開されました！ログはGoogleドライブに永続的に記録されます。')\n"
      ]
    },
    {
      "cell_type": "code",
      "execution_count": None,
      "metadata": {},
      "outputs": [],
      "source": [
        "# 100万人規模（10,000デッキ）のシミュレーターを超高速起動\n",
        "!python autonomous_loop.py\n"
      ]
    }
  ],
  "metadata": {
    "kernelspec": {
      "display_name": "Python 3",
      "language": "python",
      "name": "python3"
    },
    "language_info": {
      "name": "python",
      "version": "3.8.0"
    }
  },
  "nbformat": 4,
  "nbformat_minor": 4
}

with open("Ultimate_Colab_Runner.ipynb", "w", encoding="utf-8") as f:
    json.dump(notebook, f, ensure_ascii=False, indent=2)

print("Ultimate_Colab_Runner.ipynb has been generated successfully.")
