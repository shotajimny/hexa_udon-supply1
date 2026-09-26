# A*アルゴリズムを実装するためのモジュール
# このファイルでは、六角格子上を移動するエージェントの経路探索を行う。
# 各セルは3次元座標 (x, y, z) で表し、六方向への移動を考慮する。
import heapq
from math import isfinite

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

# 燃料消費に対する重みを定義する。これにより、燃料消費が多い経路はコストが高く評価される。
FUEL_WEIGHT = 0.8  # 燃料消費の重み


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
        self.cells_by_position = {}
        self.cells_by_id = {}
        self.path = []

    def map_input(self, cells):
        """変換済みセルを、座標とAPIのセル番号で検索できる形にする。

        ``cells`` には ``converted_map.cells`` を渡す。互換性のため
        ``CellConverter`` 自体が渡された場合も、その ``cells`` 属性を使う。
        ``spots`` は経路探索では使用しないが、既存の呼び出しを壊さないため
        任意引数として受け取る。
        """
        if hasattr(cells, "cells"):
            cells = cells.cells

        self.cells_by_position = {
            tuple(cell.position): cell
            for cell in cells
        }
        self.cells_by_id = {
            index + 1: cell
            for index, cell in enumerate(cells)
        }

    def _resolve_position(self, position_or_id):
        """セル番号または3軸座標を、3軸座標のタプルへ正規化する。"""
        if isinstance(position_or_id, int):
            cell = self.cells_by_id.get(position_or_id)
            return tuple(cell.position) if cell else None
        return tuple(position_or_id)

    def _get_cell(self, position):
        return self.cells_by_position.get(tuple(position))

    def _is_walkable(self, position):
        cell = self._get_cell(position)
        if cell is None:
            return False

        # 地形と状態の両方を確認する。道路の state=0/1/2 は
        # 通行可能であり、step_cost に混雑コストが反映されている。
        if cell.terrain_type == "lake":
            return False

        if cell.state in [None, "", "blocked", "wall"]:
            return False

        return isfinite(cell.step_cost) and isfinite(cell.fuel_cost)

    def compute_cost(self, position):
        """指定座標の CellData から移動・燃料コストを返す。"""
        cell = self._get_cell(position)
        if cell is None:
            return float("inf"), float("inf")
        return float(cell.step_cost), float(cell.fuel_cost)


    def _calculate_path_info(self, path, current_agent):
        """経路上の各セルに到達した時点での残燃料量と経過ステップ数を計算する。"""
        
        # 経路上の各セルに到達した時点での残燃料量と経過ステップ数を計算する。
        # (elapsed_steps は引数として受け取るよう後々変更する)
        path_info = []

        # 現在の残燃料量と経過ステップ数を初期化する。
        # (経過ステップはその日複数回目の経路探索に対応させるため、後々引数から参照するように変更する)
        remaining_fuel = float(current_agent["fuel"])
        elapsed_steps = 0.0

        for index, position in enumerate(path):
            current = tuple(position)

            exhausted = False

            # 現在セル到着時の情報
            path_info.append({
                "position": list(current),
                "remaining_fuel": remaining_fuel,
                "step": elapsed_steps,
                "exhausted": exhausted
            })

            # goalなら終了
            if index == len(path) - 1:
                break

            # 移動先セルのコストを消費する。
            next_position = path[index + 1]
            step_cost, fuel_cost = self.compute_cost(next_position)

            # 残燃料が足りず次のセルへ移動できない場合は、exhausted を True にする。
            if remaining_fuel < fuel_cost:
                path_info[-1]["exhausted"] = True

            # 移動コストを消費
            remaining_fuel -= fuel_cost
            elapsed_steps += step_cost

        return path_info


    def search_astar(self, current_agent, goal_position):
        # A*探索のメイン処理。
        # current_agent: 現在の巡回車の情報を含む辞書
        # goal_position: 目標位置
        # agent_fuel: 現在の燃料量
        # 戻り値: [ [x, y, z], ... ] の経路座標リスト
        start = self._resolve_position(current_agent["position"])
        goal = self._resolve_position(goal_position)

        # 各探索結果を初期化する。
        self.open_set = []
        self.closed_set = []
        self.path = []

        # 開始地点または目標地点が通行不能なら探索しない。
        if start is None or goal is None:
            return {
                "path": [], 
                "status": "unreachable"
            }

        if not self._is_walkable(start) or not self._is_walkable(goal):
            return {
                "path": [],
                "status": "unreachable"
            }

        # 同じ地点ならそのまま終了とみなす。
        if start == goal:
            return {
                "path": [{
                    "position": list(start),
                    "remaining_fuel": float(current_agent["fuel"]),
                    "step": 0.0,
                    "exhausted": False
                }],
                "status": "reached_goal"
            }

        # heapq は優先度付きキューで、f = g + h が最小のノードを取り出す。
        open_heap = []
        heapq.heappush(open_heap, (heuristic(start, goal), 0.0, start))
        came_from = {}
        # 座標ごとに、開始地点からの総合コストの最小値を保持する。
        g_score = {start: 0.0}

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

                # 移動先セルの CellData を直接参照してコストを計算する。
                neighbor_cell = self._get_cell(neighbor)
                step_cost = neighbor_cell.step_cost
                fuel_cost = neighbor_cell.fuel_cost

                # 移動時間と燃料消費を合算し、補給車の負担も経路評価に加える。
                tentative_g = current_cost + step_cost + fuel_cost * FUEL_WEIGHT

                # より短い経路が見つかれば更新する。
                if tentative_g < g_score.get(neighbor, float('inf')):
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    heapq.heappush(
                        open_heap,
                        (
                            tentative_g + heuristic(neighbor, goal),
                            tentative_g,
                            neighbor,
                        ),
                    )

        # 目標に到達できなかった場合は空配列を返す。
        if goal not in g_score:
            return {
                "path": [],
                "status": "unreachable"
            }

        # 目標から親を辿って経路を復元する。
        path = [goal]
        while path[-1] != start:
            path.append(came_from[path[-1]])
        path.reverse()

        # 最終的な結果をリスト形式に整形して返す。
        self.path = [list(pos) for pos in path]

        path_info = self._calculate_path_info(
            self.path,
            current_agent
        )
        
        # compare側が扱い易いようにキーを追加
        if not path_info:
          status = "unreachable"
        elif path_info[-1]["exhausted"]:
          status = "fuel_shortage"
        else:
          status = "reached_goal"

        return {
            "path": path_info,
            "status": status
        }
