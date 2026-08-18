# A*アルゴリズムを実装するためのモジュール
# このファイルでは、六角格子上を移動するエージェントの経路探索を行う。
# 各セルは3次元座標 (x, y, z) で表し、六方向への移動を考慮する。
import heapq

# 六角格子での6方向への移動量を定義する。
# これは「1歩で進める隣接セル」の差分座標である。
DIRECTIONS = [
    [+1, -1, 0],
    [+1, 0, -1],
    [0, +1, -1],
    [-1, +1, 0],
    [-1, 0, +1],
    [0, -1, +1],
]


class searched_cells:
    # 探索済みセルの情報を保持するためのクラス。
    # ここには、すでに訪問したセルの経路情報を格納する。
    def __init__(self):
        self.position = []      # セルの座標 (x, y, z)
        self.parent = None      # 親ノードの座標
        self.g_cost = 0         # スタートからの実コスト
        self.h_cost = 0         # 目標までの推定コスト
        self.f_cost = 0         # g_cost + h_cost


class searching_cells(searched_cells):
    # 探索中のセルにだけ必要な情報を足したクラス。
    # 燃料消費量は現在地の評価に使うため保持する。
    def __init__(self):
        super().__init__()
        self.fuel = 0          # そのセルに到達したときの残燃料


def heuristic(position, goal_position):
    # ヒューリスティック関数（推定コスト）
    # 六角格子では、3軸座標の最大絶対差分が近い距離になることが多い。
    # ここでは簡潔に最大差分を使って見積もる。
    dx = abs(position[0] - goal_position[0])
    dy = abs(position[1] - goal_position[1])
    dz = abs(position[2] - goal_position[2])
    return max(dx, dy, dz)


class AstarAlgorithm:
    # A*探索をまとめて管理するクラス。
    # このクラスが、地図の受け取りから経路計算・結果の返却までを担当する。
    def __init__(self):
        # 初期化時に探索に必要な状態を空にする。
        self.map_data = []        # マップ全体の情報
        self.open_set = []        # 現在探索候補になっているセル
        self.closed_set = []      # すでに探索済みのセル
        self.path = []            # 最終的に見つかった経路

    def map_input(self, map_data):
        # 外部からマップデータを受け取る。
        # これは API から取得した地図情報や仮のテストデータでも使える。
        self.map_data = map_data

    def _get_positions(self):
        # マップ上の全セルの座標を取得する。
        # 例: data.position, data.pos, または dict['position'] を許容する。
        if hasattr(self.map_data, 'position'):
            return list(self.map_data.position)
        if hasattr(self.map_data, 'pos'):
            return list(self.map_data.pos)
        if isinstance(self.map_data, dict):
            return self.map_data.get('position') or self.map_data.get('positions') or []
        return []

    def _get_states(self):
        # 各セルの状態を取得する。
        # 'land' なら進める, 'lake' なら進めない という扱いを想定する。
        if hasattr(self.map_data, 'state'):
            return list(self.map_data.state)
        if hasattr(self.map_data, 'status'):
            return list(self.map_data.status)
        if isinstance(self.map_data, dict):
            return self.map_data.get('state') or self.map_data.get('status') or []
        return []

    def _cell_index(self, position):
        # 指定した座標が map_data 内のどのインデックスに対応するかを返す。
        positions = self._get_positions()
        if not positions:
            return None

        target = list(position)
        if target in positions:
            return positions.index(target)
        return None

    def _is_walkable(self, position):
        # 指定座標に進めるかどうかを確認する。
        # 進めないセルは 'lake', 'wall', 'blocked' などを想定する。
        positions = self._get_positions()
        if not positions:
            # マップデータが未定義なら、とりあえず進める扱いにする。
            return True

        index = self._cell_index(position)
        if index is None:
            # マップ上に存在しない座標は進めない。
            return False

        states = self._get_states()
        if not states:
            # 状態情報がない場合は通行可能とみなす。
            return True

        if index >= len(states):
            return False

        state = states[index]
        return state not in [None, '', 'lake', 'blocked', 'wall']

    def compute_cost(self, position):
        # 指定セルの移動コストを計算する。
        # step_cost と fuel_cost があれば、それらを合計して使う。
        index = self._cell_index(position)
        if index is None:
            return 1

        step_cost = 1
        fuel_cost = 1
        if hasattr(self.map_data, 'step_cost'):
            step_cost = self.map_data.step_cost[index]
        if hasattr(self.map_data, 'fuel_cost'):
            fuel_cost = self.map_data.fuel_cost[index]
        return float(step_cost) + float(fuel_cost)

    def search_astar(self, agent_position, goal_position, agent_fuel):
        # A*探索のメイン処理。
        # agent_position: 現在位置
        # goal_position: 目標位置
        # agent_fuel: 現在の燃料量
        # 戻り値: [ [x, y, z], ... ] の経路座標リスト
        start = tuple(agent_position)
        goal = tuple(goal_position)

        # 各探索結果を初期化する。
        self.open_set = []
        self.closed_set = []
        self.path = []

        # 開始地点または目標地点が通行不能なら探索しない。
        if not self._is_walkable(start) or not self._is_walkable(goal):
            return []

        # 同じ地点ならそのまま終了とみなす。
        if start == goal:
            return [list(start)]

        # 燃料が0以下なら進めない。
        if agent_fuel is not None and agent_fuel <= 0:
            return []

        # heapq は優先度付きキューで、f = g + h が最小のノードを取り出す。
        open_heap = []
        heapq.heappush(open_heap, (heuristic(start, goal), 0.0, start))
        came_from = {}      # どの親ノードから来たかを記録
        g_score = {start: 0.0}  # 各座標までの実コスト

        # 探索候補がなくなるまで繰り返す。
        while open_heap:
            _, current_cost, current = heapq.heappop(open_heap)

            # すでにより安い経路が見つかっているなら無視する。
            if current_cost > g_score.get(current, float('inf')):
                continue

            # 目標に着いたら探索終了。
            if current == goal:
                break

            # 現在地から6方向へ隣接セルを確認する。
            for direction in DIRECTIONS:
                neighbor = (
                    current[0] + direction[0],
                    current[1] + direction[1],
                    current[2] + direction[2],
                )

                # 移動先が通行不能ならスキップする。
                if not self._is_walkable(neighbor):
                    continue

                # その隣接セルへのコストを計算する。
                move_cost = self.compute_cost(neighbor)

                # 燃料制約を満たさないなら進めない。
                if agent_fuel is not None and current_cost + move_cost > agent_fuel:
                    continue

                tentative_g = current_cost + move_cost

                # より短い経路が見つかれば更新する。
                if tentative_g < g_score.get(neighbor, float('inf')):
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    heapq.heappush(
                        open_heap,
                        (tentative_g + heuristic(neighbor, goal), tentative_g, neighbor),
                    )

        # 目標に到達できなかった場合は空配列を返す。
        if goal not in g_score:
            return []

        # 目標から親を辿って経路を復元する。
        path = [goal]
        while path[-1] != start:
            path.append(came_from[path[-1]])
        path.reverse()

        # 最終的な結果をリスト形式に整形して返す。
        self.path = [list(pos) for pos in path]
        return self.path
