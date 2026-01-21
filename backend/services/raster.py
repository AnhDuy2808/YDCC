import rasterio

def sample_raster(path, lat, lon):
    with rasterio.open(path) as src:
        row, col = src.index(lon, lat)
        value = src.read(1)[row, col]
        return float(value)
