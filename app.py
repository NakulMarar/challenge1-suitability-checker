import html

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
# CONSTANTS
# ============================================================

DEFAULT_LAT = 25.2854
DEFAULT_LON = 51.5310

PAGES = [
    "🗺️ Analyze Land",
    "🌾 Crop Finder",
    "🔬 Disease AI",
    "ℹ️ About",
]


# ============================================================
# SESSION STATE
# ============================================================

if "lat" not in st.session_state:
    st.session_state.lat = DEFAULT_LAT

if "lon" not in st.session_state:
    st.session_state.lon = DEFAULT_LON

if "page" not in st.session_state:
    st.session_state.page = PAGES[0]

if "last_map_click" not in st.session_state:
    st.session_state.last_map_click = None

if "analysis" not in st.session_state:
    st.session_state.analysis = None

if "crop_results" not in st.session_state:
    st.session_state.crop_results = None

if "disease_results" not in st.session_state:
    st.session_state.disease_results = None


# ============================================================
# HELPERS
# ============================================================

def safe_text(value):
    if value is None:
        return "—"
    return html.escape(str(value))


def render_html(value):
    st.markdown(value, unsafe_allow_html=True)


def score_percent(score):
    if score is None:
        return "—"
    return f"{score * 100:.0f}%"


def verdict_icon(verdict):
    return {
        "Suitable": "🟢",
        "Marginal": "🟡",
        "Not suitable": "🔴",
        "Unknown": "⚪",
    }.get(verdict, "⚪")


def factor_status(score):
    if score is None:
        return "Unavailable"
    if score >= 0.8:
        return "Good"
    if score >= 0.4:
        return "Moderate"
    return "Low"


def format_factor_value(value, unit):
    if value is None:
        return "Unavailable"

    if unit == "°C":
        return f"{value:.1f}°C"

    if unit == "mm/year":
        return f"{value:.0f} mm/year"

    if unit == "pH":
        return f"{value:.2f}"

    return str(value)


def reset_analysis():
    st.session_state.analysis = None
    st.session_state.crop_results = None
    st.session_state.disease_results = None


# ============================================================
# CACHED DATA
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
# CSS
# ============================================================

