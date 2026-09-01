from fastapi import FastAPI
from pydantic import BaseModel
from typing import List
from receive.api_client import get_setting, get_day_data
from receive.models2 import PreGameData, PreDateData, Convert_Cell
from divide_agent_type.car_divide import divide_initial_agents
from transmit.export import  post_agent_types


app = FastAPI()

class Setting_Pre_Game_Data():
    # ゲーム開始前の初期設定を取得し、データの格納やA*探索用セルデータへの変換を行うクラス

    def __init__(self):
        # APIからデータを取得する
        self.set_data = get_setting()

    def set_pre_game(self):
        # 初期設定データを受け取り、PreGameDataクラスのインスタンスを作成する
        self.pre_game = PreGameData(self.set_data)

    def Convert_map(self):
        # set_dataとPreGameDataのインスタンス(spotデータ)を使って、A*探索用のセルデータに変換する
        self.convert_cells = Convert_Cell(self.set_data, self.pre_game.spots)

class DayData():
        # ゲーム開始後、日毎のデータを取得し、その度にデータの格納やA*探索用セルデータの更新を行うクラス

    def __init__(self):
        # APIからデータを取得する
        self.set_data = get_day_data()

    def set_pre_date(self):
        # 日毎のデータを受け取り、PreDateDataクラスのインスタンスを作成する
        self.pre_date = PreDateData(self.set_data)

    def Update_Convert_map(self, Converted_Cell):
        # Converted_CellとPreDateDataのインスタンス(spotデータ)を使って、A*探索用のセルデータを更新する
        self.update_map = Convert_Cell.convert_cells_load(
            self.pre_date.traffics, 
            Converted_Cell
            )

class Divide_AgentType():
    # エージェントの種類を分けるためのクラス

    def __init__(self, pre_game_data):
        # PreGameDataのインスタンスを受け取り、エージェントの種類を分ける
        self.pre_game_data = pre_game_data

    def Divide_agents(self):
        # PreGameDataのインスタンスからエージェントの種類を分ける
        self.divided_agents = divide_initial_agents(self.pre_game_data)

    def Json_output(self):
        # 分けたエージェントの種類をJSON形式で出力する
        # divided_agentsのkindsのみを返す

        return {
            "kinds": self.divided_agents["kinds"]
        }

    def Post_AgentType(self):
        # 分けたエージェントの種類をAPIに送信する
        post_agent_types(self.divided_agents["kinds"])

# 実行

# 初期設定の取得とA*探索用セルデータの変換
setting = Setting_Pre_Game_Data()

setting.set_pre_game()
setting.Convert_map()

# エージェントタイプを指定
divide = Divide_AgentType(setting.pre_game)

divide.Divide_agents()

post_data = divide.Json_output()

post_agent_types(post_data)

# ゲーム開始後、日毎のデータを取得し、A*探索用セルデータの更新を行う
day_data = DayData()
day_data.set_pre_date()
day_data.Update_Convert_map(setting.convert_cells)