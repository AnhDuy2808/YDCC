import joblib
import numpy as np
from .raster import sample_raster

clf = joblib.load("models/flood_xgb_classifier.pkl")
reg = joblib.load("models/flood_xgb_regressor.pkl")

def predict_flood(lat, lon):
    VV = sample_raster("data/VV_dbscl_2022_9.tif", lat, lon)
    slope = sample_raster("data/slope_dbscl.tif", lat, lon)
    hand = sample_raster("data/hand_dbscl.tif", lat, lon)

    X = np.array([[VV, slope, hand]])

    flood_prob = clf.predict_proba(X)[0, 1]
    is_flood = flood_prob > 0.3

    depth = float(reg.predict(X)[0]) if is_flood else 0.0

    return {
        "flood": bool(is_flood),
        "probability": flood_prob,
        "depth_m": round(depth, 2)
    }
