# データモデルを定義するファイル

class MapData:
    #マップデータを格納するクラスを定義

    def __init__(self, data):
        self.width = data.get("width", 0)                  #int #マップの幅を格納する変数
        self.height = data.get("height", 0)                #int #マップの高さを格納する変数
        self.cells = data.get("cells", [])                 #マップのセル情報を格納するリスト


class SpotData:
    #スポットデータを格納するクラスを定義

    def __init__(self, data):
        self.brand = data.get("brand", 0)                 #スポットのブランド情報を格納する変数
        self.pos = data.get("pos", 0)                     #スポットの位置情報を格納する変数
        self.stocks = data.get("stocks", 0)               #スポットの在庫情報を格納する変数


class InitialAgentData:
    #試合開始前のエージェント一台分の情報

    def __init__(self, pos):
        self.pos = pos                     #int #巡回車の位置を格納する変数


class AgentData:
    #初期巡回車データを格納するクラスを定義

    def __init__(self, data):
        self.kind = data.get("kind", 0)                   #int #巡回車のタイプを格納する変数
        self.pos = data.get("pos", 0)                     #int #巡回車の位置を格納する変数
        self.fuel = data.get("fuel", 0)                   #int #巡回車の燃料積載量を格納する変数


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
            InitialAgentData(pos)
            for pos in data.get("agents", [])
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