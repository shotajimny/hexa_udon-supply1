# APIにアクセスするためのクライアントを定義するモジュール
import requests

def get_setting():
    url = "http://127.0.0.1:8080/setting"
    response = requests.get(url, params={"token": "token-p0"})

    if response.status_code == 200:
        return response.json()
    else:
       return response.status_code

