from receive.api_client import get_pre_game_data
from receive.models import AgentData, InitialAgentData, PreDateData, PreGameData
from receive.parser import parse_pre_game_data


def get_agents(data):#エージェントの情報だけ抜き取る
    # PreGameData / PreDateData または agents のリストから巡回車リストを取り出す
    if isinstance(data, (PreGameData, PreDateData)):
        return data.agents

    return data


def count_agents(data): #エージェントの数を数える
    agents = get_agents(data)
    return len(agents)


def divide_car_kinds(car_count): #0 or 1 に分ける
    kind0_count = (car_count + 1) // 2
    kind1_count = car_count - kind0_count

    return [0] * kind0_count + [1] * kind1_count


def divide_initial_agents(data): #上記の内容をまとめる関数
    agents = get_agents(data)
    car_count = count_agents(agents)

    return {
        "total": car_count,
        "positions": [
            agent.pos
            for agent in agents
        ],
        "kinds": divide_car_kinds(car_count),
    }
