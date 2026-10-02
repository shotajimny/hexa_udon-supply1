"""補給車用 Bias。

巡回車の採択済み path から補給候補地点を抽出する。
この段階では担当する補給車を決めない。
"""


class SupplyBias:
    def create_candidates(self, tour_assignments, tour_elapsed_steps=None):
        """巡回車 path から補給候補地点を作る。

        tour_elapsed_steps:
            {tourcar_id: その日すでに消費した step}。
            指定しない場合は 0 とする。
        """
        tour_elapsed_steps = tour_elapsed_steps or {}
        candidates = []

        for assignment in tour_assignments:
            path = assignment.get("path", [])
            if not path:
                continue

            tourcar_id = assignment["agent_id"]
            status = assignment.get("status")
            refuel_position = assignment.get("refuel_position")
            elapsed_before_path = float(tour_elapsed_steps.get(tourcar_id, 0.0))

            # fuel_shortage: start ～ refuel_position
            # reached_goal: path 全体
            for point_index, point in enumerate(path):
                path_step = float(point["step"])
                candidates.append({
                    "tourcar_id": tourcar_id,
                    "status": status,
                    "meeting_point": list(point["position"]),
                    "tour_path_step": path_step,
                    "tour_arrival_step": elapsed_before_path + path_step,
                    "remaining_fuel": float(point["remaining_fuel"]),
                    "path_index": point_index,
                })

                if (
                    status == "fuel_shortage"
                    and refuel_position is not None
                    and list(point["position"]) == list(refuel_position)
                ):
                    break

        return candidates
