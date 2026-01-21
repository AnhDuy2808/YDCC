import rasterio

with rasterio.open(r"D:\YDCC\backend\data\flood_depth_dbscl_2022_9.tif") as src:
    data = src.read(1)
    print(src.crs, src.transform)