import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# 巡回車から見たスポットの距離を測定するためのクラスを定義する
class prediction_spots:
    def __init__(self, id, position):
        self.id = id #巡回車のIDを格納する変数
        self.position = position #巡回車の位置情報を格納する変数
        self.distances = [] #距離測定結果を格納するリスト


    #距離測定により選択肢となるスポットを選ぶメソッドを定義
    def distance_measurement(self, spot_data, pre_filter_count): 

        #測定結果を格納するリスト
        self.distance = [] #距離測定結果の差分を格納するリストの初期化
        self.distances = [] #距離測定結果の順位を格納するリストの初期化

        #距離測定結果の差分を格納する二次元リスト
        self.distance = [
            [0.0] * len(self.position)
            for _ in range(len(spot_data))
        ] 

        for i in range(len(spot_data)): #仮のループでスポットデータを処理  
            for j in range(len(self.position)): #仮のループで位置データを処理
                self.distance[i][j] = spot_data[i][j] - self.position[j] #測定
                    
        #測定結果を距離の絶対値の合計でソートして、上位pre_filter_count件を選択する処理を追加する
        for i in range(len(self.distance)):
            total_distance = sum(abs(d) for d in self.distance[i])
            self.distances.append((total_distance, i, self.distance[i]))
        self.distances.sort()
        selected_results = self.distances[:pre_filter_count]
        self.distance = [(i, distance) for _, i, distance in selected_results]

        return self.distance #測定結果を返す

    
    # tourcarの位置更新
    def update_position(self, new_position):
        self.position = new_position

# 各tourcar ごとに候補スポットを選別して返す関数を定義する
def select_spots(tour_cars, spot_datas, pre_filter_count):
    """各tourcar ごとに候補スポットを選別して返す"""
    results = []

    # 各tourcar ごとにdistance_measurementを呼び出し、上位pre_filter_count件のスポットを選択する
    for tour in tour_cars:
        tour_results = []

        measurement = tour.distance_measurement(
            spot_datas,
            pre_filter_count
        )

        for spot_number, distance in measurement:
            tour_results.append({
                "tourcar_id": tour.id,
                "spot_number": spot_number,
                "distance": distance
            })

        results.append(tour_results)

    return results

    