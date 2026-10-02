#受け取ったデータを経路探索用に変換するための関数を定義するファイル

class CellConverter:
    def __init__(self, setting_data, spots=None):
        #初期設定を受け取る
        #初日のデータを受け取る
        self.setting_data = setting_data
        self.spots = spots or []
        self.cells = self.convert_cells(setting_data)

    def rewrite_data(self, data):
        # 毎日のデータを更新
        self.date_data = data

        # 道路セルの情報を更新
        for road_cell in data.traffics:
            index = road_cell.pos

            # エラーチェック: 受け取ったデータのposがセルの範囲外でないか確認する
            if not 0 <= index < len(self.cells):
                raise ValueError(f"不正な道路位置: {road_cell.pos}")

            self.cells[index].state = road_cell.status
            self.cells[index].step_cost = self._convert_step_cost(
                1,
                road_cell.status
            )

    def _convert_terrain_type(self, terrain_code):
        #地形タイプを変換する関数を定義する
        terrain_type_dict = {
            0: "plain",
            1: "road",
            2: "hill",
            3: "lake"
        }
        return terrain_type_dict.get(terrain_code, "unknown")


    def _convert_step_cost(self, terrain_code, state):
        #移動コストを変換する関数を定義する
        if terrain_code != 1:
            step_cost_dict = {
                0: 2.0,  #平地
                2: 3.0,  #山地
                3: float('inf')  #湖
            }
        else:
            step_cost_dict = {
                0: 1.0,  #順調
                1: 2.0,  #混雑
                2: 4.0  #交通渋滞
            }


        return step_cost_dict.get(state, float('inf'))

    def _convert_fuel_cost(self, terrain_code):
        #燃料コストを変換する関数を定義する
        fuel_cost_dict = {
            0: 1.0,  #平地
            1: 2.0,  #道路
            2: 2.0,  #山地
            3: float('inf')  #湖
        }

        return fuel_cost_dict.get(terrain_code, float('inf'))


    def convert_cells(self, data):
        #受け取る(使用する)データはheight、width、セルの配列である
        #返すセルの情報は座標、地形タイプ、状態、移動コスト、燃料コストである
        #APIから取得したセルに関する情報を経路探索用に変換するための関数を定義する
        converted_cells = []
        width = data.get("width", 0)
        height = data.get("height", 0)

        for row in range(height):
            for col in range(width):

                #地形タイプを取得する
                terrain_code = data.get("cells", [])[row][col]

                # 3軸座標系に変換する(奇数行が左にずれている)
                x = col - (row - (row & 1)) // 2
                z = row
                y = -x - z

                state=0

                converted_cells.append(
                    CellData(
                        position=[x, y, z],
                        terrain_type=self._convert_terrain_type(terrain_code),
                        state=state,
                        step_cost=self._convert_step_cost(terrain_code, state),
                        fuel_cost=self._convert_fuel_cost(terrain_code)
                    )
                )

        #スポット情報を対応するセルに設定する
        for spot in self.spots:
            index = spot.pos 
            if 0 <= index < len(converted_cells):
                converted_cells[index].spot = spot


        return converted_cells


class CellData:
    def __init__(self, position, terrain_type, state, step_cost, fuel_cost, spot=None):
        #マップのセル情報を格納するクラスを定義
        self.position = position                         #List[int] #マップの座標を格納する変数
        self.terrain_type = terrain_type                 #str #マップの地形タイプを格納する変数
        self.state = state                               #int #マップの状態を格納する変数
        self.step_cost = step_cost                       #float #マップの移動コストを格納する変数
        self.fuel_cost = fuel_cost                       #float #マップの燃料コストを格納する変数
        self.spot = spot                                 #SpotData #対応するスポットデータを格納する変数

class SpotData:
    #スポットデータを格納するクラスを定義

    def __init__(self, data):
        self.brand = data.get("brand", 0)                 #スポットのブランド情報を格納する変数
        self.pos = data.get("pos", 0)                     #スポットの位置情報を格納する変数
        self.stocks = data.get("stocks", 0)               #スポットの在庫情報を格納する変数


class preAgentData:
    #試合開始前のエージェントの情報

    def __init__(self, pos):
        self.pos = pos                    #int #巡回車の位置を格納する変数


class OtherPlayerData:
    # 他プレイヤー1人分の情報

    def __init__(self, data):
        self.id = data.get("id", 0)
        self.agents = [
            AgentData(agent)
            for agent in data.get("agents", [])
        ]


class TrafficData:
    # 道路1セル分の渋滞情報

    def __init__(self, data):
        self.pos = data.get("pos", 0)
        self.status = data.get("status", 0)


class AgentData:
    #初期巡回車データを格納するクラスを定義

    def __init__(self, data):
        self.kind = data.get("kind", 0)                   #int #巡回車のタイプを格納する変数
        self.pos = data.get("pos", 0)                     #int #巡回車の位置を格納する変数
        self.fuel = data.get("fuel", 0)                   #int #巡回車の燃料積載量を格納する変数


class PreGameData:
    # 試合開始前のゲーム情報

    def __init__(self, data):
        self.startsAt = data.get("startsAt", 0)
        self.daySeconds = data.get("daySeconds", 0)
        self.daySteps = data.get("daySteps", [])

        self.raw_map = data.get("map", {})                     #マップ情報を格納する変数

        self.spots = [
            SpotData(spot)
            for spot in data.get("spots", [])
        ]

        self.agents = [
            preAgentData(agent)
            for agent in data.get("agents", [])
        ]

        self.fuelLimits = data.get("fuelLimits", 0)
        self.players = data.get("players", 0)
        self.busyThreshold = data.get("busyThreshold", 0)
        self.jammedThreshold = data.get("jammedThreshold", 0)


class PreDateData:
    # 各日のゲーム情報

    def __init__(self, data):
        self.endsAt = data.get("endsAt", 0)
        self.day = data.get("day", 0)

        self.agents = [
            AgentData(agent)
            for agent in data.get("agents", [])
        ]

        self.others = [
            OtherPlayerData(player)
            for player in data.get("others", [])
        ]

        self.traffics = [
            TrafficData(traffic)
            for traffic in data.get("traffics", [])
        ]
