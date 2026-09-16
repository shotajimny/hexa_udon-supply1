DIRECTIONS = [
    (+1, -1, 0),
    (+1, 0, -1),
    (0, +1, -1),
    (-1, +1, 0),
    (-1, 0, +1),
    (0, -1, +1),
]

class cell:
    def __init__(self):
        self.position = [] #list #検索済みのセルの位置を格納する    リスト
        self.parent = [] #list #検索済みのセルの親ノードを格納するリスト
        self.g_cost = 0 #int #検索済みのセルのgコストを格納する変数
        self.h_cost = 0 #int #検索済みのセルのhコストを格納する変数
        self.f_cost = 0 #int #検索済みのセルのfコストを格納する変数

class MapData:
    def __init__(self, position, state):
        self.position = position
        self.state = state

def heuristic(position, goal_position):
    # ヒューリスティック関数（推定コスト）
    # 六角格子では、3軸座標の最大絶対差分が近い距離になることが多い。
    # ここでは簡潔に最大差分を使って見積もる。:  
    dx = abs(position[0] - goal_position[0])
    dy = abs(position[1] - goal_position[1])
    dz = abs(position[2] - goal_position[2])
    return max(dx, dy, dz)

class AstarAlgorithm:   
    # A*アルゴリズムを実装するクラス
    def __init__(self):
        self.map_data = [] #マップデータを格納するリスト
        self.open_set : list[cell] = [] #発見済みのセルを格納するリスト
        self.closed_set : list[cell] = []#検索済みのセルを格納するリスト
        self.path = [] #計算結果の経路を格納するリスト 

    def map_input(self, map_data):
        # A*アルゴリズムに必要なマップデータを設定する関数
        # map_data: マップデータ（2Dリストなど）
        self.map_data = map_data  # マップデータを格納
     
    def search_astar(self, agent_position, goal_position):

        # 探索開始時に前回の探索結果をリセット
        self.open_set = []
        self.closed_set = []
        self.path = []

        # スタートセルの初期化
        current_cell = cell()
        current_cell.position = agent_position
        current_cell.parent = None
        current_cell.g_cost = 0
        current_cell.h_cost = heuristic(current_cell.position, goal_position)
        current_cell.f_cost = current_cell.g_cost + current_cell.h_cost

        self.open_set.append(current_cell)

        while current_cell.position != goal_position:
            # 隣接セルの計算と評価を行う
            for direction in DIRECTIONS:
                neighbor_cell = cell()
                neighbor_cell.position = [
                    current_cell.position[0] + direction[0],
                    current_cell.position[1] + direction[1],
                    current_cell.position[2] + direction[2]
                ]
                
                if neighbor_cell.position not in self.map_data.position: #セルがマップ内に存在するかどうかを判定
                    continue #マップ外のセルはスキップ
                position_index = self.map_data.position.index(neighbor_cell.position) #隣接セルの位置インデックスを取得
                if self.map_data.state[position_index] == 'lake': #セルが通行可能かどうかを判定
                    continue #通行不可能なセルはスキップ
                neighbor_cell.parent = current_cell.position
                neighbor_cell.g_cost = current_cell.g_cost + self.map_data.fuel_cost[position_index]  # セルの燃料コストに基づいてg_costを計算
                neighbor_cell.h_cost = heuristic(neighbor_cell.position, goal_position)  # 仮のヒューリスティックコスト、実際のヒューリスティック計算はgoal_positionに基づいて行う必要がある
                neighbor_cell.f_cost = neighbor_cell.g_cost + neighbor_cell.h_cost

                # 隣接セルの評価を行い、open_setに追加する処理をここに追加する
                if neighbor_cell.position in [cell.position for cell in self.closed_set]:
                    continue
                if neighbor_cell.position not in [cell.position for cell in self.open_set]:
                    self.open_set.append(neighbor_cell)
                else:
                    # 既にopen_setに存在する場合、g_costが小さい場合は更新する処理をここに追加する
                    index = next(i for i, cell in enumerate(self.open_set) if cell.position == neighbor_cell.position)
                    if neighbor_cell.g_cost < self.open_set[index].g_cost:
                        self.open_set[index] = neighbor_cell
                        self.open_set[index].f_cost = neighbor_cell.f_cost

            # open_setから最小のf_costを持つセルを選択し、current_cellを更新する処理をここに追加する
            if not self.open_set:
                return None
            min_f_cost_index = min(
                range(len(self.open_set)),
                key=lambda i: self.open_set[i].f_cost
            )
            current_cell = self.open_set[min_f_cost_index]
            # closed_setにcurrent_cellを追加する処理をここに追加する
            self.closed_set.append(current_cell)

            # open_setからcurrent_cellを削除する処理をここに追加する
            del self.open_set[min_f_cost_index]

        # goal_positionに到達した場合、経路を復元する処理をここに追加する
        self.path = []

        while current_cell is not None:
            self.path.append(current_cell.position)

            if current_cell.parent is None:
               break
   
            current_cell = next(
                cell for cell in self.closed_set
                if cell.position == current_cell.parent
                )

        self.path.reverse()
        return self.path