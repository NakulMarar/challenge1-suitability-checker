import streamlit as st
import textwrap
import folium
from streamlit_folium import st_folium
from PIL import Image

from crop_data import (
    CROP_THRESHOLDS,
    DISEASE_TREATMENTS,
    DEFAULT_TREATMENT,
)

from data_sources import fetch_climate, fetch_soil
from suitability import evaluate, get_factor_scores
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
    textwrap.dedent(
        """
        <style>

        /* =========================
           GLOBAL
           ========================= */

        .stApp {
            background: #080b09 !important;
            color: #f2f5f3 !important;
        }

        .main .block-container {
            max-width: 1400px !important;
            padding-top: 1.5rem !important;
            padding-bottom: 3rem !important;
        }

        h1, h2, h3, h4 {
            color: #f2f5f3 !important;
        }

        p {
            color: #c7d1cb;
        }

        hr {
            border-color: #202c24 !important;
        }


        /* =========================
           SIDEBAR
           ========================= */

        [data-testid="stSidebar"] {
            background: #0d120f !important;
            border-right: 1px solid #202a23 !important;
        }

        [data-testid="stSidebar"] * {
            color: #e8eee9 !important;
        }


        /* =========================
           HERO
           ========================= */

        .hero {
            background: linear-gradient(
                135deg,
                #06150c 0%,
                #0b4d2c 100%
            );

            padding: 32px 36px;
            border-radius: 22px;
            margin-bottom: 25px;

            border: 1px solid #1d5a38;

            box-shadow:
                0 10px 35px rgba(0, 0, 0, 0.45);
        }

        .hero h1 {
            color: #ffffff !important;
            font-size: 42px;
            font-weight: 800;
            margin: 8px 0 5px 0;
        }

        .hero p {
            color: #cdebd8 !important;
            font-size: 17px;
            margin: 0;
        }

        .badge {
            display: inline-block;
            background: rgba(32, 180, 93, 0.16);
            border: 1px solid rgba(32, 180, 93, 0.3);
            padding: 6px 12px;
            border-radius: 999px;
            font-size: 12px;
            font-weight: 700;
            color: #7ff0a7 !important;
            letter-spacing: 0.4px;
        }


        /* =========================
           CARDS
           ========================= */

        .card {
            background: #101612 !important;
            border: 1px solid #202c24 !important;
            border-radius: 17px;
            padding: 20px;
            box-shadow: 0 5px 20px rgba(0, 0, 0, 0.25);
            margin-bottom: 15px;
        }

        .card-title {
            font-size: 18px;
            font-weight: 750;
            color: #f2f5f3 !important;
        }

        .card-subtitle {
            color: #91a49a !important;
            font-size: 14px;
            margin-top: 4px;
        }


        /* =========================
           SCORE CARD
           ========================= */

        .score-card {
            background: #101612 !important;
            border: 1px solid #202c24 !important;
            border-radius: 20px;
            padding: 25px;
            text-align: center;
            box-shadow: 0 5px 20px rgba(0, 0, 0, 0.25);
        }

        .score-title {
            color: #91a49a !important;
            font-size: 13px;
            font-weight: 700;
            letter-spacing: 1px;
        }

        .score-number {
            color: #38d878 !important;
            font-size: 52px;
            font-weight: 850;
            margin: 8px 0;
        }

        .score-verdict {
            color: #f2f5f3 !important;
            font-size: 18px;
            font-weight: 750;
        }


        /* =========================
           FACTOR CARDS
           ========================= */

        .factor-card {
            background: #101612 !important;
            border: 1px solid #202c24 !important;
            border-radius: 17px;
            padding: 19px;
            min-height: 135px;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.25);
        }

        .factor-title {
            font-weight: 750;
            color: #dce8df !important;
        }

        .factor-value {
            font-size: 25px;
            font-weight: 800;
            color: #ffffff !important;
            margin-top: 8px;
        }

        .factor-range {
            color: #82958b !important;
            font-size: 12px;
            margin-top: 5px;
        }


        /* =========================
           CROP CARDS
           ========================= */

        .crop-card {
            background: #101612 !important;
            border: 1px solid #202c24 !important;
            border-radius: 15px;
            padding: 15px 18px;
            margin-bottom: 10px;
        }

        .crop-name {
            color: #f2f5f3 !important;
            font-size: 17px;
            font-weight: 800;
        }

        .crop-score {
            color: #38d878 !important;
            font-weight: 800;
        }


        /* =========================
           NAVIGATION
           ========================= */

        div[role="radiogroup"] {
            background: #101612 !important;
            border: 1px solid #202c24 !important;
            border-radius: 16px;
            padding: 8px;
            gap: 6px;
            box-shadow: 0 4px 18px rgba(0, 0, 0, 0.3);
        }

        div[role="radiogroup"] label {
            border-radius: 10px;
            padding: 10px 15px;
            color: #dce8df !important;
            font-weight: 650;
        }

        div[role="radiogroup"] label p {
            color: #dce8df !important;
        }

        div[role="radiogroup"] label:hover {
            background: #18241c !important;
        }


        /* =========================
           INPUTS
           ========================= */

        input {
            background: #101612 !important;
            color: #ffffff !important;
        }

        div[data-baseweb="select"] > div {
            background: #101612 !important;
            border-color: #29372e !important;
        }


        /* =========================
           BUTTONS
           ========================= */

        .stButton > button {
            border-radius: 10px !important;
            font-weight: 700 !important;
        }


        /* =========================
           MAP
           ========================= */

        iframe {
            border-radius: 16px !important;
        }


        /* =========================
           FOOTER
           ========================= */

        .footer {
            text-align: center;
            color: #66786d !important;
            font-size: 12px;
            padding-top: 30px;
        }

        </style>
        """
    ),
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
# CACHING
# ============================================================

