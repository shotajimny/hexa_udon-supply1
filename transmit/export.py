# 計算結果をjson形式で出力するモジュール
import requests

def post_agent_types(data):
    url = "http://127.0.0.1:8080/agent"

    response = requests.post(
        url,
        params={"token": "token-p0"},
        json=data
    )

    print("POST status:", response.status_code)
    print("POST response:", response.text)

    if response.status_code == 200:
        return response.json()
    else:
        return response.status_code