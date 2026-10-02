"""補給車用A*。

巡回車用 compute_astar.py と同じ六角座標・通行判定を使う。
補給車は燃料を消費しないため step_cost のみを経路コストに使う。
移動 A -> B のコストは、仕様どおり現在地 A の step_cost を参照する。
"""

import heapq
from math import isfinite


DIRECTIONS = [
    [0, 1, -1],   # 0: 左上
    [1, 0, -1],   # 1: 右上
    [1, -1, 0],   # 2: 右
    [0, -1, 1],   # 3: 右下
    [-1, 0, 1],   # 4: 左下
    [-1, 1, 0],   # 5: 左
]


def heuristic(position, goal_position):
    dx = abs(position[0] - goal_position[0])
    dy = abs(position[1] - goal_position[1])
    dz = abs(position[2] - goal_position[2])
    return max(dx, dy, dz)


class SupplyAstarAlgorithm:
    def __init__(self):
        self.cells_by_position = {}
        self.cells_by_id = {}

    def map_input(self, cells):
        if hasattr(cells, "cells"):
            cells = cells.cells

        self.cells_by_position = {
            tuple(cell.position): cell
            for cell in cells
        }
        self.cells_by_id = {
            index: cell
            for index, cell in enumerate(cells)
        }

    def _resolve_position(self, position_or_id):
        if isinstance(position_or_id, int):
            cell = self.cells_by_id.get(position_or_id)
            return tuple(cell.position) if cell else None
        if position_or_id is None:
            return None
        return tuple(position_or_id)

    def _get_cell(self, position):
        return self.cells_by_position.get(tuple(position))

    def _is_walkable(self, position):
        cell = self._get_cell(position)
        if cell is None:
            return False
        if cell.terrain_type == "lake":
            return False
        if cell.state in [None, "", "blocked", "wall"]:
            return False
        return isfinite(float(cell.step_cost))

    def search_astar(self, start_position, goal_position):
        start = self._resolve_position(start_position)
        goal = self._resolve_position(goal_position)

        if start is None or goal is None:
            return {"path": [], "status": "unreachable", "steps": float("inf")}
        if not self._is_walkable(start) or not self._is_walkable(goal):
            return {"path": [], "status": "unreachable", "steps": float("inf")}
        if start == goal:
            return {
                "path": [{"position": list(start), "step": 0.0}],
                "status": "reached_goal",
                "steps": 0.0,
            }

        open_heap = []
        heapq.heappush(open_heap, (heuristic(start, goal), 0.0, start))
        came_from = {}
        g_score = {start: 0.0}

        while open_heap:
            _, current_cost, current = heapq.heappop(open_heap)

            if current_cost > g_score.get(current, float("inf")):
                continue
            if current == goal:
                break

            current_cell = self._get_cell(current)
            # A -> B の移動では A の step_cost を使う。
            move_step_cost = float(current_cell.step_cost)

            for direction in DIRECTIONS:
                neighbor = (
                    current[0] + direction[0],
                    current[1] + direction[1],
                    current[2] + direction[2],
                )

                if not self._is_walkable(neighbor):
                    continue

                tentative_g = current_cost + move_step_cost
                if tentative_g < g_score.get(neighbor, float("inf")):
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

        if goal not in g_score:
            return {"path": [], "status": "unreachable", "steps": float("inf")}

        positions = [goal]
        while positions[-1] != start:
            positions.append(came_from[positions[-1]])
        positions.reverse()

        path = []
        elapsed_steps = 0.0
        for index, position in enumerate(positions):
            path.append({"position": list(position), "step": elapsed_steps})
            if index < len(positions) - 1:
                elapsed_steps += float(self._get_cell(position).step_cost)

        return {
            "path": path,
            "status": "reached_goal",
            "steps": elapsed_steps,
        }
