"""
crop_data.py
------------
Static reference data for Challenge 1 (land suitability + crop health).

CROP_THRESHOLDS: ballpark agronomic ranges (temperature, annual rainfall
equivalent, soil pH) used as a simple rule-based suitability filter.
These are starting estimates from general agronomic references, not a
live pull from FAO EcoCrop — if you have 20 spare minutes, look your
priority crops up on https://ecocrop.review.fao.org and tighten the
numbers. Accuracy here matters less than the app visibly reasoning
about real numbers.

DISEASE_TREATMENTS: maps the label strings produced by the Hugging Face
model (format "Plant___Disease", underscores for spaces) to a short,
practical treatment note. Add more keys as you see what the model
actually predicts on your test images -- run a few images through
first and copy the exact label strings back in here.
"""

# temp_c: (min, max) comfortable growing range, in Celsius
# rain_mm: (min, max) annual rainfall/irrigation-equivalent, in mm/year
# ph: (min, max) soil pH range
CROP_THRESHOLDS = {
    "Date Palm": {
        "temp_c": (20, 45),
        "rain_mm": (50, 400),
        "ph": (6.0, 8.5),
        "notes": "Thrives in hot, arid conditions with irrigation; "
                 "tolerates saline and alkaline soils well.",
    },
    "Tomato": {
        "temp_c": (15, 32),
        "rain_mm": (400, 800),
        "ph": (5.8, 7.0),
        "notes": "Sensitive to frost and to heat above ~35C during "
                 "flowering; needs steady irrigation, not waterlogging.",
    },
    "Cucumber": {
        "temp_c": (18, 32),
        "rain_mm": (400, 800),
        "ph": (5.5, 7.0),
        "notes": "High water demand; does well in greenhouse/hydroponic "
                 "setups in hot climates.",
    },
    "Wheat": {
        "temp_c": (10, 26),
        "rain_mm": (300, 900),
        "ph": (6.0, 7.5),
        "notes": "Cool-season crop; heat above ~30C during grain fill "
                 "cuts yield sharply.",
    },
    "Barley": {
        "temp_c": (10, 28),
        "rain_mm": (250, 800),
        "ph": (6.0, 8.5),
        "notes": "More heat-, drought- and salt-tolerant than wheat; a "
                 "reasonable fallback on marginal land.",
    },
    "Alfalfa": {
        "temp_c": (15, 32),
        "rain_mm": (500, 900),
        "ph": (6.5, 7.5),
        "notes": "Deep-rooted and drought-tolerant once established, "
                 "but sensitive to acidic or poorly-drained soil.",
    },
    "Potato": {
        "temp_c": (10, 25),
        "rain_mm": (500, 700),
        "ph": (4.8, 6.5),
        "notes": "Prefers cooler, slightly acidic soil; tubers rot in "
                 "waterlogged ground and yield drops sharply above 30C.",
    },
    "Corn (Maize)": {
        "temp_c": (18, 32),
        "rain_mm": (500, 800),
        "ph": (5.8, 7.0),
        "notes": "Needs steady water through tasseling/silking; "
                 "otherwise fairly heat-tolerant.",
    },
    "Bell Pepper": {
        "temp_c": (18, 30),
        "rain_mm": (600, 1200),
        "ph": (5.5, 6.8),
        "notes": "Sensitive to both frost and prolonged heat above "
                 "~32C, which drops fruit set.",
    },
    "Onion": {
        "temp_c": (13, 24),
        "rain_mm": (350, 550),
        "ph": (6.0, 7.0),
        "notes": "Bulbing is day-length sensitive as well as "
                 "temperature sensitive -- check variety fits your "
                 "latitude if you take this further.",
    },
    "Lettuce": {
        "temp_c": (7, 24),
        "rain_mm": (300, 500),
        "ph": (6.0, 6.8),
        "notes": "Cool-season and heat-sensitive -- bolts (goes to "
                 "seed, turns bitter) above ~27C. A greenhouse/shade "
                 "candidate in hot climates.",
    },
    "Watermelon": {
        "temp_c": (22, 35),
        "rain_mm": (400, 600),
        "ph": (6.0, 6.8),
        "notes": "Heat-loving with deep roots once established; needs "
                 "well-drained soil.",
    },
    "Eggplant": {
        "temp_c": (20, 32),
        "rain_mm": (600, 1000),
        "ph": (5.5, 6.8),
        "notes": "Similar heat tolerance to pepper; sensitive to cold "
                 "snaps below 15C.",
    },
}

# Simple, practical notes -- not a substitute for an agronomist. These
# cover common PlantVillage classes; extend as needed. Keys should match
# the model's raw label with underscores replaced by spaces,
