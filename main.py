import time
from typing import List
from api.api_client import get_setting, get_day_data, post_agent_types, post_agent_moves
from api.models2 import PreGameData, PreDateData, CellConverter
from divide_agent_type.car_divide import divide_initial_agents
from tour_car.compare_tourcar import calculate_tourcar

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
        self.converted_map = CellConverter(
            self.pre_game.raw_map,
            self.pre_game.spots
        )


class DayData():
        # ゲーム開始後、日毎のデータを取得し、その度にデータの格納やA*探索用セルデータの更新を行うクラス

    def __init__(self):
        # APIからデータを取得する
        self.set_data = get_day_data()

    def set_pre_date(self):
        # 日毎のデータを受け取り、PreDateDataクラスのインスタンスを作成する
        self.pre_date = PreDateData(self.set_data)

    def Update_Convert_map(self, converted_map):
        # Converted_CellとPreDateDataのインスタンス(spotデータ)を使って、A*探索用のセルデータを更新する
        converted_map.rewrite_data(self.pre_date)


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


class Result_post():
    # 結果をPOSTするための処理をまとめるクラス
    def __init__(self, result_data):
        self.result_data = result_data

    def Json_output(self):
        # 結果データをJSON形式で出力する
        # 現在は仮のデータを返すが、実際にはフォーマットに従ったものを返すようにする
        return {
            "moves": self.result_data
        }

    def Post_Result(self):
        # 結果データをAPIに送信する
        post_agent_moves(self.result_data)
        

# 実行

# 1.1 初期設定の取得、PreGameDataの作成、A*探索用マップデータへの変換
setting = Setting_Pre_Game_Data()
setting.set_pre_game() #settingをselfとしてPreGameDataのインスタンスを作成する
setting.Convert_map()

# 1.2 エージェント毎の経路を格納するためのリストを作成する
daily_paths = []  # 各巡回車の経路を格納するリスト、日毎にリセットされる

# 2.エージェントタイプを決定、JSON形式で出力し、APIに送信する
divide = Divide_AgentType(setting.pre_game)
divide.Divide_agents()
post_data = divide.Json_output()
divide.Post_AgentType()

# 3.startsATまで待機
while time.time() < setting.pre_game.startsAt:
    time.sleep(0.1)

# 5.1. PreGameDataのインスタンスをcalculate_tourcarに渡して初期化する
tourcar_calculator = calculate_tourcar(setting.pre_game)

# 4.試合終了まで日数分ループする
for day in range(len(setting.pre_game.daySteps)):
    # ゲーム開始後、日毎のデータを取得し、A*探索用セルデータの更新を行う
    day_data = DayData()
    day_data.set_pre_date()
    day_data.Update_Convert_map(setting.converted_map)
    daily_paths = [
        {
            "agent_id": agent_id,
            "agent_type": agent.kind,
            "path": []
        } for agent_id, agent in enumerate(day_data.pre_date.agents)
    ]  # 各エージェントの経路を格納するリスト、日毎にリセットされる

    # 5.2 calculate_tourcarのインスタンスに日毎のデータを更新する
    tourcar_calculator.Update_Date(day_data.pre_date, setting.converted_map)

    while tourcar_calculator.has_remaining_tourcar_steps():
        # 5.3.1 経路探索を行う
        result = tourcar_calculator.calculate_path_tourcar(pre_filter_count=5)

        # 5.3.2 採択された経路をdaily_pathsへまとめる
        for assignment in result["assignments"]:
            agent_id = assignment["agent_id"]
            daily_paths[agent_id]["path"].extend(assignment["path"][1:])  # 最初の位置はすでにdaily_pathsに格納されているため、1から追加する

        # 5.3.3 余ったstepの処理(巡回車)
    
    # 5.3.4 余ったstepの処理(補給車)


    # 5.4 結果をJSON形式で出力し、APIにPOSTする
    # 仮でresultをそのままPOSTするが、実際にはフォーマットに従ったものを返すようにする
    result_post = Result_post(result)
    result_post.Json_output()
    result_post.Post_Result()


    # エージェントごとのパスをjson形式で出力し、APIにPOSTする

    # 当日の回答受付終了時間まで待機
    while time.time() < day_data.pre_date.endsAt:
        time.sleep(0.1)