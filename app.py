"""
app.py
------
Reboot the Earth 2026
Challenge 1 - Team 17

Land & Crop Suitability Checker

Features:
    - Interactive location selection
    - NASA POWER climate data
    - SoilGrids soil pH
    - Rule-based crop suitability
    - Crop Finder
    - Disease detection
    - Treatment guidance
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

from data_sources import (
    fetch_climate,
    fetch_soil,
)

from suitability import (
    evaluate,
    get_factor_scores,
)

import disease_model


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="CropWise | Team 17",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown(
    """
    <style>

    /* Main background */

    .stApp {
        background:
            linear-gradient(
                180deg,
                #f7faf8 0%,
                #ffffff 35%,
                #f7faf8 100%
            );
    }

    /* Remove excessive top spacing */

    .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
        max-width: 1400px;
    }

    /* Main hero */

    .hero {
        padding: 2rem 2.2rem;
        border-radius: 24px;
        background:
            linear-gradient(
                135deg,
                #0f5132 0%,
                #198754 55%,
                #20c997 100%
            );
        color: white;
        margin-bottom: 1.5rem;
        box-shadow: 0 12px 35px rgba(15, 81, 50, 0.18);
    }

    .hero h1 {
        font-size: 2.7rem;
        margin: 0;
        font-weight: 800;
        letter-spacing: -1px;
    }

    .hero p {
        margin-top: 0.6rem;
        font-size: 1.05rem;
        opacity: 0.92;
    }

    .hero-badge {
        display: inline-block;
        margin-top: 1rem;
        padding: 0.35rem 0.8rem;
        border-radius: 999px;
        background: rgba(255,255,255,0.16);
        font-size: 0.82rem;
        font-weight: 700;
    }

    /* Cards */

    .card {
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 18px;
        padding: 1.25rem;
        margin-bottom: 1rem;
        box-shadow: 0 5px 18px rgba(0,0,0,0.04);
    }

    .card-title {
        font-size: 1.05rem;
        font-weight: 750;
        margin-bottom: 0.35rem;
    }

    .card-subtitle {
        color: #6b7280;
        font-size: 0.9rem;
    }

    /* Score */

    .score-card {
        text-align: center;
        padding: 1.6rem;
        border-radius: 20px;
        background: white;
        border: 1px solid #e5e7eb;
        box-shadow: 0 6px 20px rgba(0,0,0,0.05);
    }

    .score-number {
        font-size: 3.4rem;
        font-weight: 850;
        line-height: 1;
        margin: 0.6rem 0;
    }

    .score-label {
        font-size: 0.85rem;
        color: #6b7280;
    }

    /* Factor */

    .factor {
        padding: 1rem;
        border-radius: 15px;
        background: #f8fafc;
        border: 1px solid #e5e7eb;
        height: 100%;
    }

    .factor-name {
        font-weight: 700;
        margin-bottom: 0.4rem;
    }

    .factor-value {
        font-size: 1.35rem;
        font-weight: 800;
    }

    .factor-range {
        color: #6b7280;
        font-size: 0.8rem;
        margin-top: 0.25rem;
    }

    /* Crop finder */

    .crop-result {
        padding: 1rem;
        border: 1px solid #e5e7eb;
        border-radius: 15px;
        background: white;
        margin-bottom: 0.7rem;
    }

    .crop-name {
        font-size: 1.05rem;
        font-weight: 800;
    }

    /* Footer */

    .footer {
        text-align: center;
        color: #6b7280;
        font-size: 0.8rem;
        padding-top: 2rem;
    }

    /* Sidebar */

    [data-testid="stSidebar"] {
        border-right: 1px solid #e5e7eb;
    }

    </style>
    """,
    unsafe_allow_html=True,
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
    show_spinner="Loading the disease-detection model..."
)
def get_disease_model():

    return disease_model.load_model()


@st.cache_data(
    ttl=3600,
    show_spinner=False,
)
def cached_fetch_climate(lat, lon):

    return fetch_climate(lat, lon)


@st.cache_data(
    ttl=3600,
    show_spinner=False,
)
def cached_fetch_soil(lat, lon):

    return fetch_soil(lat, lon)


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def format_value(value, unit=""):

    if value is None:
        return "N/A"

    return f"{value}{unit}"


def score_percent(score):

    if score is None:
        return 0

    return int(round(score * 100))


def verdict_message(verdict):

    messages = {
        "Suitable":
            "The current conditions fall mostly within the preferred ranges.",
        "Marginal":
            "Some conditions are outside the preferred ranges, so additional management may be needed.",
        "Not suitable":
            "Several measured conditions are outside the preferred ranges.",
        "Unknown":
            "There was not enough data to calculate a suitability score.",
    }

    return messages.get(verdict, "")


def verdict_icon(verdict):

    return {
        "Suitable": "🟢",
        "Marginal": "🟡",
        "Not suitable": "🔴",
        "Unknown": "⚪",
    }.get(verdict, "⚪")


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.markdown("## 🌱 CropWise")

    st.caption(
        "Smart land and crop screening"
    )

    st.divider()

    st.markdown("### How it works")

    st.markdown(
        """
        **1. Location**  
        Select a point on the map.

        **2. Crop**  
        Choose a crop or use Crop Finder.

        **3. Analyze**  
        NASA POWER + SoilGrids provide the environmental data.

        **4. Decide**  
        The transparent scoring system explains the result.

        **5. Disease AI**  
        Upload a leaf photo for an optional disease screening.
        """
    )

    st.divider()

    st.markdown("### Data sources")

    st.caption(
        "NASA POWER\n\n"
        "SoilGrids / ISRIC\n\n"
        "OpenStreetMap\n\n"
        "PlantVillage-trained MobileNetV2"
    )

    st.divider()

    st.caption(
        "Reboot the Earth 2026 • Challenge 1 • Team 17"
    )


# ============================================================
# HERO
# ============================================================

st.markdown(
    """
    <div class="hero">
        <div class="hero-badge">
            REBOOT THE EARTH 2026 • CHALLENGE 1 • TEAM 17
        </div>

        <h1>🌱 CropWise</h1>

        <p>
            Understand whether a crop matches the environmental
            conditions of a location — using real climate and soil data.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# TABS
