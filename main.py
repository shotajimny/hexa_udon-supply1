from fastapi import FastAPI
from pydantic import BaseModel
from typing import List
from receive.api_client import get_setting
from receive.parser import parse_pre_game_data, parse_pre_date_data

app = FastAPI()

#初期設定をとってくる
@app.get("/setting")
def get_setting_endpoint():
    return get_setting()

def rewrite_setting_data():
    #初期設定を計算用に書き換える
    return parse_pre_game_data(get_setting())

print(rewrite_setting_data())