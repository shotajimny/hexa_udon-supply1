from tour_car.compare_tourcar import calculate_path_tourcar

def create_patrol_paths():
    # calculate_path_tourcarから巡回車のpathを取得する
    patrol_paths = calculate_path_tourcar()
    return patrol_paths     #pathを返す