# ============================================================

tab_analyze, tab_finder, tab_disease, tab_about = st.tabs(
    [
        "🗺️ Analyze Land",
        "🌾 Crop Finder",
        "🔬 Disease AI",
        "ℹ️ About",
    ]
)


# ============================================================
# TAB 1 — ANALYZE LAND
# ============================================================

with tab_analyze:

    st.subheader("Choose your location")

    map_col, coordinate_col = st.columns(
        [2.3, 1],
        gap="large",
    )

    with map_col:

        map_object = folium.Map(
            location=[
                st.session_state.lat,
                st.session_state.lon,
            ],
            zoom_start=5,
            control_scale=True,
        )

        folium.Marker(
            [
                st.session_state.lat,
                st.session_state.lon,
            ],
            tooltip="Selected location",
            popup="Selected location",
        ).add_to(map_object)

        map_data = st_folium(
            map_object,
            height=430,
            use_container_width=True,
            key="main_location_map",
        )

        if map_data and map_data.get("last_clicked"):

            st.session_state.lat = round(
                map_data["last_clicked"]["lat"],
                5,
            )

            st.session_state.lon = round(
                map_data["last_clicked"]["lng"],
                5,
            )

    with coordinate_col:

        st.markdown(
            """
            <div class="card">
                <div class="card-title">
                    📍 Coordinates
                </div>
                <div class="card-subtitle">
                    Click the map or enter coordinates manually.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.session_state.lat = st.number_input(
            "Latitude",
            min_value=-90.0,
            max_value=90.0,
            value=float(st.session_state.lat),
            format="%.5f",
        )

        st.session_state.lon = st.number_input(
            "Longitude",
            min_value=-180.0,
            max_value=180.0,
            value=float(st.session_state.lon),
            format="%.5f",
        )

        st.info(
            f"Selected: "
            f"{st.session_state.lat:.5f}, "
            f"{st.session_state.lon:.5f}"
        )

    st.divider()

    # --------------------------------------------------------
    # Crop selection
    # --------------------------------------------------------

    st.subheader("Select a crop")

    crop_options = [
        "-- Select a crop --"
    ] + sorted(CROP_THRESHOLDS.keys())

    crop = st.selectbox(
        "Search for a crop",
        options=crop_options,
        index=0,
        help="Start typing to search the crop list.",
    )

    if crop != "-- Select a crop --":

        thresholds = CROP_THRESHOLDS[crop]

        st.markdown(
            f"""
            <div class="card">
                <div class="card-title">
                    🌾 {crop}
                </div>

                <div class="card-subtitle">
                    Reference environmental range
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        c1, c2, c3 = st.columns(3)

        c1.metric(
            "Temperature",
            f"{thresholds['temp_c'][0]}–{thresholds['temp_c'][1]} °C",
        )

        c2.metric(
            "Rainfall",
            f"{thresholds['rain_mm'][0]}–{thresholds['rain_mm'][1]} mm",
        )

        c3.metric(
            "Soil pH",
            f"{thresholds['ph'][0]}–{thresholds['ph'][1]}",
        )

        st.caption(
            thresholds.get(
                "notes",
                "Reference crop information."
            )
        )

    st.divider()

    analyze = st.button(
        "🚀 Analyze this location",
        type="primary",
        use_container_width=True,
    )

    if analyze:

        if crop == "-- Select a crop --":

            st.warning(
                "Please select a crop before running the analysis."
            )

        else:

            latitude = st.session_state.lat
            longitude = st.session_state.lon

            with st.spinner(
                "Fetching climate and soil data..."
            ):

                climate = cached_fetch_climate(
                    latitude,
                    longitude,
                )

                soil = cached_fetch_soil(
                    latitude,
                    longitude,
                )

            thresholds = CROP_THRESHOLDS[crop]

            verdict, score, reasons = evaluate(
                climate,
                soil,
                thresholds,
            )

            factors = get_factor_scores(
                climate,
                soil,
                thresholds,
            )

            st.session_state.analysis = {
                "crop": crop,
                "climate": climate,
                "soil": soil,
                "thresholds": thresholds,
                "verdict": verdict,
                "score": score,
                "reasons": reasons,
                "factors": factors,
            }

    # --------------------------------------------------------
    # Display saved analysis
    # --------------------------------------------------------

    analysis = st.session_state.get(
        "analysis"
    )

    if analysis:

        st.divider()

        verdict = analysis["verdict"]
        score = analysis["score"]
        climate = analysis["climate"]
        soil = analysis["soil"]

        st.subheader(
            f"{verdict_icon(verdict)} Analysis result"
        )

        result_col1, result_col2 = st.columns(
            [1, 2],
            gap="large",
        )

        with result_col1:

            st.markdown(
                f"""
                <div class="score-card">

                    <div class="score-label">
                        SUITABILITY SCORE
                    </div>

                    <div class="score-number">
                        {score_percent(score)}%
                    </div>

                    <strong>
                        {verdict}
                    </strong>

                    <div class="score-label">
                        Transparent rule-based screening
                    </div>

                </div>
                """,
                unsafe_allow_html=True,
            )

        with result_col2:

            st.markdown(
                f"""
                <div class="card">

                    <div class="card-title">
                        Why this result?
                    </div>

                    <div class="card-subtitle">
                        {verdict_message(verdict)}
                    </div>

                </div>
                """,
                unsafe_allow_html=True,
            )

            for reason in analysis["reasons"]:
                st.write("•", reason)

        st.subheader("Environmental factors")

        factor_columns = st.columns(3)

        for column, (name, factor) in zip(
            factor_columns,
            analysis["factors"].items(),
        ):

            value = factor["value"]

            if value is None:

                display_value = "N/A"

            elif name == "Temperature":

                display_value = f"{value:.1f} °C"

            elif name == "Rainfall":

                display_value = f"{value:.0f} mm"

            else:

                display_value = f"{value:.1f}"

            if factor["score"] == 1.0:
                status = "🟢 Within range"

            elif factor["score"] == 0.5:
                status = "🟡 Marginal"

            elif factor["score"] == 0.0:
                status = "🔴 Outside range"

            else:
                status = "⚪ Data unavailable"

            with column:

                st.markdown(
                    f"""
                    <div class="factor">

                        <div class="factor-name">
                            {name}
                        </div>

                        <div class="factor-value">
                            {display_value}
                        </div>

                        <div class="factor-range">
                            Preferred:
                            {factor['low']}
                            –
                            {factor['high']}
                            {factor['unit']}
                        </div>

                        <br>

                        <strong>
                            {status}
                        </strong>

                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        st.subheader("Climate & soil snapshot")

        d1, d2, d3, d4 = st.columns(4)

        d1.metric(
            "🌡️ Temperature",
            (
                f"{climate['temp_c']:.1f} °C"
                if climate.get("temp_c") is not None
                else "N/A"
            ),
        )

        d2.metric(
            "🌧️ Rainfall",
            (
                f"{climate['rain_mm_year']:.0f} mm/year"
                if climate.get("rain_mm_year") is not None
                else "N/A"
            ),
        )

        d3.metric(
            "💧 Humidity",
            (
                f"{climate['humidity_pct']:.0f}%"
                if climate.get("humidity_pct") is not None
                else "N/A"
            ),
        )

        d4.metric(
            "🪨 Soil pH",
            (
                f"{soil['ph']:.1f}"
                if soil.get("ph") is not None
                else "N/A"
            ),
        )

        if climate.get("error"):
            st.warning(climate["error"])

        if soil.get("error"):
            st.warning(soil["error"])

        st.caption(
            "The score is a transparent environmental screening "
            "indicator based on the reference ranges in crop_data.py. "
            "It is not a guaranteed yield prediction."
        )


# ============================================================
# TAB 2 — CROP FINDER
# ============================================================

with tab_finder:

    st.subheader("🌾 Find crops for this location")

    st.write(
        "Analyze the selected location against every crop in the "
        "reference database."
    )

    st.info(
        "This compares the same temperature, rainfall and soil-pH "
        "rules used by the main suitability checker."
    )

    if st.button(
        "🔎 Find matching crops",
        type="primary",
        use_container_width=True,
    ):

        latitude = st.session_state.lat
        longitude = st.session_state.lon

        with st.spinner(
            "Analyzing environmental conditions against all crops..."
        ):

            climate = cached_fetch_climate(
                latitude,
                longitude,
            )

            soil = cached_fetch_soil(
                latitude,
                longitude,
            )

        results = []

        for crop_name, thresholds in CROP_THRESHOLDS.items():

            verdict, score, reasons = evaluate(
                climate,
                soil,
                thresholds,
            )

            results.append(
                {
                    "crop": crop_name,
                    "verdict": verdict,
                    "score": score,
                    "reasons": reasons,
                }
            )

        results.sort(
            key=lambda item: item["score"],
            reverse=True,
        )

        st.session_state.crop_results = results
        st.session_state.crop_finder_climate = climate
        st.session_state.crop_finder_soil = soil

    results = st.session_state.get(
        "crop_results"
    )

    if results:

        climate = st.session_state.crop_finder_climate
        soil = st.session_state.crop_finder_soil

        st.markdown(
            f"""
            <div class="card">

                <div class="card-title">
                    📍 Location analyzed
                </div>

                <div class="card-subtitle">
                    Latitude:
                    {st.session_state.lat:.5f}
                    &nbsp; • &nbsp;
                    Longitude:
                    {st.session_state.lon:.5f}
                </div>

            </div>
            """,
            unsafe_allow_html=True,
        )

        if climate.get("error"):
            st.warning(climate["error"])

        if soil.get("error"):
            st.warning(soil["error"])

        st.subheader("Top environmental matches")

        for number, result in enumerate(
            results[:8],
            start=1,
        ):

            score = score_percent(
                result["score"]
            )

            icon = verdict_icon(
                result["verdict"]
            )

            st.markdown(
                f"""
                <div class="crop-result">

                    <div class="crop-name">
                        {number}. {result['crop']}
                    </div>

                    <div>
                        {icon}
                        {result['verdict']}
                        &nbsp; • &nbsp;
                        <strong>{score}%</strong>
                    </div>

                </div>
                """,
                unsafe_allow_html=True,
            )

        with st.expander(
            "Show all crops"
        ):

            for result in results:

                st.write(
                    f"{verdict_icon(result['verdict'])} "
                    f"**{result['crop']}** — "
                    f"{score_percent(result['score'])}% "
                    f"({result['verdict']})"
                )

        st.caption(
            "These are model matches based only on the environmental "
            "thresholds currently stored in crop_data.py. They should "
            "not be interpreted as guaranteed agronomic recommendations."
        )


# ============================================================
# TAB 3 — DISEASE AI
# ============================================================

with tab_disease:

    st.subheader("🔬 Plant Disease AI")

    st.write(
        "Upload a clear leaf image to run the PlantVillage-trained "
        "MobileNetV2 classifier."
    )

    uploaded_photo = st.file_uploader(
        "Upload a leaf photo",
        type=[
            "jpg",
            "jpeg",
            "png",
            "webp",
        ],
        key="disease_upload",
    )

    if uploaded_photo:

        image = Image.open(
            uploaded_photo
        ).convert("RGB")

        left, right = st.columns(
            [1, 1],
            gap="large",
        )

        with left:

            st.image(
                image,
                caption="Uploaded image",
                use_container_width=True,
            )

        with right:

            st.markdown(
                """
                <div class="card">

                    <div class="card-title">
                        🧠 AI screening
                    </div>

                    <div class="card-subtitle">
                        The image is compared with labels learned
                        from the PlantVillage dataset.
                    </div>

                </div>
                """,
                unsafe_allow_html=True,
            )

            run_disease = st.button(
                "Analyze leaf",
                type="primary",
                use_container_width=True,
            )

        if run_disease:

            try:

                with st.spinner(
                    "Analyzing the leaf image..."
                ):

                    model = get_disease_model()

                    predictions = disease_model.predict(
                        image,
                        model,
                        top_k=3,
                    )

                if not predictions:

                    st.error(
                        "The model did not return a prediction."
                    )

                else:

                    top = predictions[0]

                    confidence = (
                        top["confidence"] * 100
                    )

                    st.divider()

                    st.subheader(
                        "AI result"
                    )

                    r1, r2 = st.columns(2)

                    with r1:

                        st.metric(
                            "Plant",
                            top["plant"],
                        )

                    with r2:

                        st.metric(
                            "Confidence",
                            f"{confidence:.1f}%",
                        )

                    if top["disease"].lower() == "healthy":

                        st.success(
                            f"🌿 The model's top label is "
                            f"**Healthy {top['plant']}**."
                        )

                    else:

                        st.warning(
                            f"⚠️ The model's top label is "
                            f"**{top['disease']}**."
                        )

                    treatment = DISEASE_TREATMENTS.get(
                        top["disease"],
                        DEFAULT_TREATMENT,
                    )

                    st.markdown(
                        f"""
                        <div class="card">

                            <div class="card-title">
                                💡 General guidance
                            </div>

                            <div>
                                {treatment}
                            </div>

                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                    if len(predictions) > 1:

                        with st.expander(
                            "Other model predictions"
                        ):

                            for prediction in predictions[1:]:

                                st.write(
                                    f"• "
                                    f"**{prediction['plant']}** — "
                                    f"{prediction['disease']} "
                                    f"({prediction['confidence'] * 100:.1f}%)"
                                )

                    st.info(
                        "Important: this is an AI screening tool, "
                        "not a definitive plant-disease diagnosis. "
                        "PlantVillage images are generally cleaner "
                        "than real field photographs, so real-world "
                        "performance can differ."
                    )

            except Exception as exc:

                st.error(
                    "The disease model could not be loaded or run."
                )

                st.code(
                    str(exc)
                )

    else:

        st.info(
            "Upload a JPG, JPEG, PNG or WebP leaf image to begin."
        )


# ============================================================
# TAB 4 — ABOUT
# ============================================================

with tab_about:

    st.subheader("About CropWise")

    st.markdown(
        """
        ### 🌱 The idea

        CropWise is a transparent environmental screening tool
        designed to help users understand whether a crop's
        preferred environmental conditions match a selected
        location.

        ### 📊 Data pipeline

        **Location**
        → latitude / longitude

        **Climate**
        → NASA POWER

        **Soil**
        → SoilGrids / ISRIC

        **Scoring**
        → transparent range-based rules

        **Optional disease screening**
        → MobileNetV2 trained on PlantVillage

        ### 🔎 Why transparent scoring?

        Instead of producing an unexplained AI number, the app
        shows the individual environmental factors behind the
        result:

        - Temperature
        - Rainfall
        - Soil pH

        This makes the result easier to inspect and explain.

        ### ⚠️ Limitations

        The crop ranges in `crop_data.py` are reference ranges
        used for this prototype. They are not a complete crop
        production model.

        Real agricultural decisions can also depend on:

        - soil texture
        - salinity
        - nutrients
        - irrigation
        - sunlight
        - elevation
        - pests
        - local varieties
        - planting season
        - farm management

        Disease predictions are also screening results and should
        not be treated as definitive diagnoses.
        """
    )

    st.divider()

    st.markdown(
        """
        **Reboot the Earth 2026**

        Challenge 1 • Team 17

        Built with free/open data and open-source software.
        """
    )


# ============================================================
# FOOTER
# ============================================================

st.markdown(
    """
    <div class="footer">
        CropWise • Team 17 • Reboot the Earth 2026
        <br>
        Environmental screening, not guaranteed agricultural advice.
    </div>
    """,
    unsafe_allow_html=True,
)
