import ee

# 1. INIT EARTH ENGINE
ee.Initialize(project="test-project-425219")

# 2. DEFINE ĐBSCL = 13 TỈNH (CÁCH ĐÚNG – KHÔNG DÙNG "Mekong Delta")
DBSCL = ee.FeatureCollection("FAO/GAUL/2015/level1") \
    .filter(ee.Filter.inList("ADM1_NAME", [
        "An Giang", "Ben Tre", "Bac Lieu", "Ca Mau",
        "Can Tho", "Dong Thap", "Hau Giang", "Kien Giang",
        "Long An", "Soc Trang", "Tien Giang",
        "Tra Vinh", "Vinh Long"
    ]))


# 3. HELPER: EMPTY IMAGE (CHUẨN EE, KHÔNG LỖI RENAME)
def empty_image():
    return ee.Image.constant(0).updateMask(ee.Image.constant(0))

def safe_mean(col):
    return ee.Image(
        ee.Algorithms.If(
            col.size().gt(0),
            col.mean(),
            empty_image()
        )   
    )

def safe_lt(image, threshold):
    return ee.Image(
        ee.Algorithms.If(
            image.bandNames().size().gt(0),
            image.lt(threshold),
            empty_image()
        )
    )

# 4. BUILD DATA FOR ONE MONTH
def build_month(year, month):
    start = ee.Date.fromYMD(year, month, 1)
    end = start.advance(1, "month")

    # Sentinel-1 collection
    s1_col = ee.ImageCollection("COPERNICUS/S1_GRD") \
        .filterBounds(DBSCL.geometry()) \
        .filterDate(start, end) \
        .filter(ee.Filter.eq("instrumentMode", "IW")) \
        .filter(ee.Filter.listContains("transmitterReceiverPolarisation", "VV")) \
        .select("VV")

    # DEBUG: xem có ảnh hay không
    print(f"Year {year} Month {month} → S1 images:",
          s1_col.size().getInfo())

    # Safe mean
    s1 = safe_mean(s1_col).rename("VV")

    # Flood mask
    flood = safe_lt(s1, -17).rename("flood")

    # DEM + slope
    dem = ee.Image("USGS/SRTMGL1_003").rename("elevation")
    slope = ee.Terrain.slope(dem).rename("slope")

    # Build feature image (chỉ khi có VV)
    features = ee.Image(
        ee.Algorithms.If(
            s1.bandNames().size().gt(0),
            s1.addBands([dem, slope, flood]),
            empty_image()
        )
    )

    samples = ee.FeatureCollection(
        ee.Algorithms.If(
            features.bandNames().size().gt(0),
            features.sample(
                region=DBSCL.geometry(),
                scale=30,
                numPixels=2000,  
                geometries=False
            ),
            ee.FeatureCollection([])
        )
    )

    # Add metadata
    return samples.map(lambda f: f.set({
        "year": year,
        "month": month
    }))

# 5. EXPORT PER YEAR (CHỈ EXPORT KHI CÓ DATA)
for year in range(2018, 2025):
    print(f"\n BUILDING DATASET FOR YEAR {year}")
    dataset = ee.FeatureCollection([])

    for month in range(1, 13):
        dataset = dataset.merge(build_month(year, month))

    total = dataset.size().getInfo()
    print(f"TOTAL SAMPLES {year}: {total}")

    if total == 0:
        print(f" Year {year}: NO DATA → SKIP EXPORT")
        continue

    task = ee.batch.Export.table.toDrive(
        collection=dataset,
        description=f"flood_dataset_dbscl_{year}",
        folder="EarthEngine",
        fileNamePrefix=f"flood_dataset_dbscl_{year}",
        fileFormat="CSV"
    )

    task.start()
    print(f" EXPORT STARTED: flood_dataset_dbscl_{year}.csv")
