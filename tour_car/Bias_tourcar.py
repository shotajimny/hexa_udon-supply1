import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from transmit.export import export_result


class prediction_spots:
    def __init__ (self, id, position, capacity):
        #巡回車のID、位置、タンク容量を初期化
        self.id = id
        self.position = position
        self.capacity = capacity

    def distance_measurement(self, spot_data):
        
        self.distance = [0.0, 0.0] #測定結果を格納するリスト

        for i in range(len(spot_data)): #仮のループでスポットデータを処理  
            self.distance[i] = spot_data[i] - self.position[i] #仮の測定結果
        
        return self.distance #測定結果を返す
    

tour_car = [] #巡回車のリストを作成
tour_car.append(prediction_spots(1, [0.0, 0.0], 100)) #巡回車のインスタンスを作成

#例として、スポットデータを与えて距離測定を行う
spot_data = [] #スポットデータのリストを作成
spot_data.append([5.0, 5.0]) #仮のスポットデータ

#測定結果を取得
measurement_result = tour_car[0].distance_measurement(spot_data[0]) #インスタンス.メソッド(引数)の形で呼び出す

export_result(measurement_result) # 測定結果をJSON形式で出力する