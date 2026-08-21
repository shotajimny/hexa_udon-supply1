# APIにアクセスするためのクライアントを定義するモジュール
import json
from urllib.request import urlopen

BASE_URL = "http://192.168.0.52:8000/api/map"  # APIのベースURLを設定


def get_pre_game_data():
    with urlopen(f"{BASE_URL}") as response:
        return json.loads(response.read().decode("utf-8"))

#試合前のデータを取得する関数
#def get_pre_game_data():
#    with urlopen(f"{BASE_URL}/pre-game-data") as response:
#       return json.loads(response.read().decode("utf-8"))

#試合中各日のデータを取得する関数
#def get_pre_date_data():
#    with urlopen(f"{BASE_URL}/pre-date-data") as response:
#        return json.loads(response.read().decode("utf-8"))