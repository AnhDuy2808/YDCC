from fastapi import FastAPI
from pydantic import BaseModel
import rasterio
from rasterio.transform import rowcol
import numpy as np
import requests


WEATHER_API_KEY = "edae6fa68eb75d19f5c822e8a1a7844f"

def get_weather(lat, lon):
    url = (
        "https://api.openweathermap.org/data/2.5/weather"
        f"?lat={lat}&lon={lon}&appid={WEATHER_API_KEY}&units=metric"
    )
    r = requests.get(url)
    if r.status_code != 200:
        return None

    data = r.json()
    return {
        "temperature": data["main"]["temp"],
        "humidity": data["main"]["humidity"],
        "wind_speed": data["wind"]["speed"],
        "weather": data["weather"][0]["description"]
    }



# LOAD DATA (1 LẦN)

RASTER_PATH = r"D:\YDCC\backend\data\flood_depth_dbscl_2022_9_pred.tif"

src = rasterio.open(RASTER_PATH)
depth_arr = src.read(1)
transform = src.transform
nodata = src.nodata

print("Raster loaded:", depth_arr.shape)

# FASTAPI

app = FastAPI(title="Flood Depth API – DBSCL")

class Query(BaseModel):
    lat: float
    lon: float

# HELPER

def advice_from_depth(d):
    if d <= 0.05:
        return "Không ngập – sinh hoạt bình thường"
    elif d <= 0.3:
        return "Ngập nhẹ – cẩn thận khi đi bộ"
    elif d <= 0.6:
        return "Ngập trung bình – tránh xe máy"
    else:
        return "Ngập nặng – nên di dời người và tài sản"

# API ENDPOINT

@app.post("/query")
def query_flood(q: Query):

    row, col = rowcol(transform, q.lon, q.lat)

    if row < 0 or col < 0 or row >= depth_arr.shape[0] or col >= depth_arr.shape[1]:
        return {"error": "Point outside raster"}

    depth = depth_arr[row, col]
    weather = get_weather(q.lat, q.lon)

    return {
        "location": {"lat": q.lat, "lon": q.lon},
        "flood_depth_m": round(float(depth), 2),
        "flooded": depth > 0.05,
        "weather": weather,
        "advice": advice_from_depth(depth)
    }