@st.cache_resource(show_spinner="Loading disease AI...")
def get_disease_model():
    return disease_model.load_model()


@st.cache_data(ttl=3600, show_spinner=False)
def cached_fetch_climate(lat, lon):
    return fetch_climate(lat, lon)


@st.cache_data(ttl=3600, show_spinner=False)
def cached_fetch_soil(lat, lon):
    return fetch_soil(lat, lon)


# ============================================================
# HERO
# ============================================================

st.markdown(
    textwrap.dedent(
        """
        <div class="hero">

            <span class="badge">
                REBOOT THE EARTH 2026 • CHALLENGE 1 • TEAM 17
            </span>

            <h1>🌱 CropWise</h1>

            <p>
                Smart environmental screening for better crop decisions.
                Analyze land, discover suitable crops and screen plant diseases.
            </p>

        </div>
        """
    ),
    unsafe_allow_html=True,
)


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.markdown("## 🌱 CropWise")

    st.caption("Land & Crop Intelligence")

    st.divider()

    st.markdown("### 🧭 Navigation")

    st.write("🗺️ Analyze Land")
    st.write("🌾 Crop Finder")
    st.write("🔬 Disease AI")
    st.write("ℹ️ About")

    st.divider()

    st.markdown("### 📡 Data Sources")

    st.caption(
        "NASA POWER\n\n"
        "SoilGrids / ISRIC\n\n"
        "OpenStreetMap\n\n"
        "PlantVillage + MobileNetV2"
    )

    st.divider()

    st.caption("Team 17 • Reboot the Earth 2026")


# ============================================================
# NAVIGATION
# ============================================================

page = st.radio(
    "Navigation",
    [
        "🗺️ Analyze Land",
        "🌾 Crop Finder",
        "🔬 Disease AI",
        "ℹ️ About",
    ],
    horizontal=True,
    label_visibility="collapsed",
)

st.divider()


# ============================================================
# ANALYZE LAND
# ============================================================

