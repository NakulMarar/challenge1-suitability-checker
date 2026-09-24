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
}

# Simple, practical notes -- not a substitute for an agronomist. These
# cover common PlantVillage classes; extend as needed. Keys should match
# the model's raw label with underscores replaced by spaces, and the
# plant name stripped off, at lookup time (see disease_model.py).
DISEASE_TREATMENTS = {
    "Healthy": "No signs of disease. Keep up current watering and "
               "spacing; recheck every 1-2 weeks.",
    "Early Blight": "Remove and destroy affected lower leaves, avoid "
                     "overhead watering, apply a copper-based fungicide, "
                     "and rotate crops next season.",
    "Late Blight": "Remove infected plants promptly to stop spread, "
                    "improve airflow between plants, and apply a "
                    "fungicide labelled for late blight.",
    "Leaf Mold": "Increase ventilation and reduce humidity around the "
                  "canopy, avoid wetting leaves when watering, remove "
                  "affected leaves.",
    "Bacterial Spot": "Avoid overhead irrigation, remove infected "
                       "material, disinfect tools between plants, use "
                       "copper-based bactericide if available.",
    "Powdery Mildew": "Improve air circulation, avoid excess nitrogen, "
                       "apply sulfur or a potassium-bicarbonate spray.",
    "Target Spot": "Remove infected leaves, avoid overhead watering, "
                    "apply a labelled fungicide, rotate crops.",
    "Septoria Leaf Spot": "Remove infected lower leaves, mulch to stop "
                           "soil splashing onto foliage, apply a "
                           "labelled fungicide, rotate crops.",
    # Note: the PlantVillage tomato virus classes repeat the plant name
    # inside the disease label itself (e.g. "Tomato___Tomato_mosaic_virus"),
    # so the key needs "Tomato" in it too, not just the disease name.
    "Tomato Mosaic Virus": "No cure -- remove and destroy infected "
                            "plants to stop spread, wash hands/tools "
                            "between plants (this virus spreads by "
                            "contact), control aphids.",
    "Tomato Yellow Leaf Curl Virus": "No cure -- remove infected "
                                      "plants, control whiteflies "
                                      "aggressively (their main "
                                      "vector), use reflective mulch "
                                      "or insect netting.",
    "Common Rust": "Apply a labelled fungicide at first sign, avoid "
                    "overhead watering, choose resistant varieties next "
                    "planting.",
    "Northern Leaf Blight": "Rotate crops, apply a labelled fungicide, "
                             "remove crop debris after harvest.",
    "Apple Scab": "Rake and destroy fallen leaves (where spores "
                   "overwinter), improve airflow through pruning, "
                   "apply a labelled fungicide in early spring.",
    "Black Rot": "Prune out infected wood/fruit, remove mummified "
                  "fruit, apply a labelled fungicide, improve airflow.",
    "Cedar Apple Rust": "Remove nearby cedar/juniper hosts if "
                         "practical, apply a labelled fungicide from "
                         "pink-bud stage, choose resistant varieties.",
}

DEFAULT_TREATMENT = (
    "Specific guidance for this exact label isn't in our lookup table yet. "
    "General steps: isolate/remove the worst-affected leaves, avoid "
    "overhead watering, improve airflow, and consult local agricultural "
    "extension guidance for a targeted treatment."
)
