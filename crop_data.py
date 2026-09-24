"""
crop_data.py
------------
Static reference data for Challenge 1.
"""

CROP_THRESHOLDS = {
    "Date Palm": {
        "temp_c": (20, 45),
        "rain_mm": (50, 400),
        "ph": (6.0, 8.5),
        "notes": "Thrives in hot, arid conditions with irrigation; tolerates saline and alkaline soils well.",
    },
    "Tomato": {
        "temp_c": (15, 32),
        "rain_mm": (400, 800),
        "ph": (5.8, 7.0),
        "notes": "Sensitive to frost and heat above ~35C; needs steady irrigation.",
    },
    "Cucumber": {
        "temp_c": (18, 32),
        "rain_mm": (400, 800),
        "ph": (5.5, 7.0),
        "notes": "High water demand; greenhouse/hydroponic setups work well in hot climates.",
    },
    "Wheat": {
        "temp_c": (10, 26),
        "rain_mm": (300, 900),
        "ph": (6.0, 7.5),
        "notes": "Cool-season crop; high heat during grain filling can reduce yield.",
    },
    "Barley": {
        "temp_c": (10, 28),
        "rain_mm": (250, 800),
        "ph": (6.0, 8.5),
        "notes": "More heat-, drought- and salt-tolerant than wheat.",
    },
    "Alfalfa": {
        "temp_c": (15, 32),
        "rain_mm": (500, 900),
        "ph": (6.5, 7.5),
        "notes": "Deep-rooted and drought-tolerant once established.",
    },
    "Potato": {
        "temp_c": (10, 25),
        "rain_mm": (500, 700),
        "ph": (4.8, 6.5),
        "notes": "Prefers cooler conditions and slightly acidic soil.",
    },
    "Corn (Maize)": {
        "temp_c": (18, 32),
        "rain_mm": (500, 800),
        "ph": (5.8, 7.0),
        "notes": "Needs steady water through tasseling and silking.",
    },
    "Bell Pepper": {
        "temp_c": (18, 30),
        "rain_mm": (600, 1200),
        "ph": (5.5, 6.8),
        "notes": "Sensitive to frost and prolonged heat.",
    },
    "Onion": {
        "temp_c": (13, 24),
        "rain_mm": (350, 550),
        "ph": (6.0, 7.0),
        "notes": "Bulbing depends on temperature and day length.",
    },
    "Lettuce": {
        "temp_c": (7, 24),
        "rain_mm": (300, 500),
        "ph": (6.0, 6.8),
        "notes": "Cool-season and heat-sensitive crop.",
    },
    "Watermelon": {
        "temp_c": (22, 35),
        "rain_mm": (400, 600),
        "ph": (6.0, 6.8),
        "notes": "Heat-loving crop that needs well-drained soil.",
    },
    "Eggplant": {
        "temp_c": (20, 32),
        "rain_mm": (600, 1000),
        "ph": (5.5, 6.8),
        "notes": "Heat tolerant but sensitive to cold conditions.",
    },
}


DISEASE_TREATMENTS = {
    "Healthy": "No signs of disease. Maintain proper watering, spacing, and regular monitoring.",

    "Early Blight": "Remove affected lower leaves, avoid overhead watering, and apply an appropriate fungicide if needed.",

    "Late Blight": "Remove infected plants promptly, improve airflow, and use a fungicide labelled for late blight.",

    "Leaf Mold": "Increase ventilation, reduce humidity, avoid wetting leaves, and remove affected leaves.",

    "Bacterial Spot": "Avoid overhead irrigation, remove infected material, disinfect tools, and consider a suitable copper-based treatment.",

    "Powdery Mildew": "Improve air circulation, avoid excess nitrogen, and use an appropriate mildew treatment.",

    "Target Spot": "Remove infected leaves, avoid overhead watering, and apply a labelled fungicide if required.",

    "Septoria Leaf Spot": "Remove infected leaves, prevent soil from splashing onto foliage, and use an appropriate fungicide.",

    "Tomato Mosaic Virus": "There is no direct cure. Remove infected plants, disinfect tools, and control insect vectors.",

    "Tomato Yellow Leaf Curl Virus": "Remove infected plants and control whiteflies, which are a major vector.",

    "Common Rust": "Use a labelled fungicide when appropriate, avoid overhead watering, and consider resistant varieties.",

    "Northern Leaf Blight": "Rotate crops, remove crop debris, and use a labelled fungicide when appropriate.",

    "Apple Scab": "Remove fallen leaves, improve airflow through pruning, and use an appropriate fungicide.",

    "Black Rot": "Remove infected wood and fruit, improve airflow, and use a labelled fungicide.",

    "Cedar Apple Rust": "Remove nearby cedar/juniper hosts where practical and use appropriate disease management.",
}


DEFAULT_TREATMENT = (
    "Specific guidance for this exact disease label is not available yet. "
    "General steps: remove severely affected leaves, avoid overhead watering, "
    "improve airflow, and consult local agricultural extension guidance."
)
