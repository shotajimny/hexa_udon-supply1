from fastapi import FastAPI
from pydantic import BaseModel
from typing import List

app = FastAPI()

# データそれぞれの型を定義
class tour_vehicle(BaseModel): #巡回車のデータ構造
    id: int
    position: List[float]
    capacity: int

class supply_vehicle(BaseModel): #補給車のデータ構造
    id: int
    position: List[float]

class map_data(BaseModel): #マップデータの構造
    width: int
    height: int
    status: List[List[float]] #二次元配列でセルそれぞれの状態を表す

@app.post("/run")
def run_simulation(data: List[tour_vehicle]):
    return {
        "status": "ok",
        "received": data
    }