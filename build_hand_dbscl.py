import ee
ee.Initialize(project="test-project-425219")

print("EE initialized")

# ===============================
# BUILD DBSCL REGION (CORRECT)
# ===============================
provinces = [
    "An Giang", "Bac Lieu", "Ben Tre", "Can Tho", "Ca Mau",
    "Dong Thap", "Hau Giang", "Kien Giang", "Long An",
    "Soc Trang", "Tien Giang", "Tra Vinh", "Vinh Long"
]

gaul = ee.FeatureCollection("FAO/GAUL/2015/level1")

dbscl = gaul.filter(ee.Filter.inList("ADM1_NAME", provinces))

# CHECK
count = dbscl.size().getInfo()
print("Number of DBSCL provinces:", count)
assert count > 0, "❌ DBSCL geometry is empty!"

region = dbscl.geometry()

# ===============================
# HAND (MERIT)
# ===============================
hand = (
    ee.Image("MERIT/Hydro/v1_0_1")
    .select("hnd")
    .rename("HAND")
    .clip(region)
)

print("HAND bands:", hand.bandNames().getInfo())

# ===============================
# EXPORT HAND
# ===============================
task = ee.batch.Export.image.toDrive(
    image=hand,
    description="HAND_DBSCL",
    folder="EarthEngine",
    fileNamePrefix="hand_dbscl",
    region=region,
    scale=90,
    maxPixels=1e13
)

task.start()
print("🚀 HAND_DBSCL export started")
