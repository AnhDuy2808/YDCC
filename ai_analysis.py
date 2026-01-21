"""
OFFLINE AI FLOOD ANALYST
Rule-based + domain knowledge
Ổn định 100% cho hackathon demo
"""

def analyze_flood_risk(
    flood_depth,
    elevation=0.0,
    slope=0.0,
    hand=0.0,
    weather_desc="unknown"
):
    depth = float(flood_depth)

    # =============================
    # RISK LEVEL
    # =============================
    if depth > 0.6:
        risk = "CAO"
    elif depth > 0.3:
        risk = "TRUNG BÌNH"
    elif depth > 0.1:
        risk = "THẤP"
    else:
        risk = "KHÔNG NGẬP"

    # =============================
    # ANALYSIS
    # =============================
    reasons = []

    if depth > 0.3:
        reasons.append("khu vực có địa hình thấp, dễ tích nước")

    if hand < 1.0:
        reasons.append("khả năng thoát nước kém do gần sông/kênh rạch")

    if weather_desc and "mưa" in weather_desc.lower():
        reasons.append("ảnh hưởng bởi mưa trong thời gian gần đây")

    if not reasons:
        reasons.append("điều kiện địa hình và thủy văn tương đối ổn định")

    # =============================
    # ADVICE
    # =============================
    if depth > 0.6:
        advice = (
            "Người dân nên hạn chế ra ngoài, di dời tài sản lên cao, "
            "chuẩn bị phương án sơ tán nếu mưa tiếp tục kéo dài."
        )
    elif depth > 0.3:
        advice = (
            "Cần hạn chế di chuyển bằng xe máy, theo dõi tình hình thời tiết "
            "và cảnh báo từ chính quyền địa phương."
        )
    elif depth > 0.1:
        advice = (
            "Ngập nhẹ, người dân cần cẩn thận khi đi lại, đặc biệt vào ban đêm."
        )
    else:
        advice = (
            "Hiện tại khu vực không có nguy cơ ngập đáng kể, "
            "sinh hoạt có thể diễn ra bình thường."
        )

    # =============================
    # FINAL TEXT
    # =============================
    return f"""
🔎 **Đánh giá rủi ro ngập:** {risk}

📌 **Nguyên nhân chính:**
- {", ".join(reasons)}

🧭 **Khuyến nghị:**
{advice}
""".strip()
