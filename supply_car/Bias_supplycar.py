# pos → (x, y, z)
def pos_to_cube(self, pos):

    width = self.pre_map.width

    x = pos % width
    z = pos // width
    y = -x - z

    return (x, y, z)


# 六角形マップ(x, y, z)の直線距離
def hex_distance(self, a, b):

    # 座標を x・y・z に分解
    x1, y1, z1 = a
    x2, y2, z2 = b

    # 六角形マスの最短距離を返す
    return (
        abs(x1 - x2)
        + abs(y1 - y2)
        + abs(z1 - z2)
    ) // 2


# 補給車1台の候補を作成
def select_supply_targets(self, assignments):

    # 補給車ID
    supply_id = self.agent_id

    # 補給車の現在位置（cube座標）
    supply_pos = self.pos_to_cube(
        self.pre_date.agents[supply_id].pos
    )

    # 候補一覧
    candidates = []

    # 巡回車を1台ずつ評価
    for candidate in assignments:

        # 巡回車の情報
        tourcar_id = candidate["agent_id"]
        path = candidate["path"]
        status = candidate["status"]
        fuel_used = candidate["fuel_used"]

        # 巡回車の現在燃料
        current_fuel = self.pre_date.agents[tourcar_id].fuel

        # spot到達時の残燃料
        remaining_fuel = current_fuel - fuel_used

        # 燃料切れの場合
        if status == "fuel_shortage":

            meeting_point = candidate["refuel_position"]

            distance = self.hex_distance(
                supply_pos,
                meeting_point
            )

            score = (
                distance * 0.4 +
                remaining_fuel * 0.6
            )

            candidates.append({

                "supply_id": supply_id,
                "tourcar_id": tourcar_id,
                "meeting_point": meeting_point,
                "score": score

            })

        # 到達可能の場合
        else:

            for point in path:

                distance = self.hex_distance(
                    supply_pos,
                    point
                )

                score = (
                    distance * 0.4 +
                    remaining_fuel * 0.6
                )

                candidates.append({

                    "supply_id": supply_id,
                    "tourcar_id": tourcar_id,
                    "meeting_point": point,
                    "score": score

                })

    # scoreの小さい順に並べ替え
    candidates.sort(
        key=lambda x: x["score"]
    )

    return candidates


# 補給車同士の競合を解決する関数
def resolve_conflict(self, all_candidates):

    # 補給車ごとの最終候補
    final_result = [
        [] for _ in range(len(all_candidates))
    ]

    # 各補給車が見ている候補番号
    index = [0] * len(all_candidates)

    while True:

        # 全補給車が5件なら終了
        if all(
            len(result) >= 5
            for result in final_result
        ):
            break

        # 採用済みの補給地点
        used = set()

        for result in final_result:
            for data in result:
                used.add((
                    data["tourcar_id"],
                    data["meeting_point"]
                ))

        progress = False

        # 補給車を1台ずつ処理
        for supply_id in range(len(all_candidates)):

            if len(final_result[supply_id]) >= 5:
                continue

            while index[supply_id] < len(all_candidates[supply_id]):

                candidate = all_candidates[supply_id][index[supply_id]]

                key = (
                    candidate["tourcar_id"],
                    candidate["meeting_point"]
                )

                # 重複しなければ採用
                if key not in used:

                    final_result[supply_id].append({

                        "supply_id": candidate["supply_id"],
                        "tourcar_id": candidate["tourcar_id"],
                        "meeting_point": candidate["meeting_point"]

                    })

                    used.add(key)

                    index[supply_id] += 1
                    progress = True
                    break

                # 重複したら次候補
                else:
                    index[supply_id] += 1

        # これ以上追加できなければ終了
        if not progress:
            break

    return final_result


# Biasの実行関数
def create_supply_candidates(self, assignments):

    # 全補給車の候補
    all_candidates = []

    # 補給車を1台ずつ処理
    for agent in self.pre_date.agents:

        # 巡回車は飛ばす
        if agent.kind != 1:
            continue

        # この補給車を対象にする
        self.agent_id = agent.id

        # 候補作成
        candidates = self.select_supply_targets(
            assignments
        )

        all_candidates.append(candidates)

    # 競合解決後の候補を返す
    return self.resolve_conflict(all_candidates)