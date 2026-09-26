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

    # 補給車の現在位置
    supply_pos = self.pre_date.agents[supply_id].pos

    # 候補一覧
    candidates = []

    # 巡回車を1台ずつ評価
    for candidate in assignments:

        # 巡回車の情報
        tourcar_id = candidate["agent_id"]
        path = candidate["path"]
        status = candidate["status"]
        fuel_used = candidate["fuel_used"]
        steps = candidate["steps"]

        if status == "fuel_shortage":

            # refuel_positionのみ候補にする
            meeting_point = candidate["refuel_position"]

            distance = self.hex_distance(
                supply_pos,
                meeting_point
            )

            score = (
                distance * 0.4 +
                fuel_used * 0.3 +
                steps * 0.3
            )

            candidates.append({

                "supply_id": supply_id,
                "tourcar_id": tourcar_id,
                "meeting_point": meeting_point,
                "score": score

            })

        # reached_goalのとき
        else:

            # 経路を1マスずつ候補に追加
            for point in path:

                distance = self.hex_distance(
                    supply_pos,
                    point
                )

                score = (
                    distance * 0.4 +
                    fuel_used * 0.3 +
                    steps * 0.3
                )

                candidates.append({

                    "supply_id": supply_id,
                    "tourcar_id": tourcar_id,
                    "meeting_point": point,
                    "score": score

                })

    # 候補の並べ替え
    candidates.sort(
        key=lambda x: x["score"]
    )

    # 候補一覧を返す
    return candidates


# 補給車同士の競合を解決する関数
def resolve_conflict(self, all_candidates):

    # 補給車ごとの最終候補
    final_result = [
        [] for _ in range(len(all_candidates))
    ]

    # 各補給車が現在見ている候補番号
    index = [0] * len(all_candidates)

    # 各補給車が5件集まるまで繰り返す
    while True:

        # 全補給車が5件なら終了
        if all(
            len(result) >= 5
            for result in final_result
        ):
            break

        # すでに採用された補給地点
        used = set()

        # 採用済み候補を登録
        for result in final_result:

            for data in result:

                used.add((
                    data["tourcar_id"],
                    data["meeting_point"]
                ))

        progress = False

        # 補給車を1台ずつ処理
        for supply_id in range(len(all_candidates)):

            # 5件集まっていれば飛ばす
            if len(final_result[supply_id]) >= 5:
                continue

            # 候補を順番に探索
            while index[supply_id] < len(all_candidates[supply_id]):

                candidate = all_candidates[supply_id][index[supply_id]]

                key = (
                    candidate["tourcar_id"],
                    candidate["meeting_point"]
                )

                # 競合しなければ採用
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

                # 競合したら次候補へ
                else:

                    index[supply_id] += 1

        # 候補が尽きたら終了
        if progress is False:
            break

    # 補給車ごとの5候補を返す
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

        # 候補を作成
        candidates = self.select_supply_targets(
            assignments
        )

        all_candidates.append(candidates)

    # 競合解決後の5候補を返す
    return self.resolve_conflict(all_candidates)