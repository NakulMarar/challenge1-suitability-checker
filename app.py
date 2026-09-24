"""
app.py
------
Challenge 1 demo -- Team 17.

Flow:
  1. Pick a location on the map or type coordinates.
  2. Search and pick a crop.
  3. Optionally upload a leaf photo.
  4. Check whether the land is suitable for that crop.
  5. Show climate and soil data behind the decision.
  6. If a photo was uploaded, check it for disease.
  7. Show treatment/recommendation.

Run locally:
    streamlit run app.py
"""

import streamlit as st
import folium
from streamlit_folium import st_folium
from PIL import Image

from crop_data import (
    CROP_THRESHOLDS,
    DISEASE_TREATMENTS,
    DEFAULT_TREATMENT,
)

from data_sources import fetch_climate, fetch_soil
from suitability import evaluate
import disease_model


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Land & Crop Suitability",
    page_icon="🌱",
    layout="wide",
)


# ============================================================
# DEFAULT LOCATION
# ============================================================

DEFAULT_LAT = 25.2854
DEFAULT_LON = 51.5310


if "lat" not in st.session_state:
    st.session_state.lat = DEFAULT_LAT

if "lon" not in st.session_state:
    st.session_state.lon = DEFAULT_LON


# ============================================================
# CACHED FUNCTIONS
# ============================================================

@st.cache_resource(
    show_spinner="Loading the disease-detection model (first run only)..."
)
def get_disease_model():
    return disease_model.load_model()


@st.cache_data(ttl=3600, show_spinner=False)
def cached_fetch_climate(lat, lon):
    return fetch_climate(lat, lon)


@st.cache_data(ttl=3600, show_spinner=False)
def cached_fetch_soil(lat, lon):
    return fetch_soil(lat, lon)


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.header("🌱 About this tool")

    st.write(
        "Pick a location, search for a crop, and check whether "
        "the climate and soil conditions are suitable. You can "
        "also upload a leaf photo for an optional disease check."
    )

    st.divider()

    st.subheader("How it works")

    st.write("1. 📍 Select a location")
    st.write("2. 🌾 Search for a crop")
    st.write("3. 📊 Check suitability")
    st.write("4. 🔬 Check plant disease")
    st.write("5. 💡 Get recommendations")

    st.divider()

    st.caption("Reboot the Earth 2026 - Challenge 1 - Team 17")

    st.caption(
        "Data: NASA POWER, SoilGrids (ISRIC), OpenStreetMap."
    )

    st.caption(
        "Disease model: PlantVillage-trained MobileNetV2 "
        "via Hugging Face."
    )


# ============================================================
# TITLE
# ============================================================

st.title("🌱 Land & Crop Suitability Checker")

st.caption("Team 17 - Reboot the Earth, Challenge 1")

st.divider()


# ============================================================
# STEP 1 — LOCATION
# ============================================================

st.header("🗺️ 1. Choose a location")

map_col, coord_col = st.columns([2, 1])


# -------------------------
# MAP
# -------------------------

with map_col:

    m = folium.Map(
        location=[
            st.session_state.lat,
            st.session_state.lon
        ],
        zoom_start=6,
    )

    folium.Marker(
        [
            st.session_state.lat,
            st.session_state.lon
        ],
        tooltip="Selected point",
    ).add_to(m)

    map_data = st_folium(
        m,
        height=420,
        use_container_width=True,
        key="location_map",
    )

    if map_data and map_data.get("last_clicked"):

        st.session_state.lat = map_data["last_clicked"]["lat"]

        st.session_state.lon = map_data["last_clicked"]["lng"]


# -------------------------
# COORDINATES
# -------------------------

with coord_col:

    st.session_state.lat = st.number_input(
        "Latitude",
        value=float(st.session_state.lat),
        format="%.4f",
    )

    st.session_state.lon = st.number_input(
        "Longitude",
        value=float(st.session_state.lon),
        format="%.4f",
    )

    st.caption(
        "Click the map or type coordinates directly. "
        "Both methods stay in sync."
    )


st.divider()


# ============================================================
# STEP 2 — CROP
# ============================================================

st.header("🌾 2. Pick a crop")

st.write(
    "Search for the crop you want to plant in the selected region."
)


# Create crop list
crop_options = [
    "-- Select a crop --"
] + sorted(CROP_THRESHOLDS.keys())


# Searchable selectbox
crop = st.selectbox(
    "🔎 Search for a crop",
    options=crop_options,
    index=0,
    help="Start typing the name of a crop to search for it.",
)


# Show selected crop information
if crop != "-- Select a crop --":

    selected_crop_data = CROP_THRESHOLDS[crop]

    with st.container(border=True):

        st.subheader(f"🌱 {crop}")

        info_col1, info_col2, info_col3 = st.columns(3)

        info_col1.metric(
            "Temperature",
            f"{selected_crop_data['temp_c'][0]}–"
            f"{selected_crop_data['temp_c'][1]} °C",
        )

        info_col2.metric(
            "Rainfall",
            f"{selected_crop_data['rain_mm'][0]}–"
            f"{selected_crop_data['rain_mm'][1]} mm",
        )

        info_col3.metric(
            "Soil pH",
            f"{selected_crop_data['ph'][0]}–"
            f"{selected_crop_data['ph'][1]}",
        )

        st.caption(selected_crop_data["notes"])


# -------------------------
# LEAF PHOTO
# -------------------------

