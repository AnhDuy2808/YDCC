import ee
ee.Initialize(project="test-project-425219")


# ĐBSCL REGION 
region = ee.Geometry.Rectangle([104.5, 8.5, 106.8, 11.5])

# # 1️ DEM
# dem = ee.Image("USGS/SRTMGL1_003").clip(region)

# ee.batch.Export.image.toDrive(
#     image=dem,
#     description="dem_dbscl",
#     folder="EarthEngine",
#     fileNamePrefix="dem_dbscl",
#     region=region,
#     scale=30,
#     maxPixels=1e13
# ).start()

# print(" Export DEM")

# # 2️ SLOPE
# slope = ee.Terrain.slope(dem)

# ee.batch.Export.image.toDrive(
#     image=slope,
#     description="slope_dbscl",
#     folder="EarthEngine",
#     fileNamePrefix="slope_dbscl",
#     region=region,
#     scale=30,
#     maxPixels=1e13
# ).start()

# print(" Export slope")

# 3️ VV – Sep 2022
vv = (
    ee.ImageCollection("COPERNICUS/S1_GRD")
    .filterBounds(region)
    .filterDate("2022-09-01", "2022-10-01")
    .filter(ee.Filter.eq("instrumentMode", "IW"))
    .filter(ee.Filter.listContains("transmitterReceiverPolarisation", "VV"))
    .select("VV")
    .mean()
    # ⬇️ Resample trước khi export
    .resample("bilinear")
    .reproject(
        crs="EPSG:4326",
        scale=30      # ⬅️ 30 m: chuẩn ML, KHÔNG tile
    )
    .clip(region)
)

ee.batch.Export.image.toDrive(
    image=vv,
    description="VV_dbscl_2022_9",
    folder="EarthEngine",
    fileNamePrefix="VV_dbscl_2022_9",
    region=region,
    scale=30,
    maxPixels=1e13,
    fileFormat="GeoTIFF"
).start()

print("🚀 Export VV Sep 2022 @30m")
