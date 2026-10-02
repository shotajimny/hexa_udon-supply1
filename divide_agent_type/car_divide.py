# エージェントタイプを分けるための関数をまとめたファイル
from api.models2 import PreDateData, PreGameData


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
    kind0_count = (car_count + 1) // 2 # 奇数なら巡回車を1台多くする
    kind1_count = car_count - kind0_count # 残りのエージェントをkind1にする

    return [0] * kind0_count + [1] * kind1_count


def _cube_position(pos, width):
    # CellConverterと同じ、奇数行が左にずれる0始まりの座標系。
    row, col = divmod(pos, width)
    x = col - (row + (row & 1)) // 2
    return (x, -x - row, row)


def divide_initial_agents(data):
    agents = get_agents(data)
    car_count = len(agents)
    tourcar_count = (car_count + 1) // 2
    if not data.spots:
        # スポットがない場合は元のID順で割り当てる。
        return {"kinds": divide_car_kinds(car_count)}

    width = data.raw_map["width"]
    spot_positions = [_cube_position(spot.pos, width) for spot in data.spots]

    def nearest_spot_distance(agent_id):
        position = _cube_position(agents[agent_id].pos, width)
        return min(max(abs(a - b) for a, b in zip(position, spot))
                   for spot in spot_positions)

    # 同距離ならID順。送信するkinds配列自体は元のエージェント順を保つ。
    ranked_ids = sorted(range(car_count),
                        key=lambda agent_id: (nearest_spot_distance(agent_id), agent_id))
    kinds = [1] * car_count
    for agent_id in ranked_ids[:tourcar_count]:
        kinds[agent_id] = 0
    return {"kinds": kinds}