st.markdown(
    """
    <style>
    .stApp {
        background:
            radial-gradient(circle at top right, rgba(34,197,94,0.08), transparent 30%),
            linear-gradient(180deg, #07110b 0%, #09140e 100%);
    }

    section[data-testid="stSidebar"] {
        background: #07100a;
        border-right: 1px solid rgba(255,255,255,0.08);
    }

    .hero {
        padding: 2rem 0 1.5rem 0;
    }

    .hero-tag {
        color: #86efac;
        font-size: 0.78rem;
        font-weight: 700;
        letter-spacing: 0.12em;
        margin-bottom: 0.5rem;
    }

    .hero-title {
        font-size: 3.2rem;
        font-weight: 800;
        line-height: 1;
        margin: 0;
        color: #f0fdf4;
    }

    .hero-subtitle {
        color: #a7b5aa;
        font-size: 1.05rem;
        margin-top: 0.8rem;
        max-width: 720px;
    }

    .card {
        background: rgba(16, 31, 21, 0.8);
        border: 1px solid rgba(134,239,172,0.12);
        border-radius: 18px;
        padding: 1.25rem;
        margin-bottom: 1rem;
    }

    .metric-card {
        background: rgba(16, 31, 21, 0.8);
        border: 1px solid rgba(134,239,172,0.12);
        border-radius: 16px;
        padding: 1rem;
        min-height: 115px;
    }

    .metric-label {
        color: #9ca89f;
        font-size: 0.8rem;
        margin-bottom: 0.4rem;
    }

    .metric-value {
        color: #f0fdf4;
        font-size: 1.55rem;
        font-weight: 750;
    }

    .metric-sub {
        color: #86efac;
        font-size: 0.78rem;
        margin-top: 0.25rem;
    }

    .score {
        font-size: 3rem;
        font-weight: 800;
        color: #86efac;
    }

    .crop-card {
        background: rgba(16, 31, 21, 0.8);
        border: 1px solid rgba(134,239,172,0.12);
        border-radius: 16px;
        padding: 1rem;
        margin-bottom: 0.8rem;
    }

    .crop-name {
        color: #f0fdf4;
        font-size: 1.1rem;
        font-weight: 700;
    }

    .crop-score {
        color: #86efac;
        font-size: 1.3rem;
        font-weight: 800;
    }

    .factor-title {
        color: #f0fdf4;
        font-weight: 700;
    }

    .factor-range {
        color: #8d9b91;
        font-size: 0.78rem;
    }

    .factor-good {
        color: #86efac;
        font-weight: 700;
    }

    .factor-mid {
        color: #facc15;
        font-weight: 700;
    }

    .factor-low {
        color: #f87171;
        font-weight: 700;
    }

    .footer {
        text-align: center;
        color: #68756d;
        padding: 2rem 0 1rem 0;
        font-size: 0.8rem;
    }

    div[data-testid="stButton"] > button {
        border-radius: 10px;
    }

    div[data-testid="stRadio"] label {
        font-weight: 600;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# HERO
# ============================================================

render_html(
    """
    <div class="hero">
        <div class="hero-tag">REBOOT THE EARTH 2026 • CHALLENGE 1 • TEAM 17</div>
        <div class="hero-title">🌱 CropWise</div>
        <div class="hero-subtitle">
            Smart environmental screening for crop decisions using climate,
            soil and plant-disease data.
        </div>
    </div>
    """
)


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:
    st.markdown("## 🌱 CropWise")
    st.caption("Land & Crop Intelligence")
    st.divider()

    st.markdown("### 🧭 Explore")

    for sidebar_page in PAGES:
        if st.button(
            sidebar_page,
            use_container_width=True,
            type=(
                "primary"
                if st.session_state.page == sidebar_page
                else "secondary"
            ),
            key=f"sidebar_{sidebar_page}",
        ):
            if st.session_state.page != sidebar_page:
                st.session_state.page = sidebar_page
                st.rerun()

    st.divider()

    st.markdown("### 📡 Data")

    st.caption(
        "NASA POWER\n\n"
        "SoilGrids / ISRIC\n\n"
        "OpenStreetMap\n\n"
        "PlantVillage + MobileNetV2"
    )

    st.divider()

    st.caption("Team 17 • Reboot the Earth 2026")


# ============================================================
# TOP NAVIGATION
# ============================================================

page = st.radio(
    "Navigation",
    PAGES,
    index=PAGES.index(st.session_state.page),
    horizontal=True,
    label_visibility="collapsed",
)

if page != st.session_state.page:
    st.session_state.page = page

st.divider()


# ============================================================
# ANALYZE LAND
# ============================================================

if st.session_state.page == "🗺️ Analyze Land":

    st.subheader("🗺️ Analyze Land")
    st.write(
        "Choose a point on the map or enter coordinates manually, "
        "then check how suitable the environment is for a crop."
    )

    # --------------------------------------------------------
    # MAP
    # --------------------------------------------------------

    map_col, control_col = st.columns([1.55, 1], gap="large")

    with map_col:

        m = folium.Map(
            location=[
                st.session_state.lat,
                st.session_state.lon,
            ],
            zoom_start=8,
            control_scale=True,
        )

        folium.Marker(
            [
                st.session_state.lat,
                st.session_state.lon,
            ],
            tooltip="Selected location",
            popup=(
                f"Latitude: {st.session_state.lat:.5f}<br>"
                f"Longitude: {st.session_state.lon:.5f}"
            ),
        ).add_to(m)

        map_data = st_folium(
            m,
            width=None,
            height=450,
            returned_objects=["last_clicked"],
        )

        # ----------------------------------------------------
        # FIXED MAP CLICK HANDLING
        # ----------------------------------------------------

        if map_data and map_data.get("last_clicked"):

            clicked = map_data["last_clicked"]

            new_lat = round(
                float(clicked["lat"]),
                5,
            )

            new_lon = round(
                float(clicked["lng"]),
                5,
            )

            click_key = (
                new_lat,
                new_lon,
            )

            # Only process a genuinely new click.
            # This prevents an old map click from continuously
            # overwriting manually entered coordinates.
            if st.session_state.last_map_click != click_key:

                st.session_state.last_map_click = click_key

                st.session_state.lat = new_lat
                st.session_state.lon = new_lon

                st.session_state.latitude_input = new_lat
                st.session_state.longitude_input = new_lon

                st.rerun()

    # --------------------------------------------------------
    # CONTROLS
    # --------------------------------------------------------

    with control_col:

        st.markdown("### 📍 Location")

        lat = st.number_input(
            "Latitude",
            min_value=-90.0,
            max_value=90.0,
            value=float(st.session_state.lat),
            step=0.01,
            format="%.5f",
            key="latitude_input",
        )

        lon = st.number_input(
            "Longitude",
            min_value=-180.0,
            max_value=180.0,
            value=float(st.session_state.lon),
            step=0.01,
            format="%.5f",
            key="longitude_input",
        )

        st.session_state.lat = lat
        st.session_state.lon = lon

        st.markdown("### 🌾 Crop")

        crop = st.selectbox(
            "Select crop",
            list(CROP_THRESHOLDS.keys()),
        )

        thresholds = CROP_THRESHOLDS[crop]

        render_html(
            f"""
            <div class="card">
                <div class="factor-title">🌱 {safe_text(crop)}</div>
                <br>
                <div class="factor-range">
                    Temperature: {thresholds["temp_c"][0]}–{thresholds["temp_c"][1]} °C
                </div>
                <div class="factor-range">
                    Rainfall: {thresholds["rain_mm"][0]}–{thresholds["rain_mm"][1]} mm/year
                </div>
                <div class="factor-range">
                    Soil pH: {thresholds["ph"][0]}–{thresholds["ph"][1]}
                </div>
            </div>
            """
        )

        st.caption(thresholds["notes"])

        col_a, col_b = st.columns(2)

        with col_a:
            analyze = st.button(
                "🔍 Check this location",
                use_container_width=True,
                type="primary",
            )

        with col_b:
            reset = st.button(
                "↩️ Reset",
                use_container_width=True,
            )

        if reset:
            st.session_state.lat = DEFAULT_LAT
            st.session_state.lon = DEFAULT_LON

            st.session_state.latitude_input = DEFAULT_LAT
            st.session_state.longitude_input = DEFAULT_LON

            st.session_state.last_map_click = None

            reset_analysis()

            st.rerun()

        if analyze:

            climate = cached_fetch_climate(
                float(lat),
                float(lon),
            )

            soil = cached_fetch_soil(
                float(lat),
                float(lon),
            )

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
                "lat": lat,
                "lon": lon,
                "climate": climate,
                "soil": soil,
                "verdict": verdict,
                "score": score,
                "reasons": reasons,
                "factors": factors,
            }

    # --------------------------------------------------------
    # ANALYSIS RESULTS
    # --------------------------------------------------------

    analysis = st.session_state.analysis

    if analysis:

        st.markdown("---")
        st.subheader("📊 Suitability Result")

        verdict = analysis["verdict"]
        score = analysis["score"]

        result_col, info_col = st.columns([1, 2])

        with result_col:

            render_html(
                f"""
                <div class="card">
                    <div class="metric-label">
                        {safe_text(analysis["crop"])}
                    </div>

                    <div class="score">
                        {score_percent(score)}
                    </div>

                    <div style="font-size:1.15rem;font-weight:700;">
                        {verdict_icon(verdict)}
                        {safe_text(verdict)}
                    </div>

                    <div class="factor-range">
                        Screening indicator — not a guaranteed yield prediction.
                    </div>
                </div>
                """
            )

        with info_col:

            climate = analysis["climate"]
            soil = analysis["soil"]

            c1, c2, c3 = st.columns(3)

            with c1:
                render_html(
                    f"""
                    <div class="metric-card">
                        <div class="metric-label">🌡️ Temperature</div>
                        <div class="metric-value">
                            {format_factor_value(climate.get("temp_c"), "°C")}
                        </div>
                    </div>
                    """
                )

            with c2:
                render_html(
                    f"""
                    <div class="metric-card">
                        <div class="metric-label">🌧️ Rainfall</div>
                        <div class="metric-value">
                            {format_factor_value(climate.get("rain_mm_year"), "mm/year")}
                        </div>
                    </div>
                    """
                )

            with c3:
                render_html(
                    f"""
                    <div class="metric-card">
                        <div class="metric-label">🪨 Soil pH</div>
                        <div class="metric-value">
                            {format_factor_value(soil.get("ph"), "pH")}
                        </div>
                    </div>
                    """
                )

        st.markdown("### 🔎 Factor Breakdown")

        factors = analysis["factors"]

        for factor_name, factor in factors.items():

            score_value = factor["score"]
            status = factor_status(score_value)

            if score_value is None:
                status_class = "factor-range"
            elif score_value >= 0.8:
                status_class = "factor-good"
            elif score_value >= 0.4:
                status_class = "factor-mid"
            else:
                status_class = "factor-low"

            value_text = format_factor_value(
                factor["value"],
                factor["unit"],
            )

            render_html(
                f"""
                <div class="card">
                    <div style="display:flex;justify-content:space-between;">
                        <div>
                            <div class="factor-title">
                                {safe_text(factor_name)}
                            </div>
                            <div class="factor-range">
                                Preferred:
                                {factor["low"]}–{factor["high"]}
                                {safe_text(factor["unit"])}
                            </div>
                        </div>

                        <div style="text-align:right;">
                            <div class="{status_class}">
                                {safe_text(status)}
                            </div>
                            <div style="font-weight:700;">
                                {safe_text(value_text)}
                                &nbsp;•&nbsp;
                                {score_percent(score_value)}
                            </div>
                        </div>
                    </div>
                </div>
                """
            )

        st.markdown("### 💡 Why this result?")

        for reason in analysis["reasons"]:
            st.write(f"• {reason}")

        if analysis["climate"].get("error"):
            st.warning(
                analysis["climate"]["error"]
            )

        if analysis["soil"].get("error"):
            st.warning(
                analysis["soil"]["error"]
            )


# ============================================================
# CROP FINDER
# ============================================================

elif st.session_state.page == "🌾 Crop Finder":

    st.subheader("🌾 Crop Finder")

    st.write(
        "Compare the available crops at your selected location "
        "using the same transparent environmental screening model."
    )

    lat = st.session_state.lat
    lon = st.session_state.lon

    st.info(
        f"📍 Current location: "
        f"{lat:.5f}, {lon:.5f}"
    )

    filter_option = st.selectbox(
        "Show",
        [
            "All crops",
            "Suitable only",
            "Suitable + Marginal",
        ],
    )

    if st.button(
        "🌾 Find suitable crops",
        use_container_width=True,
        type="primary",
    ):

        climate = cached_fetch_climate(
            float(lat),
            float(lon),
        )

        soil = cached_fetch_soil(
            float(lat),
            float(lon),
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
                    "notes": thresholds["notes"],
                }
            )

        results.sort(
            key=lambda item: item["score"],
            reverse=True,
        )

        st.session_state.crop_results = {
            "results": results,
            "climate": climate,
            "soil": soil,
            "lat": lat,
            "lon": lon,
        }

    finder = st.session_state.get("crop_results")

    if isinstance(finder, dict):

        results = finder.get("results", [])

        if filter_option == "Suitable only":
            results = [
                item
                for item in results
                if item["verdict"] == "Suitable"
            ]

        elif filter_option == "Suitable + Marginal":
            results = [
                item
                for item in results
                if item["verdict"]
                in ("Suitable", "Marginal")
            ]

        st.markdown("### 🏆 Crop Matches")

        if not results:
            st.warning(
                "No crops match the selected filter."
            )
        else:

            for rank, item in enumerate(
                results[:15],
                start=1,
            ):

                render_html(
                    f"""
                    <div class="crop-card">
                        <div style="
                            display:flex;
                            justify-content:space-between;
                            align-items:center;
                        ">
                            <div>
                                <span style="
                                    color:#86efac;
                                    font-weight:700;
                                ">
                                    #{rank}
                                </span>
                                &nbsp;
                                <span class="crop-name">
                                    {safe_text(item["crop"])}
                                </span>
                            </div>

                            <div>
                                <span class="crop-score">
                                    {score_percent(item["score"])}
                                </span>
                                &nbsp;
                                {verdict_icon(item["verdict"])}
                                {safe_text(item["verdict"])}
                            </div>
                        </div>

                        <div class="factor-range" style="margin-top:0.5rem;">
                            {safe_text(item["notes"])}
                        </div>
                    </div>
                    """
                )

        climate = finder.get("climate", {})
        soil = finder.get("soil", {})

        st.markdown("### 🌍 Environmental Conditions")

        c1, c2, c3 = st.columns(3)

        with c1:
            render_html(
                f"""
                <div class="metric-card">
                    <div class="metric-label">🌡️ Temperature</div>
                    <div class="metric-value">
                        {format_factor_value(climate.get("temp_c"), "°C")}
                    </div>
                </div>
                """
            )

        with c2:
            render_html(
                f"""
                <div class="metric-card">
                    <div class="metric-label">🌧️ Rainfall</div>
                    <div class="metric-value">
                        {format_factor_value(climate.get("rain_mm_year"), "mm/year")}
                    </div>
                </div>
                """
            )

        with c3:
            render_html(
                f"""
                <div class="metric-card">
                    <div class="metric-label">🪨 Soil pH</div>
                    <div class="metric-value">
                        {format_factor_value(soil.get("ph"), "pH")}
                    </div>
                </div>
                """
            )


# ============================================================
# DISEASE AI
# ============================================================

elif st.session_state.page == "🔬 Disease AI":

    st.subheader("🔬 Plant Disease AI")

    st.write(
        "Upload a plant leaf image and the PlantVillage-trained "
        "MobileNetV2 model will return its top predictions."
    )

    uploaded_file = st.file_uploader(
        "Upload a leaf image",
        type=[
            "jpg",
            "jpeg",
            "png",
            "webp",
        ],
    )

    if uploaded_file:

        image = Image.open(uploaded_file)

        col_image, col_result = st.columns(
            [1, 1.3],
            gap="large",
        )

        with col_image:

            st.image(
                image,
                caption="Uploaded image",
                use_container_width=True,
            )

        with col_result:

            if st.button(
                "🔬 Analyze leaf",
                use_container_width=True,
                type="primary",
            ):

                try:

                    model = get_disease_model()

                    predictions = disease_model.predict(
                        image,
                        model,
                        top_k=3,
                    )

                    st.session_state.disease_results = predictions

                except Exception as exc:

                    st.error(
                        f"Disease model failed: {exc}"
                    )

    predictions = st.session_state.get(
        "disease_results"
    )

    if predictions:

        st.markdown("### 🧠 Prediction")

        top = predictions[0]

        confidence = top["confidence"]

        render_html(
            f"""
            <div class="card">
                <div class="metric-label">Detected plant</div>
                <div class="metric-value">
                    {safe_text(top["plant"])}
                </div>

                <br>

                <div class="metric-label">Most likely condition</div>
                <div style="
                    color:#f0fdf4;
                    font-size:1.35rem;
                    font-weight:750;
                ">
                    {safe_text(top["disease"])}
                </div>

                <br>

                <div class="metric-label">Confidence</div>
                <div class="score">
                    {confidence * 100:.1f}%
                </div>
            </div>
            """
        )

        treatment = DISEASE_TREATMENTS.get(
            top["disease"],
            DEFAULT_TREATMENT,
        )

        st.markdown("### 🩺 Treatment / Management")

        render_html(
            f"""
            <div class="card">
                {safe_text(treatment)}
            </div>
            """
        )

        if confidence < 0.60:
            st.warning(
                "The model has relatively low confidence in this "
                "prediction. Treat this as a screening result and "
                "verify the diagnosis before taking action."
            )
        else:
            st.info(
                "AI prediction only — verify plant disease diagnosis "
                "with appropriate agricultural guidance before treatment."
            )

        if len(predictions) > 1:

            st.markdown("### 🔎 Other possibilities")

            for prediction in predictions[1:]:

                st.write(
                    f"• **{prediction['plant']}** — "
                    f"{prediction['disease']} "
                    f"({prediction['confidence'] * 100:.1f}%)"
                )


# ============================================================
# ABOUT
# ============================================================

elif st.session_state.page == "ℹ️ About":

    st.subheader("ℹ️ About CropWise")

    st.write(
        "CropWise is a transparent environmental screening tool "
        "built for Reboot the Earth 2026 — Challenge 1."
    )

    st.markdown("### 🌍 Data Pipeline")

    render_html(
        """
        <div class="card">
            <b>🌦️ NASA POWER</b><br>
            Long-term climate information including temperature,
            precipitation and relative humidity.
            <br><br>

            <b>🪨 SoilGrids / ISRIC</b><br>
            Soil pH information for the selected location.
            <br><br>

            <b>🗺️ OpenStreetMap</b><br>
            Map visualization and geographic context.
            <br><br>

            <b>🔬 PlantVillage + MobileNetV2</b><br>
            Plant leaf disease classification.
        </div>
        """
    )

    st.markdown("### 🧠 Suitability Method")

    st.write(
        "Each crop is evaluated against three environmental factors:"
    )

    st.write(
        "• Temperature\n"
        "\n"
        "• Annual rainfall\n"
        "\n"
        "• Soil pH"
    )

    st.write(
        "The available factors receive equal weight. "
        "The resulting score is a screening indicator and should "
        "not be interpreted as a guaranteed agricultural yield prediction."
    )

    st.markdown("### ⚠️ Limitations")

    st.write(
        "Crop thresholds are reference ranges and may vary by "
        "cultivar, season, irrigation, local soil conditions, "
        "management practices and other environmental factors."
    )

    st.write(
        "Disease AI predictions should also be treated as screening "
        "results rather than definitive diagnoses."
    )

    st.markdown("### 💚 Team")

    st.write(
        "Team 17 • Reboot the Earth 2026"
    )


# ============================================================
# FOOTER
# ============================================================

st.markdown(
    """
    <div class="footer">
        🌱 CropWise • Team 17 • Reboot the Earth 2026
    </div>
    """,
    unsafe_allow_html=True,
)
