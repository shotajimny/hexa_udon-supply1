from tour_car.compare_tourcar import calculate_tourcar

# data はサーバーから受け取ったゲームデータ
tourcar = calculate_tourcar(data)

path = tourcar.calculate_path_tourcar(3)

print(path)
print(type(path))
print(type(path[0]))
print(path[0])