import ee
ee.Initialize(project="test-project-425219")

print("EE initialized")

# ===============================
# DBSCL REGION
# ===============================
provinces = [
    "An Giang", "Bac Lieu", "Ben Tre", "Can Tho", "Ca Mau",
    "Dong Thap", "Hau Giang", "Kien Giang", "Long An",
    "Soc Trang", "Tien Giang", "Tra Vinh", "Vinh Long"
]

dbscl = (
    ee.FeatureCollection("FAO/GAUL/2015/level1")
    .filter(ee.Filter.inList("ADM1_NAME", provinces))
)

region = dbscl.geometry()

# ===============================
# LOAD HAND
# ===============================
hand = ee.Image("MERIT/Hydro/v1_0_1").select("hnd").rename("HAND")

# ===============================
# FUNCTION BUILD DEPTH
# ===============================
def build_flood_depth(year, month):
    start = ee.Date.fromYMD(year, month, 1)
    end = start.advance(1, "month")

    s1 = (
        ee.ImageCollection("COPERNICUS/S1_GRD")
        .filterBounds(region)
        .filterDate(start, end)
        .filter(ee.Filter.eq("instrumentMode", "IW"))
        .filter(ee.Filter.listContains("transmitterReceiverPolarisation", "VV"))
        .select("VV")
    )

    count = s1.size()
    print(f"{year}-{month:02d} | S1 images:", count.getInfo())

    # nếu không có ảnh → skip
    s1_mean = ee.Image(
        ee.Algorithms.If(count.gt(0), s1.mean(), ee.Image.constant(-999))
    )

    flood = s1_mean.lt(-17).rename("flood")

    # HAND tại vùng flood
    hand_flood = hand.updateMask(flood)

    water_level = hand_flood.reduceRegion(
        reducer=ee.Reducer.percentile([95]),
        geometry=region,
        scale=90,
        maxPixels=1e13
    ).get("HAND")

    water_level = ee.Number(water_level)

    flood_depth = (
        ee.Image.constant(water_level)
        .subtract(hand)
        .max(0)
        .rename("flood_depth")
        .clip(region)
    )

    return flood_depth.set({
        "year": year,
        "month": month
    })

# ===============================
# EXPORT 1 NĂM (TEST TRƯỚC)
# ===============================
year = 2022
month = 9   # mùa lũ rõ

depth = build_flood_depth(year, month)

task = ee.batch.Export.image.toDrive(
    image=depth,
    description=f"FloodDepth_DBSCL_{year}_{month}",
    folder="EarthEngine",
    fileNamePrefix=f"flood_depth_dbscl_{year}_{month}",
    region=region,
    scale=90,
    maxPixels=1e13
)

task.start()
print("🚀 Flood depth export started")
