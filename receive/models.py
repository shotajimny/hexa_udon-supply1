# データモデルを定義するファイル

class Pre_game_data:
    #試合開始前ゲーム情報を取得するためのクラスを定義

    def __init__(self, data):
        self.starsAT = data.get("startsAT", 0)                  #int #試合開始時刻を格納する変数
        self.daySeconds = data.get("daySeconds", 0)             #int #1日の構成秒数を格納する変数
        self.daySteps = data.get("daySteps", 0)                 #int #各日の構成ステップ数を格納する変数

        self.maps = data.get("maps", {})                        #マップ情報を格納するリスト
        self.width = self.maps.get("width", 0)                  #int #マップの幅を格納する変数
        self.height = self.maps.get("height", 0)                #int #マップの高さを格納する変数
        self.cells = self.maps.get("cells", [])                 #マップのセル情報を格納するリスト

        self.spots = data.get("spots", [])                      #スポット情報を格納するリスト
        self.brand = self.spots.get("brand", 0)                 #スポットのブランド情報を格納する変数
        self.pos = self.spots.get("pos", 0)                     #スポットの位置情報を格納する変数
        self.stocks = self.spots.get("stocks", 0)               #スポットの在庫情報を格納する変数

        self.tourcar = data.get("agents", [])                    #巡回車の位置を格納するリスト

        self.fuelLimits = data.get("fuelLimits", 0)             #巡回車の燃料制限を格納する変数
        self.players = data.get("players", 0)                   #int #プレイヤー数を格納する変数
        self.busyThreshold = data.get("busyThreshold", 0)       #int #巡回車の混雑閾値を格納する変数
        self.jammedThreshold = data.get("jammedThreshold", 0)   #int #巡回車の渋滞閾値を格納する変数


class Pre_date_data:
    #各日のゲーム情報を取得するためのクラスを定義

    def __init__(self, data):
        self.endAT = data.get("endAT", 0)                           #int #各日回答受付終了時刻を格納する変数
        self.day = data.get("day", 0)                               #int #日付を格納する変数(初日は0)

        self.my_agents = data.get("agents", [])                     #エージェント情報を格納するリスト
        self.kind = self.my_agents.get("kind", 0)                   #int #エージェントタイプを格納する変数
        self.pos = self.my_agents.get("pos", 0)                     #int #エージェントの位置を格納する変数
        self.fuel = self.my_agents.get("fuel", 0)                   #int #エージェントの燃料積載量を格納する変数

        self.others = data.get("others", [])                        #他のプレイヤーの情報を格納するリスト
        self.id = self.others.get("id", 0)                          #int #他のプレイヤーのIDを格納する変数
        self.other_player_agents = self.others.get("agents", [])    #他のプレイヤーの巡回車情報を格納するリスト
        self.kind = self.other_player_agents.get("kind", 0)         #int #他のプレイヤーの巡回車タイプを格納する変数
        self.pos = self.other_player_agents.get("pos", 0)           #int #他のプレイヤーの巡回車位置を格納する変数
        self.fuel = self.other_player_agents.get("fuel", 0)         #int #他のプレイヤーの巡回車燃料積載量を格納する変数

        self.traffics = data.get("traffics", [])                    #道路の渋滞情報を格納するリスト
        self.pos = self.traffics.get("pos", 0)                      #int #道路の位置を格納する変数
        self.status = self.traffics.get("status", 0)                #int #各道路セルの状態を格納する変数(0:順調, 1:混雑, 2:渋滞)