uploaded_photo = st.file_uploader(
    "Leaf photo (optional) — upload one to also run a disease check",
    type=["jpg", "jpeg", "png"],
)


if uploaded_photo is not None:

    st.image(
        uploaded_photo,
        caption="Uploaded leaf photo",
        width=220,
    )


st.divider()


# ============================================================
# STEP 3 — CHECK SUITABILITY
# ============================================================

st.header("✅ 3. Check suitability")

run = st.button(
    "🔍 Check this location",
    type="primary",
    use_container_width=True,
)


if run:

    # -------------------------
    # Make sure crop was selected
    # -------------------------

    if crop == "-- Select a crop --":

        st.warning(
            "🌾 Please select a crop before checking the location."
        )

        st.stop()


    # -------------------------
    # Get coordinates
    # -------------------------

    lat = st.session_state.lat
    lon = st.session_state.lon


    # -------------------------
    # Fetch climate + soil
    # -------------------------

    with st.spinner(
        "Fetching climate and soil data for this location..."
    ):

        climate = cached_fetch_climate(
            lat,
            lon,
        )

        soil = cached_fetch_soil(
            lat,
            lon,
        )


    # -------------------------
    # Get crop thresholds
    # -------------------------

    thresholds = CROP_THRESHOLDS[crop]


    # -------------------------
    # Evaluate suitability
    # -------------------------

    verdict, score, reasons = evaluate(
        climate,
        soil,
        thresholds,
    )


    # ========================================================
    # RESULT
    # ========================================================

    st.subheader("🌱 Suitability result")


    status_box = {
        "Suitable": st.success,
        "Marginal": st.warning,
        "Not suitable": st.error,
        "Unknown": st.info,
    }[verdict]


    status_box(
        f"**{verdict}** for **{crop}** "
        f"— score **{score:.2f} / 1.00**"
    )


    # -------------------------
    # Reasons
    # -------------------------

    with st.container(border=True):

        st.markdown("### Why?")

        for reason in reasons:

            st.write(
                f"- {reason}"
            )

        st.caption(
            thresholds["notes"]
        )


    # -------------------------
    # API errors
    # -------------------------

    if climate.get("error"):

        st.warning(
            f"Climate data warning: {climate['error']}"
        )


    if soil.get("error"):

        st.warning(
            f"Soil data warning: {soil['error']}"
        )


    # ========================================================
    # STEP 4 — CLIMATE / SOIL DATA
    # ========================================================

    st.subheader(
        "💧 Water / humidity / soil data used"
    )


    with st.container(border=True):

        d1, d2, d3 = st.columns(3)


        # Temperature
        if climate["temp_c"] is not None:

            d1.metric(
                "Avg. temperature",
                f"{climate['temp_c']:.1f} °C",
            )

        else:

            d1.metric(
                "Avg. temperature",
                "n/a",
            )


        # Rainfall
        if climate["rain_mm_year"] is not None:

            d2.metric(
                "Est. annual rainfall",
                f"{climate['rain_mm_year']:.0f} mm",
            )

        else:

            d2.metric(
                "Est. annual rainfall",
                "n/a",
            )


        # Humidity
        if climate["humidity_pct"] is not None:

            d3.metric(
                "Avg. humidity",
                f"{climate['humidity_pct']:.0f}%",
            )

        else:

            d3.metric(
                "Avg. humidity",
                "n/a",
            )


        # Soil pH
        if soil["ph"] is not None:

            st.metric(
                "Soil pH",
                f"{soil['ph']:.1f}",
            )

        else:

            st.metric(
                "Soil pH",
                "n/a",
            )


    # ========================================================
    # STEP 5 — DISEASE CHECK
    # ========================================================

    if uploaded_photo is not None:

        st.subheader(
            "🔬 Disease check & recommendation"
        )


        try:

            # Load model
            processor, model = get_disease_model()


            # Open uploaded image
            image = Image.open(
                uploaded_photo
            )


            # Run prediction
            with st.spinner(
                "Analyzing the leaf photo..."
            ):

                predictions = disease_model.predict(
                    image,
                    processor,
                    model,
                    top_k=3,
                )


            # Top prediction
            top = predictions[0]


            with st.container(border=True):

                st.write(
                    f"**Top match:** "
                    f"{top['plant']} - {top['disease']} "
                    f"({top['confidence'] * 100:.1f}% confidence)"
                )


                # Other predictions
                with st.expander(
                    "Other possibilities"
                ):

                    for prediction in predictions[1:]:

                        st.write(
                            f"- {prediction['plant']} - "
                            f"{prediction['disease']} "
                            f"({prediction['confidence'] * 100:.1f}%)"
                        )


                # Treatment
                treatment = DISEASE_TREATMENTS.get(
                    top["disease"],
                    DEFAULT_TREATMENT,
                )


                st.info(
                    f"**Recommendation:** {treatment}"
                )


                st.caption(
                    "Model: linkanjarad/"
                    "mobilenet_v2_1.0_224-plant-disease-identification "
                    "(MobileNetV2 fine-tuned on PlantVillage). "
                    "The model was trained on mostly clean laboratory-style "
                    "images, so performance on real field photos may be lower."
                )


        except Exception as exc:

            st.error(
                "Disease model unavailable right now "
                f"({exc}). The suitability check above "
                "still works independently."
            )


    # ========================================================
    # NO PHOTO
    # ========================================================

    else:

        st.caption(
            "📷 Upload a leaf photo above to also run "
            "the disease check and treatment step."
        )
