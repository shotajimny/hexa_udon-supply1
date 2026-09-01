# APIにアクセスするためのクライアントを定義するモジュール
import requests

def get_setting():
    url = "http://127.0.0.1:8080/setting"
    response = requests.get(url, params={"token": "token-p0"})

    if response.status_code == 200:
        return response.json()
    else:
       return response.status_code

def get_day_data():
    url = "http://127.0.0.1:8080/"
    response = requests.get(url, params={"token": "token-p0"})

    if response.status_code == 200:
        print("get_day_data response:", response.json())  # デバッグ用の出力
        return response.json()
    else:
       print("get_day_data failed with status code:", response.status_code)  # デバッグ用の出力
       return response.status_code