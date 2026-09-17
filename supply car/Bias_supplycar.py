def select_supply_targets(self, all_paths):
    # 1. 補給車の情報を取得
    supply_id = self.agent_id
    supply_pos = self.pre_date.agents[supply_id].pos

    # 2. 評価結果を管理
    candidates = []

    # 3. 巡回車を1台ずつ取り出して評価
    for candidate in all_paths:
        tourcar_id = candidate["agent_id"]
        path = candidate["path"]

        fuel = self.pre_date.agents[tourcar_id].fuel

        best_distance = float("inf")
        meeting_point = None

        # 4. 巡回車の経路上で、補給車に最も近い地点を探す
        for point in path:
            distance = self.hex_distance(supply_pos, point)

            if distance < best_distance:
                best_distance = distance
                meeting_point = point

        # 5. 距離と燃料から評価値を計算
        score = best_distance * 0.4 + fuel * 0.6

        candidates.append({
            "supply_id": supply_id,
            "tourcar_id": tourcar_id,
            "meeting_point": meeting_point,
            "score": score,
        })

    # 6. 評価値の低い順にソート
    sorted_targets = sorted(candidates, key=lambda x: x["score"])

    # 7. 上位5件を返す
    assignments = []

    for target in sorted_targets[:5]:
        assignments.append({
            "supply_id": target["supply_id"],
            "tourcar_id": target["tourcar_id"],
            "meeting_point": target["meeting_point"],
        })

    return assignments