if page == "🗺️ Analyze Land":

    st.header("🗺️ Analyze Land")

    st.caption(
        "Select a location and determine how well a crop matches "
        "the measured environmental conditions."
    )

    map_col, coord_col = st.columns(
        [2.2, 1],
        gap="large",
    )

    # --------------------------------------------------------
    # MAP
    # --------------------------------------------------------

    with map_col:

        m = folium.Map(
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
        ).add_to(m)

        map_data = st_folium(
            m,
            height=430,
            use_container_width=True,
            key="land_map",
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

    # --------------------------------------------------------
    # LOCATION
    # --------------------------------------------------------

    with coord_col:

        st.markdown(
            textwrap.dedent(
                """
                <div class="card">
                    <div class="card-title">
                        📍 Location
                    </div>

                    <div class="card-subtitle">
                        Click the map or enter coordinates.
                    </div>
                </div>
                """
            ),
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

        st.success(
            f"{st.session_state.lat:.5f}, "
            f"{st.session_state.lon:.5f}"
        )

    st.divider()

    # --------------------------------------------------------
    # CROP
    # --------------------------------------------------------

    st.header("🌾 Select a crop")

    crop_options = [
        "-- Select a crop --"
    ] + sorted(CROP_THRESHOLDS.keys())

    crop = st.selectbox(
        "Search crops",
        crop_options,
        index=0,
    )

    if crop != "-- Select a crop --":

        thresholds = CROP_THRESHOLDS[crop]

        st.markdown(
            textwrap.dedent(
                f"""
                <div class="card">

                    <div class="card-title">
                        🌱 {crop}
                    </div>

                    <div class="card-subtitle">
                        Preferred environmental conditions
                    </div>

                </div>
                """
            ),
            unsafe_allow_html=True,
        )

        a, b, c = st.columns(3)

        a.metric(
            "🌡️ Temperature",
            f"{thresholds['temp_c'][0]}–{thresholds['temp_c'][1]} °C",
        )

        b.metric(
            "🌧️ Rainfall",
            f"{thresholds['rain_mm'][0]}–{thresholds['rain_mm'][1]} mm",
        )

        c.metric(
            "🪨 Soil pH",
            f"{thresholds['ph'][0]}–{thresholds['ph'][1]}",
        )

        st.caption(thresholds.get("notes", ""))

    analyze = st.button(
        "🚀 Analyze Location",
        type="primary",
        use_container_width=True,
    )

    # --------------------------------------------------------
    # ANALYZE
    # --------------------------------------------------------

    if analyze:

        if crop == "-- Select a crop --":

            st.warning("Select a crop first.")

        else:

            lat = st.session_state.lat
            lon = st.session_state.lon

            with st.spinner(
                "Fetching NASA POWER and SoilGrids data..."
            ):

                climate = cached_fetch_climate(
                    lat,
                    lon,
                )

                soil = cached_fetch_soil(
                    lat,
                    lon,
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
    # RESULTS
    # --------------------------------------------------------

    analysis = st.session_state.get("analysis")

    if analysis:

        st.divider()

        if analysis["verdict"] == "Suitable":
            result_icon = "🟢"
        elif analysis["verdict"] == "Marginal":
            result_icon = "🟡"
        else:
            result_icon = "🔴"

        st.header(
            f"{result_icon} Result for {analysis['crop']}"
        )

        left, right = st.columns(
            [1, 2],
            gap="large",
        )

        with left:

            st.markdown(
                textwrap.dedent(
                    f"""
                    <div class="score-card">

                        <div class="score-title">
                            SUITABILITY SCORE
                        </div>

                        <div class="score-number">
                            {round(analysis['score'] * 100)}%
                        </div>

                        <div class="score-verdict">
                            {analysis['verdict']}
                        </div>

                    </div>
                    """
                ),
                unsafe_allow_html=True,
            )

        with right:

            st.markdown(
                textwrap.dedent(
                    """
                    <div class="card">

                        <div class="card-title">
                            💡 Why?
                        </div>

                        <div class="card-subtitle">
                            The score is calculated from the
                            available environmental factors.
                        </div>

                    </div>
                    """
                ),
                unsafe_allow_html=True,
            )

            for reason in analysis["reasons"]:
                st.write("•", reason)

        st.subheader("📊 Environmental factors")

        factor_cols = st.columns(3)

        for col, (name, factor) in zip(
            factor_cols,
            analysis["factors"].items(),
        ):

            value = factor["value"]

            if value is None:
                display = "N/A"
            elif name == "Temperature":
                display = f"{value:.1f} °C"
            elif name == "Rainfall":
                display = f"{value:.0f} mm"
            else:
                display = f"{value:.1f}"

            if factor["score"] == 1.0:
                status = "🟢 Within range"
            elif factor["score"] == 0.5:
                status = "🟡 Marginal"
            elif factor["score"] == 0.0:
                status = "🔴 Outside range"
            else:
                status = "⚪ Unavailable"

            with col:

                st.markdown(
                    textwrap.dedent(
                        f"""
                        <div class="factor-card">

                            <div class="factor-title">
                                {name}
                            </div>

                            <div class="factor-value">
                                {display}
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
                        """
                    ),
                    unsafe_allow_html=True,
                )

        st.subheader("🌍 Current environmental data")

        a, b, c, d = st.columns(4)

        a.metric(
            "Temperature",
            (
                f"{analysis['climate']['temp_c']:.1f} °C"
                if analysis["climate"].get("temp_c") is not None
                else "N/A"
            ),
        )

        b.metric(
            "Rainfall",
            (
                f"{analysis['climate']['rain_mm_year']:.0f} mm"
                if analysis["climate"].get("rain_mm_year") is not None
                else "N/A"
            ),
        )

        c.metric(
            "Humidity",
            (
                f"{analysis['climate']['humidity_pct']:.0f}%"
                if analysis["climate"].get("humidity_pct") is not None
                else "N/A"
            ),
        )

        d.metric(
            "Soil pH",
            (
                f"{analysis['soil']['ph']:.1f}"
                if analysis["soil"].get("ph") is not None
                else "N/A"
            ),
        )

        if analysis["climate"].get("error"):
            st.warning(analysis["climate"]["error"])

        if analysis["soil"].get("error"):
            st.warning(analysis["soil"]["error"])


# ============================================================
# CROP FINDER
# ============================================================

elif page == "🌾 Crop Finder":

    st.header("🌾 Crop Finder")

    st.caption(
        "Find crops whose environmental requirements match "
        "the selected location."
    )

    st.markdown(
        textwrap.dedent(
            """
            <div class="card">

                <div class="card-title">
                    🔎 How Crop Finder works
                </div>

                <div class="card-subtitle">
                    The current location is compared with every crop
                    in the database using the same transparent rules
                    as the main analyzer.
                </div>

            </div>
            """
        ),
        unsafe_allow_html=True,
    )

    st.info(
        f"📍 Location: {st.session_state.lat:.5f}, "
        f"{st.session_state.lon:.5f}"
    )

    find_crops = st.button(
        "🌱 Find Matching Crops",
        type="primary",
        use_container_width=True,
    )

    if find_crops:

        with st.spinner(
            "Comparing environmental conditions with all crops..."
        ):

            climate = cached_fetch_climate(
                st.session_state.lat,
                st.session_state.lon,
            )

            soil = cached_fetch_soil(
                st.session_state.lat,
                st.session_state.lon,
            )

            crop_results = []

            for crop_name, thresholds in CROP_THRESHOLDS.items():

                verdict, score, reasons = evaluate(
                    climate,
                    soil,
                    thresholds,
                )

                crop_results.append(
                    {
                        "crop": crop_name,
                        "score": score,
                        "verdict": verdict,
                        "reasons": reasons,
                    }
                )

            crop_results.sort(
                key=lambda x: x["score"],
                reverse=True,
            )

            st.session_state.crop_results = crop_results

    results = st.session_state.get("crop_results")

    if results:

        st.subheader("🌿 Matching crops")

        for i, result in enumerate(results[:10], 1):

            score = round(result["score"] * 100)

            if result["verdict"] == "Suitable":
                icon = "🟢"
            elif result["verdict"] == "Marginal":
                icon = "🟡"
            else:
                icon = "🔴"

            st.markdown(
                textwrap.dedent(
                    f"""
                    <div class="crop-card">

                        <div class="crop-name">
                            {icon} {i}. {result['crop']}
                        </div>

                        <div>
                            {result['verdict']}
                            &nbsp; • &nbsp;
                            <span class="crop-score">
                                {score}%
                            </span>
                        </div>

                    </div>
                    """
                ),
                unsafe_allow_html=True,
            )

        with st.expander("View every crop"):

            for result in results:

                st.write(
                    f"{result['crop']} — "
                    f"{round(result['score'] * 100)}% — "
                    f"{result['verdict']}"
                )

        st.caption(
            "Crop Finder results are environmental screening "
            "matches based on the reference ranges in crop_data.py."
        )


# ============================================================
# DISEASE AI
# ============================================================

elif page == "🔬 Disease AI":

    st.header("🔬 Plant Disease AI")

    st.caption(
        "Upload a leaf image for AI-based disease screening."
    )

    uploaded_photo = st.file_uploader(
        "Upload leaf image",
        type=[
            "jpg",
            "jpeg",
            "png",
            "webp",
        ],
        key="disease_photo",
    )

    if uploaded_photo:

        image = Image.open(uploaded_photo).convert("RGB")

        col1, col2 = st.columns(
            [1, 1],
            gap="large",
        )

        with col1:

            st.image(
                image,
                caption="Uploaded leaf",
                use_container_width=True,
            )

        with col2:

            st.markdown(
                textwrap.dedent(
                    """
                    <div class="card">

                        <div class="card-title">
                            🧠 MobileNetV2 Disease Screening
                        </div>

                        <div class="card-subtitle">
                            The model analyzes the image and returns
                            its most likely plant-disease labels.
                        </div>

                    </div>
                    """
                ),
                unsafe_allow_html=True,
            )

            analyze_disease = st.button(
                "🔬 Analyze Leaf",
                type="primary",
                use_container_width=True,
            )

        if analyze_disease:

            try:

                with st.spinner("Running disease AI..."):

                    model = get_disease_model()

                    predictions = disease_model.predict(
                        image,
                        model,
                        top_k=3,
                    )

                if predictions:

                    top = predictions[0]

                    st.divider()

                    st.subheader("AI prediction")

                    a, b = st.columns(2)

                    a.metric(
                        "Plant",
                        top["plant"],
                    )

                    b.metric(
                        "Confidence",
                        f"{top['confidence'] * 100:.1f}%",
                    )

                    if top["disease"].lower() == "healthy":

                        st.success(
                            f"🌿 Top prediction: "
                            f"**Healthy {top['plant']}**"
                        )

                    else:

                        st.warning(
                            f"⚠️ Top prediction: "
                            f"**{top['disease']}**"
                        )

                    treatment = DISEASE_TREATMENTS.get(
                        top["disease"],
                        DEFAULT_TREATMENT,
                    )

                    st.markdown(
                        textwrap.dedent(
                            f"""
                            <div class="card">

                                <div class="card-title">
                                    💡 Guidance
                                </div>

                                <div>
                                    {treatment}
                                </div>

                            </div>
                            """
                        ),
                        unsafe_allow_html=True,
                    )

                    if len(predictions) > 1:

                        with st.expander("Other predictions"):

                            for prediction in predictions[1:]:

                                st.write(
                                    f"• **{prediction['plant']}** — "
                                    f"{prediction['disease']} "
                                    f"({prediction['confidence'] * 100:.1f}%)"
                                )

                    st.info(
                        "AI screening only: model predictions can "
                        "differ on real-world field photographs."
                    )

                else:

                    st.error("No prediction was returned.")

            except Exception as exc:

                st.error("The disease model could not run.")
                st.code(str(exc))

    else:

        st.info("Upload a clear leaf photo to begin.")


# ============================================================
# ABOUT
# ============================================================

elif page == "ℹ️ About":

    st.header("ℹ️ About CropWise")

    st.markdown(
        """
        ### 🌱 What is CropWise?

        CropWise is an environmental screening platform that
        connects location data with crop requirements.

        ### 📡 Data pipeline

        **Location**

        Latitude + longitude

        ↓

        **Climate**

        NASA POWER

        ↓

        **Soil**

        SoilGrids / ISRIC

        ↓

        **Suitability engine**

        Transparent range-based scoring

        ↓

        **Optional Disease AI**

        MobileNetV2 + PlantVillage

        ---

        ### ⚠️ Important limitations

        The suitability score is a prototype screening indicator.
        It does not predict actual farm yield.

        Real agricultural suitability can also depend on:

        - Soil texture
        - Soil nutrients
        - Salinity
        - Irrigation
        - Sunlight
        - Elevation
        - Season
        - Local varieties
        - Pests and diseases
        - Farming practices

        Disease AI is also a screening tool and should not be
        treated as a definitive diagnosis.
        """
    )


# ============================================================
# FOOTER
# ============================================================

st.markdown(
    textwrap.dedent(
        """
        <div class="footer">
            🌱 CropWise • Team 17 • Reboot the Earth 2026
            <br>
            Environmental screening prototype
        </div>
        """
    ),
    unsafe_allow_html=True,
)
