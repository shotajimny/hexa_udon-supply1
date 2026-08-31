# 受け取ったデータをモデルに変換する関数を定義するモジュール
from receive.models import PreGameData,PreDateData


def parse_pre_game_data(data):
    return PreGameData(data)

def parse_pre_date_data(data):
    return PreDateData(data)