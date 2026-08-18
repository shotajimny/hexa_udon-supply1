# 受け取ったデータをモデルに変換する関数を定義するモジュール
from receive.models import MapData, SpotData, InitialAgentData, AgentData, OtherPlayerData, TrafficData, PreGameData,PreDateData

def parse_map_data(data):
    return MapData(data)

def parse_spot_data(data):
    return SpotData(data)

def parse_initial_agent_data(data):
    return InitialAgentData(data)

def parse_agent_data(data):
    return AgentData(data)

def parse_other_player_data(data):
    return OtherPlayerData(data)

def parse_traffic_data(data):
    return TrafficData(data)

def parse_pre_game_data(data):
    return PreGameData(data)

def parse_pre_date_data(data):
    return PreDateData(data)