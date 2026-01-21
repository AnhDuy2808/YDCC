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
# STATIC DATA
# ===============================
dem = ee.Image("USGS/SRTMGL1_003").rename("elevation")
slope = ee.Terrain.slope(dem).rename("slope")
hand = ee.Image("MERIT/Hydro/v1_0_1").select("hnd").rename("HAND")

# ===============================
# BUILD ONE MONTH
# ===============================
def build_month(year, month):
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

    # Nếu không có ảnh → bỏ
    def empty():
        return ee.FeatureCollection([])

    def non_empty():
        vv = s1.mean().rename("VV")
        flood = vv.lt(-17)

        # flood depth (tính giống B3)
        hand_flood = hand.updateMask(flood)

        water_level = ee.Number(
            hand_flood.reduceRegion(
                reducer=ee.Reducer.percentile([95]),
                geometry=region,
                scale=90,
                maxPixels=1e13
            ).get("HAND")
        )

        flood_depth = (
            ee.Image.constant(water_level)
            .subtract(hand)
            .max(0)
            .rename("flood_depth")
        )

        img = vv.addBands([dem, slope, hand, flood_depth])

        samples = img.sample(
            region=region,
            scale=90,
            numPixels=5000,
            geometries=False
        )

        # Chỉ giữ pixel flood (depth > 0)
        samples = samples.filter(ee.Filter.gt("flood_depth", 0))

        return samples.map(lambda f: f.set({
            "year": year,
            "month": month
        }))

    return ee.FeatureCollection(
        ee.Algorithms.If(count.gt(0), non_empty(), empty())
    )

# ===============================
# EXPORT PER YEAR
# ===============================
for year in range(2018, 2025):
    print(f"\n🚀 Building regression dataset for {year}")
    dataset = ee.FeatureCollection([])

    for month in range(1, 13):
        dataset = dataset.merge(build_month(year, month))

    task = ee.batch.Export.table.toDrive(
        collection=dataset,
        description=f"FloodRegression_DBSCL_{year}",
        folder="EarthEngine",
        fileNamePrefix=f"flood_regression_dbscl_{year}",
        fileFormat="CSV"
    )

    task.start()
    print(f"✅ Export started: flood_regression_dbscl_{year}.csv")
