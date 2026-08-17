# APIにアクセスするためのクライアントを定義するモジュール
import json
from urllib.request import urlopen

BASE_URL = "http://localhost:3000/api"  # APIのベースURLを設定

def get_pre_game_data():
    with urlopen(f"{BASE_URL}/pre-game-data") as response:
        return json.loads(response.read().decode("utf-8"))

def get_pre_date_data():
    with urlopen(f"{BASE_URL}/pre-date-data") as response:
        return json.loads(response.read().decode("utf-8"))