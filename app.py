"""
app.py
------
Challenge 1 demo -- Team 17.

Flow (matches the team's plan):
  1. Pick a location on the map (or type coordinates).
  2. Pick a crop, optionally upload a leaf photo.
  3. Check whether the land is suitable for that crop.
  4. If suitable, show the water/humidity/soil data behind the call.
  5. If a photo was uploaded, check it for disease.
  6. Show a treatment/efficiency recommendation.

Run locally:   streamlit run app.py
Deploy free:   push this folder to a public GitHub repo, then
               https://share.streamlit.io -> New app -> pick the repo.
"""

import streamlit as st
import folium
from streamlit_folium import st_folium
from PIL import Image

from crop_data import CROP_THRESHOLDS, DISEASE_TREATMENTS, DEFAULT_TREATMENT
from data_sources import fetch_climate, fetch_soil
from suitability import evaluate
import disease_model

# Default map center: Doha, Qatar. Just a starting view -- any point on
# the map can be picked, this isn't a restriction on the tool.
DEFAULT_LAT, DEFAULT_LON = 25.2854, 51.5310

st.set_page_config(page_title="Challenge 1 - Land & Crop Suitability", page_icon="🌱", layout="wide")

if "lat" not in st.session_state:
    st.session_state.lat = DEFAULT_LAT
if "lon" not in st.session_state:
    st.session_state.lon = DEFAULT_LON


@st.cache_resource(show_spinner="Loading the disease-detection model (first run only)...")
def get_disease_model():
    return disease_model.load_model()


@st.cache_data(ttl=3600, show_spinner=False)
def cached_fetch_climate(lat, lon):
    return fetch_climate(lat, lon)


@st.cache_data(ttl=3600, show_spinner=False)
def cached_fetch_soil(lat, lon):
    return fetch_soil(lat, lon)


with st.sidebar:
    st.header("About this tool")
    st.write(
        "Pick a spot on the map, choose a crop, and get an explainable "
        "suitability read from real climate and soil data -- plus an "
        "optional leaf-photo disease check with treatment tips."
    )
    st.divider()
    st.caption("Reboot the Earth 2026 - Challenge 1 - Team 17")
    st.caption(
        "Data: NASA POWER, SoilGrids (ISRIC), OpenStreetMap. "
        "Disease model: PlantVillage-trained MobileNetV2 via Hugging Face."
    )

st.title("🌱 Land & Crop Suitability Checker")
st.caption("Team 17 - Reboot the Earth, Challenge 1")
st.divider()

# ---------- Step 1: location ----------
st.header("🗺️ 1. Choose a location")
map_col, coord_col = st.columns([2, 1])

with map_col:
    m = folium.Map(location=[st.session_state.lat, st.session_state.lon], zoom_start=6)
    folium.Marker(
        [st.session_state.lat, st.session_state.lon],
        tooltip="Selected point",
    ).add_to(m)
    map_data = st_folium(m, height=420, use_container_width=True, key="location_map")

    if map_data and map_data.get("last_clicked"):
        st.session_state.lat = map_data["last_clicked"]["lat"]
        st.session_state.lon = map_data["last_clicked"]["lng"]

with coord_col:
    st.session_state.lat = st.number_input(
        "Latitude", value=float(st.session_state.lat), format="%.4f"
    )
    st.session_state.lon = st.number_input(
        "Longitude", value=float(st.session_state.lon), format="%.4f"
    )
    st.caption("Click the map or type coordinates directly -- both stay in sync.")

st.divider()

# ---------- Step 2: crop + optional photo ----------
st.header("🌾 2. Pick a crop")
crop = st.selectbox("Crop", options=list(CROP_THRESHOLDS.keys()))
uploaded_photo = st.file_uploader(
    "Leaf photo (optional) -- upload one to also run a disease check",
    type=["jpg", "jpeg", "png"],
)
if uploaded_photo is not None:
    st.image(uploaded_photo, caption="Uploaded photo", width=220)

st.divider()

# ---------- Step 3-6: run everything ----------
st.header("✅ 3. Check suitability")
run = st.button("Check this location", type="primary")

if run:
    lat, lon = st.session_state.lat, st.session_state.lon

    with st.spinner("Fetching climate and soil data for this point..."):
        climate = cached_fetch_climate(lat, lon)
        soil = cached_fetch_soil(lat, lon)

    thresholds = CROP_THRESHOLDS[crop]
    verdict, score, reasons = evaluate(climate, soil, thresholds)

    status_box = {"Suitable": st.success, "Marginal": st.warning,
                  "Not suitable": st.error, "Unknown": st.info}[verdict]
    status_box(f"**{verdict}** for {crop} -- score {score:.2f} / 1.00")

    with st.container(border=True):
        st.markdown("**Why:**")
        for r in reasons:
            st.write("-", r)
        st.caption(thresholds["notes"])

    if climate.get("error"):
        st.warning(climate["error"])
    if soil.get("error"):
        st.warning(soil["error"])

    # ---------- Step 4: show the data behind the verdict ----------
    st.subheader("💧 Water / humidity / soil data used")
    with st.container(border=True):
        d1, d2, d3 = st.columns(3)
        d1.metric("Avg. temperature", f"{climate['temp_c']:.1f} C" if climate["temp_c"] is not None else "n/a")
        d2.metric("Est. annual rainfall", f"{climate['rain_mm_year']:.0f} mm" if climate["rain_mm_year"] is not None else "n/a")
        d3.metric("Avg. humidity", f"{climate['humidity_pct']:.0f}%" if climate["humidity_pct"] is not None else "n/a")
        st.metric("Soil pH", f"{soil['ph']:.1f}" if soil["ph"] is not None else "n/a")

    # ---------- Step 5-6: disease check + treatment ----------
    if uploaded_photo is not None:
        st.subheader("🔬 Disease check & recommendation")
        try:
            processor, model = get_disease_model()
            image = Image.open(uploaded_photo)
            with st.spinner("Analyzing the photo..."):
                predictions = disease_model.predict(image, processor, model, top_k=3)

            top = predictions[0]
            with st.container(border=True):
                st.write(
                    f"**Top match:** {top['plant']} - {top['disease']} "
                    f"({top['confidence']*100:.1f}% confidence)"
                )
                with st.expander("Other possibilities"):
                    for p in predictions[1:]:
                        st.write(f"- {p['plant']} - {p['disease']} ({p['confidence']*100:.1f}%)")

                treatment = DISEASE_TREATMENTS.get(top["disease"], DEFAULT_TREATMENT)
                st.info(f"**Recommendation:** {treatment}")
                st.caption(
                    "Model: linkanjarad/mobilenet_v2_1.0_224-plant-disease-identification "
                    "(MobileNetV2 fine-tuned on PlantVillage). Trained on clean lab-condition "
                    "photos, so accuracy on real field photos will be lower -- flag this "
                    "honestly if asked."
                )
        except Exception as exc:  # noqa: BLE001 -- keep the core demo alive either way
            st.error(f"Disease model unavailable right now ({exc}). "
                      "The suitability check above still works independently.")
    else:
        st.caption("Upload a leaf photo above to also run the disease check + treatment step.")
