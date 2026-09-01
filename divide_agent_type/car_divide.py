# エージェントタイプを分けるための関数をまとめたファイル
from receive.models2 import PreDateData, PreGameData


def get_agents(data):
    # エージェントの情報だけ抜き取る
    # PreGameData / PreDateData または agents のリストからエージェントに関するリストを取り出す
    if isinstance(data, (PreGameData, PreDateData)):
        return data.agents

    return data


def count_agents(data): 
    # エージェントの数を数える
    agents = get_agents(data)
    return len(agents)


def divide_car_kinds(car_count): 
    # 0 or 1 に分ける
    # 0: 巡回車, 1: 補給車
    kind0_count = (car_count + 1) // 2 #0から半数までのエージェントをkind0にする
    kind1_count = car_count - kind0_count # 残りのエージェントをkind1にする

    return [0] * kind0_count + [1] * kind1_count


def divide_initial_agents(data): 
    # 上記の内容をまとめる関数
    car_count = count_agents(data) # エージェントの数を入れる

    return {
        "kinds": divide_car_kinds(car_count),
    }
