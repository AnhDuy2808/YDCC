import streamlit as st
import rasterio
import requests
import folium
from streamlit_folium import st_folium
from ai_analysis import analyze_flood_risk

# =====================================================
# CONFIG
# =====================================================
WEATHER_API_KEY = "edae6fa68eb75d19f5c822e8a1a7844f"

RASTER_PATH = r"D:\YDCC\backend\data\flood_depth_dbscl_2022_9_pred.tif"

DEFAULT_CENTER = [10.2, 105.8]  # Mekong Delta

# =====================================================
# SESSION STATE
# =====================================================
if "lat" not in st.session_state:
    st.session_state.lat = None
    st.session_state.lon = None
    st.session_state.depth = None
    st.session_state.weather = None

# =====================================================
# LOAD RASTER (1 LẦN)
# =====================================================
@st.cache_resource
def load_raster():
    src = rasterio.open(RASTER_PATH)
    arr = src.read(1)
    return src, arr

src, depth_arr = load_raster()

# =====================================================
# GEOCODING
# =====================================================
def geocode_address(address):
    url = "https://nominatim.openstreetmap.org/search"
    params = {"q": address, "format": "json", "limit": 1}
    headers = {"User-Agent": "FloodDemo"}
    r = requests.get(url, params=params, headers=headers, timeout=5)

    if r.status_code != 200:
        return None

    data = r.json()
    if not data:
        return None

    return float(data[0]["lat"]), float(data[0]["lon"])

# =====================================================
# WEATHER
# =====================================================
def get_weather(lat, lon):
    try:
        url = (
            "https://api.openweathermap.org/data/2.5/weather"
            f"?lat={lat}&lon={lon}&appid={WEATHER_API_KEY}&units=metric"
        )
        r = requests.get(url, timeout=5)
        if r.status_code != 200:
            return None

        data = r.json()
        return {
            "temp": data["main"]["temp"],
            "humidity": data["main"]["humidity"],
            "wind": data["wind"]["speed"],
            "desc": data["weather"][0]["description"]
        }
    except Exception:
        return None

# =====================================================
# PAGE UI
# =====================================================
st.set_page_config(layout="wide")
st.title("🌊 Flood Risk Prediction – Mekong Delta")

st.markdown("""
**Dữ liệu**: Sentinel-1 + DEM + HAND  
**Mô hình**: XGBoost Regression  
**Mục tiêu**: Dự đoán độ sâu ngập & tư vấn rủi ro theo vị trí
""")

# =====================================================
# INPUT ADDRESS
# =====================================================
col1, col2 = st.columns([3, 1])

with col1:
    address = st.text_input("📍 Nhập địa điểm (VD: Sa Đéc, Đồng Tháp)")

with col2:
    if st.button("🔍 Tìm địa điểm"):
        result = geocode_address(address)
        if result:
            st.session_state.lat, st.session_state.lon = result
        else:
            st.error("❌ Không tìm thấy địa điểm")

# =====================================================
# MAP (CENTER)
# =====================================================
map_center = (
    [st.session_state.lat, st.session_state.lon]
    if st.session_state.lat is not None
    else DEFAULT_CENTER
)

m = folium.Map(location=map_center, zoom_start=11)

if st.session_state.lat is not None:
    folium.Marker(
        [st.session_state.lat, st.session_state.lon],
        tooltip="Selected location",
        icon=folium.Icon(color="red")
    ).add_to(m)

map_data = st_folium(m, height=520, width=1000)

# =====================================================
# MAP CLICK
# =====================================================
if map_data and map_data.get("last_clicked"):
    st.session_state.lat = map_data["last_clicked"]["lat"]
    st.session_state.lon = map_data["last_clicked"]["lng"]

# =====================================================
# INFERENCE
# =====================================================
if st.session_state.lat is not None:

    lat, lon = st.session_state.lat, st.session_state.lon
    row, col = src.index(lon, lat)

    st.subheader("📍 Vị trí được chọn")
    st.write(f"Latitude: {lat:.5f}, Longitude: {lon:.5f}")

    if 0 <= row < depth_arr.shape[0] and 0 <= col < depth_arr.shape[1]:

        depth = float(depth_arr[row, col])
        weather = get_weather(lat, lon)

        # lưu state
        st.session_state.depth = depth
        st.session_state.weather = weather

        st.subheader("🌊 Độ sâu ngập dự đoán")
        st.metric("Flood depth (m)", f"{depth:.2f}")

        st.subheader("🌦 Thời tiết hiện tại")
        if weather:
            st.write(f"🌡 Nhiệt độ: {weather['temp']} °C")
            st.write(f"💧 Độ ẩm: {weather['humidity']} %")
            st.write(f"💨 Gió: {weather['wind']} m/s")
            st.write(f"☁️ Trạng thái: {weather['desc']}")
        else:
            st.info("Không lấy được dữ liệu thời tiết")

        st.subheader("🚦 Đánh giá rủi ro")
        if depth > 0.6:
            st.error("🚨 Ngập nặng – nên di dời người và tài sản")
        elif depth > 0.3:
            st.warning("⚠️ Ngập trung bình – hạn chế di chuyển")
        elif depth > 0.1:
            st.info("🌧 Ngập nhẹ – cần cẩn thận")
        else:
            st.success("✅ Không ngập")

    else:
        st.error("❌ Vị trí nằm ngoài vùng dữ liệu")

# =====================================================
# AI ANALYST
# =====================================================
if st.session_state.depth is not None:

    if st.button("🤖 AI phân tích nguyên nhân & khuyến nghị"):
        with st.spinner("AI đang phân tích..."):
            ai_text = analyze_flood_risk(
                flood_depth=st.session_state.depth,
                elevation=0.0,     # demo (có thể nối raster DEM sau)
                slope=0.0,         # demo
                hand=0.0,          # demo
                weather_desc=(
                    st.session_state.weather["desc"]
                    if st.session_state.weather else "unknown"
                )
            )

        st.markdown("### 🧠 Phân tích từ AI")
        st.write(ai_text)
