from tour_car.Bias_tourcar import select_spots
from tour_car.Bias_tourcar import TOUR_CAR, SPOT_DATA

DIRECTIONS = [
    [+1, -1, 0],
    [+1, 0, -1],
    [0, +1, -1],
    [-1, +1,  0],
    [-1,  0, +1],
    [ 0, -1, +1]
]

def heuristic(position, goal_position):
        # ヒューリスティック関数の計算を行う関数
        # position: 現在位置
        # goal_position: 目標位置
        # ここにヒューリスティック関数の実装を追加する
        return sum((p - g) ** 2 for p, g in zip(position, goal_position)) ** 0.5  # ユークリッド距離を使用

class AstarAlgorithm:
    def __init__(self):
        self.map_data = None
        self.open_set = { # 探索中のノードを格納するリスト
            'position': [],
            'parent': [],
            'g_cost': [],
            'h_cost': [],
            'f_cost': [] 
        }
        self.closed_set = { # 探索済みのノードを格納するリスト
            'position': [],
            'parent': [],
            'g_cost': [],
            'h_cost': [],
            'f_cost': []
        }
        self.path = None

    def compute_astar(self, map_data):
        # A*アルゴリズムの計算を行う関数
        # map_data: マップデータ（2Dリストなど）
        # ここにA*アルゴリズムの実装を追加する
        self.map_data = map_data  # マップデータを格納
        
    # A*アルゴリズムのロジックをここに実装する
    def search_astar(self, agent_position, goal_position, agent_fuel):
        # A*アルゴリズムの探索を行う関数
        # agent_position: エージェントの現在位置
        # goal_position: 目標位置
        # agent_fuel: エージェントの燃料
        # ここにA*アルゴリズムの探索ロジックを追加する
        current_cell = {  #現在のセルの情報を格納する辞書
            'position': agent_position,
            'parent': None,
            'g_cost': 0,
            'h_cost': heuristic(agent_position, goal_position),
            'f_cost': 'g_cost' + 'h_cost',
            'fuel': agent_fuel
        }
        neighbor_cell = {  # 隣接セルのリストを初期化
            'position': [],
            'parent': [],
            'g_cost': 0,
            'h_cost': heuristic(goal_position, goal_position),
            'f_cost': 'g_cost' + 'h_cost',
            'fuel': None
        }

        while current_cell['position'] != goal_position:
            # 隣接セルの計算と評価を行う
            for direction in DIRECTIONS:
                neighbor_cell = {
                    'position': [
                        current_cell['position'][0] + direction[0],
                        current_cell['position'][1] + direction[1],
                        current_cell['position'][2] + direction[2]
                    ],
                    'parent': current_cell['position'],
                    'g_cost': current_cell['g_cost'],
                    'h_cost': 0, #仮のヒューリスティックコスト、実際のヒューリスティック計算はgoal_positionに基づいて行う必要がある
                    'f_cost': 'g_cost' + 'h_cost'
                }
                position_index = self.map_data['position'].index(neighbor_cell['position']) #位置インデックスを取得
                if self.map_data['state'][position_index] == 'lake': #セルが通行可能かどうかを判定
                    continue #通行不可能なセルはスキップ
                neighbor_cell['g_cost'] += self.map_data['step_cost'][position_index] #コスト計算、map_dataよりセルの状態に依存

                neighbor_cell['h_cost'] = heuristic(neighbor_cell['position'], goal_position)
                neighbor_cell['f_cost'] = neighbor_cell['g_cost'] + neighbor_cell['h_cost']
                neighbor_cell['fuel'] = current_cell['fuel'] - self.map_data['fuel_cost'][position_index] #燃料消費計算、map_dataよりセルの状態に依存

                # 隣接セルの評価を行い、open_setに追加する処理をここに追加する
                if neighbor_cell['position'] not in self.open_set['position']:
                    self.open_set['position'].append(neighbor_cell['position'])
                    self.open_set['parent'].append(neighbor_cell['parent'])
                    self.open_set['g_cost'].append(neighbor_cell['g_cost'])
                    self.open_set['h_cost'].append(neighbor_cell['h_cost'])
                    self.open_set['f_cost'].append(neighbor_cell['f_cost'])
                    self.open_set['fuel'].append(neighbor_cell['fuel'])
                else:
                    # 既にopen_setに存在する場合、g_costが小さい場合は更新する処理をここに追加する
                    index = self.open_set['position'].index(neighbor_cell['position'])
                    if neighbor_cell['g_cost'] < self.open_set['g_cost'][index]:
                        self.open_set['parent'][index] = neighbor_cell['parent']
                        self.open_set['g_cost'][index] = neighbor_cell['g_cost']
                        self.open_set['h_cost'][index] = neighbor_cell['h_cost']
                        self.open_set['f_cost'][index] = neighbor_cell['f_cost']
                        self.open_set['fuel'][index] = neighbor_cell['fuel']

            # open_setから最小のf_costを持つセルを選択し、current_cellを更新する処理をここに追加する
            min_f_cost_index = self.open_set['f_cost'].index(min(self.open_set['f_cost']))
            current_cell = {
                'position': self.open_set['position'][min_f_cost_index],
                'parent': self.open_set['parent'][min_f_cost_index],
                'g_cost': self.open_set['g_cost'][min_f_cost_index],
                'h_cost': self.open_set['h_cost'][min_f_cost_index],
                'f_cost': self.open_set['f_cost'][min_f_cost_index],
                'fuel': self.open_set['fuel'][min_f_cost_index]
            }
            # closed_setにcurrent_cellを追加する処理をここに追加する
            self.closed_set['position'].append(current_cell['position'])
            self.closed_set['parent'].append(current_cell['parent'])
            self.closed_set['g_cost'].append(current_cell['g_cost'])
            self.closed_set['h_cost'].append(current_cell['h_cost'])
            self.closed_set['f_cost'].append(current_cell['f_cost'])
            self.closed_set['fuel'].append(current_cell['fuel'])

        # goal_positionに到達した場合、経路を復元する処理をここに追加する
        self.path = []
        while current_cell['parent'] is not None:
            self.path.append(current_cell['position'])
            parent_index = self.closed_set['position'].index(current_cell['parent'])
            current_cell = {
                'position': self.closed_set['position'][parent_index],
                'parent': self.closed_set['parent'][parent_index],
                'g_cost': self.closed_set['g_cost'][parent_index],
                'h_cost': self.closed_set['h_cost'][parent_index],
                'f_cost': self.closed_set['f_cost'][parent_index],
                'fuel': self.closed_set['fuel'][parent_index]
            }
        self.path.append(current_cell['position']) # agent_positionを追加
        self.path.reverse() # 経路を逆順にする

        return self.path  # 計算結果の経路を返す