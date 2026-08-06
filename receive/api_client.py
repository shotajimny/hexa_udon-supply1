# APIにアクセスするためのクライアントを定義するモジュール
import requests

BASE_URL = "http://localhost:3000/api"  # APIのベースURLを設定

def get_pre_game_data():
    game_data = requests.get(f"{BASE_URL}/pre-game-data")
    return game_data.json()

def get_pre_date_data():
    date_data = requests.get(f"{BASE_URL}/pre-date-data")
    return date_data.json()