# データモデルを定義するファイル


def convert_cells(self):
    #APIから取得したセルに関する情報を経路探索用に変換するための関数を定義する
    converted_cells = []

    for row, row_data in enumerate(self.raw_cells):
        for column, terrain_code in enumerate(row_data):
            index = row * self.width + column

            # 3軸座標系に変換する(奇数行が左にずれている)
            x = 0
            if( column % 2 != 0):
                x = x - 1
            z = row
            y = -x - z

            converted_cells.append(
                CellData(
                    index=index,
                    row=row,
                    column=column,
                    position=[x, y, z],
                    terrain_code=terrain_code,
                    state=self._convert_state(terrain_code),
                )
            )

    return converted_cells


class CellData:
    #マップのセル情報を格納するクラスを定義
    def __init__(
            self,
            index,
            row,
            col,
            position,
            terrain_type,
            state,
            step_cost,
            fuel_cost
    ):
        self.index = index                               #int #マップのインデックスを格納する変数
        self.row = row                                   #int #マップの行数を格納する変数
        self.col = col                                   #int #マップの列数を格納する変数
        self.position = position                         #List[int] #マップの座標を格納する変数
        self.terrain_type = terrain_type                 #str #マップの地形タイプを格納する変数
        self.state = state                               #str #マップの状態を格納する変数
        self.step_cost = step_cost                       #float #マップの移動コストを格納する変数
        self.fuel_cost = fuel_cost                       #float #マップの燃料コストを格納する変数


class MapData:
    #マップデータを格納するクラスを定義

    def __init__(self, data):
        self.width = data.get("width", 0)                 #マップの横幅を格納する変数
        self.height = data.get("height", 0)               #マップの高さを格納する変数

        #APIから受け取った元のデータ
        self.raw_cells = data.get("cells", [])                     #マップのセル情報を格納する変数

        #探索用に変換したデータ
        self.cells = self.convert_cells()

        # A*から使いやすい形式
        self.position = [cell.position for cell in self.cells]
        self.state = [cell.state for cell in self.cells]
        self.step_cost = [cell.step_cost for cell in self.cells]
        self.fuel_cost = [cell.fuel_cost for cell in self.cells]


class SpotData:
    #スポットデータを格納するクラスを定義

    def __init__(self, data):
        self.brand = data.get("brand", 0)                 #スポットのブランド情報を格納する変数
        self.pos = data.get("pos", 0)                     #スポットの位置情報を格納する変数
        self.stocks = data.get("stocks", 0)               #スポットの在庫情報を格納する変数


class preAgentData:
    #試合開始前のエージェントの情報

    def __init__(self, data):
        self.pos = data.get("pos", [])                     #int #巡回車の位置を格納する変数


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

        self.map = MapData(
            data.get("map", {})
        )

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