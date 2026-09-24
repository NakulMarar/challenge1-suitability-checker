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


# ============================================================
# SESSION STATE
# ============================================================

if "lat" not in st.session_state:
    st.session_state.lat = DEFAULT_LAT

if "lon" not in st.session_state:
    st.session_state.lon = DEFAULT_LON

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
    """Safely escape text before inserting it into HTML."""
    return html.escape(str(value))


def render_html(content):
    """Render compact custom HTML."""
    st.markdown(
        "\n".join(
            line.strip()
            for line in content.splitlines()
            if line.strip()
        ),
        unsafe_allow_html=True,
    )


def score_percent(score):
    if score is None:
        return 0

    return max(
        0,
        min(
            100,
            round(float(score) * 100),
        ),
    )


def verdict_icon(verdict):
    return {
        "Suitable": "🟢",
        "Marginal": "🟡",
        "Not suitable": "🔴",
        "Unknown": "⚪",
    }.get(verdict, "⚪")


def factor_status(score):
    if score is None:
        return "⚪ Unavailable", "unavailable"

    if score >= 1.0:
        return "🟢 Within range", "good"

    if score >= 0.5:
        return "🟡 Marginal", "warning"

    return "🔴 Outside range", "bad"


def format_factor_value(name, value):
    if value is None:
        return "N/A"

    if name == "Temperature":
        return f"{value:.1f} °C"

    if name == "Rainfall":
        return f"{value:.0f} mm/year"

    if name == "Soil pH":
        return f"{value:.1f}"

    return str(value)


def reset_analysis():
    st.session_state.analysis = None
    st.session_state.crop_results = None
    st.session_state.disease_results = None


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
# CSS
# ============================================================

st.markdown(
    """
<style>

.stApp {
    background: #080b09;
    color: #f2f5f3;
}

.main .block-container {
    max-width: 1450px;
    padding-top: 1.2rem;
    padding-bottom: 3rem;
}

h1, h2, h3, h4 {
    color: #f4f7f5 !important;
}

p {
    color: #c7d1cb;
}

hr {
    border-color: #202c24 !important;
}


/* SIDEBAR */

[data-testid="stSidebar"] {
    background: #0d120f !important;
    border-right: 1px solid #202c24;
}

[data-testid="stSidebar"] * {
    color: #e8eee9 !important;
}


/* HERO */

.hero {
    background:
        radial-gradient(
            circle at 85% 20%,
            rgba(62, 224, 125, 0.18),
            transparent 35%
        ),
        linear-gradient(
            135deg,
            #06150c,
            #0b4d2c
        );

    border: 1px solid #1d5a38;
    border-radius: 24px;
    padding: 34px;
    margin-bottom: 24px;

    box-shadow:
        0 12px 40px rgba(0,0,0,.42);
}

.hero h1 {
    font-size: 46px;
    font-weight: 850;
    margin: 10px 0 5px;
    color: white !important;
}

.hero p {
    color: #cdebd8 !important;
    font-size: 17px;
    max-width: 850px;
}

.badge {
    display: inline-block;
    color: #7ff0a7 !important;
    background: rgba(32,180,93,.15);
    border: 1px solid rgba(32,180,93,.32);
    padding: 6px 12px;
    border-radius: 999px;
    font-size: 12px;
    font-weight: 750;
}


/* CARDS */

.card {
    background: #101612;
    border: 1px solid #202c24;
    border-radius: 18px;
    padding: 20px;
    margin-bottom: 15px;

    box-shadow:
        0 5px 20px rgba(0,0,0,.25);
}

.card-title {
    color: #f2f5f3 !important;
    font-size: 18px;
    font-weight: 800;
}

.card-subtitle {
    color: #91a49a !important;
    font-size: 13px;
    margin-top: 5px;
}


/* STEP CARDS */

.step {
    background: #101612;
    border: 1px solid #202c24;
    border-radius: 16px;
    padding: 15px;
    height: 100%;
}

.step-number {
    color: #38d878;
    font-weight: 850;
    font-size: 13px;
}

.step-title {
    font-weight: 800;
    color: #f4f7f5;
    margin-top: 5px;
}


/* SCORE */

.score-card {
    background:
        radial-gradient(
            circle at 50% 0%,
            rgba(56,216,120,.12),
            transparent 55%
        ),
        #101612;

    border: 1px solid #202c24;
    border-radius: 20px;
    padding: 28px;
    text-align: center;
}

.score-title {
    color: #91a49a;
    font-size: 12px;
    font-weight: 800;
    letter-spacing: 1.2px;
}

.score-number {
    color: #38d878;
    font-size: 55px;
    font-weight: 900;
    margin: 5px 0;
}

.score-verdict {
    color: #f4f7f5;
    font-size: 19px;
    font-weight: 800;
}


/* FACTORS */

.factor-card {
    background: #101612;
    border: 1px solid #202c24;
    border-radius: 17px;
    padding: 19px;
    min-height: 175px;
}

.factor-title {
    color: #dce8df;
    font-weight: 800;
}

.factor-value {
    color: white;
    font-size: 26px;
    font-weight: 850;
    margin: 8px 0;
}

.factor-range {
    color: #82958b;
    font-size: 12px;
}

.progress {
    height: 8px;
    background: #1d2921;
    border-radius: 999px;
    overflow: hidden;
    margin: 12px 0;
}

.progress-bar {
    height: 100%;
    background: linear-gradient(
        90deg,
        #1eaa5b,
        #55e98c
    );
    border-radius: 999px;
}


/* CROP CARDS */

.crop-card {
    background: #101612;
    border: 1px solid #202c24;
    border-radius: 16px;
    padding: 17px;
    margin-bottom: 10px;
}

.crop-name {
    color: #f4f7f5;
    font-size: 17px;
    font-weight: 850;
}

.crop-score {
    color: #38d878;
    font-weight: 850;
}


/* NAV */

div[role="radiogroup"] {
    background: #101612;
    border: 1px solid #202c24;
    border-radius: 16px;
    padding: 7px;
    gap: 5px;
}

div[role="radiogroup"] label {
    border-radius: 10px;
    padding: 9px 13px;
    color: #dce8df !important;
    font-weight: 700;
}

div[role="radiogroup"] label:hover {
    background: #18241c !important;
}


/* INPUTS */

input {
    background: #101612 !important;
    color: white !important;
}

div[data-baseweb="select"] > div {
    background: #101612 !important;
    border-color: #29372e !important;
}


/* BUTTONS */

.stButton > button {
    border-radius: 11px !important;
    font-weight: 800 !important;
    min-height: 44px;
}


/* MAP */

iframe {
    border-radius: 17px !important;
}


/* FOOTER */

.footer {
    text-align: center;
    color: #66786d !important;
    font-size: 12px;
    padding-top: 35px;
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
<span class="badge">REBOOT THE EARTH 2026 • CHALLENGE 1 • TEAM 17</span>
<h1>🌱 CropWise</h1>
<p>
Smart environmental screening for crop decisions.
Choose a location, compare crops with local conditions,
and optionally screen a leaf image for disease.
</p>
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

    st.write("🗺️ Analyze Land")
    st.write("🌾 Crop Finder")
    st.write("🔬 Disease AI")
    st.write("ℹ️ About")

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
        "Start with a location, select a crop, then analyze "
        "the environmental conditions."
    )

    # --------------------------------------------------------
    # WORKFLOW
    # --------------------------------------------------------

    step_cols = st.columns(3)

    with step_cols[0]:
        render_html(
            """
<div class="step">
<div class="step-number">STEP 01</div>
<div class="step-title">📍 Choose location</div>
<div class="card-subtitle">Click the map or enter coordinates.</div>
</div>
"""
        )

    with step_cols[1]:
        render_html(
            """
<div class="step">
<div class="step-number">STEP 02</div>
<div class="step-title">🌾 Choose crop</div>
<div class="card-subtitle">Select a crop from the database.</div>
</div>
"""
        )

    with step_cols[2]:
        render_html(
            """
<div class="step">
<div class="step-number">STEP 03</div>
<div class="step-title">🚀 Analyze</div>
<div class="card-subtitle">Compare climate and soil conditions.</div>
</div>
"""
        )

    st.write("")

    map_col, location_col = st.columns(
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
            tiles="OpenStreetMap",
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
            icon=folium.Icon(
                color="green",
                icon="leaf",
                prefix="fa",
            ),
        ).add_to(m)

        map_data = st_folium(
            m,
            height=440,
            use_container_width=True,
            key="main_land_map",
        )

        if map_data and map_data.get("last_clicked"):

            st.session_state.lat = round(
                float(map_data["last_clicked"]["lat"]),
                5,
            )

            st.session_state.lon = round(
                float(map_data["last_clicked"]["lng"]),
                5,
            )

            st.rerun()

    # --------------------------------------------------------
    # LOCATION PANEL
    # --------------------------------------------------------

    with location_col:

        render_html(
            """
<div class="card">
<div class="card-title">📍 Selected location</div>
<div class="card-subtitle">
Use the map or type coordinates manually.
</div>
</div>
"""
        )

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

        st.success(
            f"📍 {lat:.5f}, {lon:.5f}"
        )

        if st.button(
            "↩️ Reset location",
            use_container_width=True,
        ):
            st.session_state.lat = DEFAULT_LAT
            st.session_state.lon = DEFAULT_LON
            reset_analysis()
            st.rerun()

    st.divider()

    # --------------------------------------------------------
    # CROP
    # --------------------------------------------------------

    st.header("🌾 Select a crop")

    crop_options = [
        "-- Select a crop --"
    ] + sorted(CROP_THRESHOLDS.keys())

    crop = st.selectbox(
        "Search and select crop",
        crop_options,
        index=0,
        help="Choose the crop you want to screen.",
    )

    if crop != "-- Select a crop --":

        thresholds = CROP_THRESHOLDS[crop]

        render_html(
            f"""
<div class="card">
<div class="card-title">🌱 {safe_text(crop)}</div>
<div class="card-subtitle">
Reference environmental conditions
</div>
</div>
"""
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

        if thresholds.get("notes"):
            st.info(
                f"💡 {thresholds['notes']}"
            )

    analyze = st.button(
        "🚀 Analyze This Location",
        type="primary",
        use_container_width=True,
    )

    if analyze:

        if crop == "-- Select a crop --":

            st.warning(
                "🌾 Please select a crop before starting the analysis."
            )

        else:

            lat = float(st.session_state.lat)
            lon = float(st.session_state.lon)

            reset_analysis()

            with st.spinner(
                "🌍 Fetching climate and soil data..."
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
                "lat": lat,
                "lon": lon,
                "climate": climate,
                "soil": soil,
                "thresholds": thresholds,
                "verdict": verdict,
                "score": score,
                "reasons": reasons,
                "factors": factors,
            }

            st.success("Analysis complete.")


    # ========================================================
    # RESULTS
    # ========================================================

    analysis = st.session_state.get("analysis")

    if analysis:

        st.divider()

        icon = verdict_icon(
            analysis["verdict"]
        )

        st.header(
            f"{icon} {analysis['crop']} screening result"
        )

        st.caption(
            f"📍 {analysis['lat']:.5f}, "
            f"{analysis['lon']:.5f}"
        )

        left, right = st.columns(
            [1, 2],
            gap="large",
        )

        with left:

            render_html(
                f"""
<div class="score-card">
<div class="score-title">SUITABILITY SCORE</div>
<div class="score-number">
{score_percent(analysis['score'])}%
</div>
<div class="score-verdict">
{safe_text(analysis['verdict'])}
</div>
</div>
"""
            )

            st.write("")

            if analysis["verdict"] == "Suitable":
                st.success(
                    "Most available environmental factors "
                    "fall within the reference ranges."
                )

            elif analysis["verdict"] == "Marginal":
                st.warning(
                    "Some environmental factors are outside "
                    "their preferred ranges."
                )

            elif analysis["verdict"] == "Not suitable":
                st.error(
                    "Several environmental factors are outside "
                    "the reference ranges."
                )

            else:
                st.info(
                    "There is not enough environmental data "
                    "to calculate a meaningful screening result."
                )

        with right:

            render_html(
                """
<div class="card">
<div class="card-title">💡 Why this score?</div>
<div class="card-subtitle">
Each available factor is compared with the crop's
reference range using transparent rules.
</div>
</div>
"""
            )

            for reason in analysis["reasons"]:
                st.write("•", reason)

        # ----------------------------------------------------
        # FACTORS
        # ----------------------------------------------------

        st.subheader("📊 Environmental match")

        factor_cols = st.columns(3)

        for col, (name, factor) in zip(
            factor_cols,
            analysis["factors"].items(),
        ):

            value = factor["value"]
            percentage = score_percent(
                factor["score"]
            )

            status, _ = factor_status(
                factor["score"]
            )

            display_value = format_factor_value(
                name,
                value,
            )

            with col:

                render_html(
                    f"""
<div class="factor-card">
<div class="factor-title">
{safe_text(name)}
</div>

<div class="factor-value">
{safe_text(display_value)}
</div>

<div class="factor-range">
Preferred:
{factor['low']} – {factor['high']}
{safe_text(factor['unit'])}
</div>

<div class="progress">
<div class="progress-bar"
style="width:{percentage}%">
</div>
</div>

<strong>{safe_text(status)}</strong>
</div>
"""
                )

        # ----------------------------------------------------
        # RAW DATA
        # ----------------------------------------------------

        st.subheader("🌍 Environmental data")

        climate = analysis["climate"]
        soil = analysis["soil"]

        a, b, c, d = st.columns(4)

        a.metric(
            "🌡️ Temperature",
            (
                f"{climate['temp_c']:.1f} °C"
                if climate.get("temp_c") is not None
                else "N/A"
            ),
        )

        b.metric(
            "🌧️ Annual rainfall",
            (
                f"{climate['rain_mm_year']:.0f} mm"
                if climate.get("rain_mm_year") is not None
                else "N/A"
            ),
        )

        c.metric(
            "💧 Humidity",
            (
                f"{climate['humidity_pct']:.0f}%"
                if climate.get("humidity_pct") is not None
                else "N/A"
            ),
        )

        d.metric(
            "🪨 Soil pH",
            (
                f"{soil['ph']:.1f}"
                if soil.get("ph") is not None
                else "N/A"
            ),
        )

        if climate.get("error"):
            st.warning(
                f"NASA POWER: {climate['error']}"
            )

        if soil.get("error"):
            st.warning(
                f"SoilGrids: {soil['error']}"
            )

        with st.expander("ℹ️ How the score is calculated"):

            st.markdown(
                """
**1. Temperature**

The measured value is compared with the crop's
preferred temperature range.

**2. Rainfall**

Annual rainfall is compared with the crop's
reference rainfall range.

**3. Soil pH**

The measured soil pH is compared with the crop's
preferred pH range.

Each available factor contributes equally.

- 🟢 Inside range = full factor score
- 🟡 Slightly outside = partial factor score
- 🔴 Further outside = zero factor score
- ⚪ Missing = excluded from the calculation

The final number is a **screening indicator**, not a
prediction of farm yield.
"""
            )


# ============================================================
# CROP FINDER
# ============================================================

elif page == "🌾 Crop Finder":

    st.header("🌾 Crop Finder")

    st.caption(
        "Compare the selected location against every crop "
        "in the CropWise reference database."
    )

    render_html(
        f"""
<div class="card">
<div class="card-title">📍 Current location</div>
<div class="card-subtitle">
{st.session_state.lat:.5f}, {st.session_state.lon:.5f}
</div>
</div>
"""
    )

    find_crops = st.button(
        "🌱 Find Matching Crops",
        type="primary",
        use_container_width=True,
    )

    if find_crops:

        with st.spinner(
            "Comparing climate and soil conditions..."
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
                key=lambda item: item["score"],
                reverse=True,
            )

            st.session_state.crop_results = {
                "results": crop_results,
                "climate": climate,
                "soil": soil,
            }

    finder = st.session_state.get(
        "crop_results"
    )

    if finder:

        results = finder["results"]

        st.subheader("🌿 Crop matches")

        # ----------------------------------------------------
        # FILTER
        # ----------------------------------------------------

        show_only = st.selectbox(
            "Show",
            [
                "All crops",
                "Suitable only",
                "Suitable + Marginal",
            ],
        )

        filtered = results

        if show_only == "Suitable only":

            filtered = [
                item
                for item in results
                if item["verdict"] == "Suitable"
            ]

        elif show_only == "Suitable + Marginal":

            filtered = [
                item
                for item in results
                if item["verdict"]
                in ["Suitable", "Marginal"]
            ]

        if not filtered:

            st.info(
                "No crops match this filter at the selected location."
            )

        else:

            for index, result in enumerate(
                filtered[:15],
                1,
            ):

                score = score_percent(
                    result["score"]
                )

                icon = verdict_icon(
                    result["verdict"]
                )

                render_html(
                    f"""
<div class="crop-card">
<div class="crop-name">
{icon} {index}. {safe_text(result['crop'])}
</div>

<div style="margin-top:6px;">
{safe_text(result['verdict'])}
&nbsp; • &nbsp;
<span class="crop-score">{score}% match</span>
</div>

<div class="progress">
<div class="progress-bar"
style="width:{score}%">
</div>
</div>
</div>
"""
                )

            if len(filtered) > 15:

                st.caption(
                    f"Showing 15 of {len(filtered)} matching results."
                )

        # ----------------------------------------------------
        # DATA
        # ----------------------------------------------------

        with st.expander(
            "🌍 Environmental data used"
        ):

            climate = finder["climate"]
            soil = finder["soil"]

            a, b, c, d = st.columns(4)

            a.metric(
                "Temperature",
                (
                    f"{climate['temp_c']:.1f} °C"
                    if climate.get("temp_c") is not None
                    else "N/A"
                ),
            )

            b.metric(
                "Rainfall",
                (
                    f"{climate['rain_mm_year']:.0f} mm"
                    if climate.get("rain_mm_year") is not None
                    else "N/A"
                ),
            )

            c.metric(
                "Humidity",
                (
                    f"{climate['humidity_pct']:.0f}%"
                    if climate.get("humidity_pct") is not None
                    else "N/A"
                ),
            )

            d.metric(
                "Soil pH",
                (
                    f"{soil['ph']:.1f}"
                    if soil.get("ph") is not None
                    else "N/A"
                ),
            )

        st.caption(
            "Crop Finder uses the same transparent reference-range "
            "screening system as Analyze Land."
        )


# ============================================================
# DISEASE AI
# ============================================================

elif page == "🔬 Disease AI":

    st.header("🔬 Plant Disease AI")

    st.caption(
        "Upload a clear leaf image for AI-based disease screening."
    )

    render_html(
        """
<div class="card">
<div class="card-title">🧠 How it works</div>
<div class="card-subtitle">
The uploaded image is processed locally by the
PlantVillage-trained MobileNetV2 classifier.
The model returns its highest-probability labels.
</div>
</div>
"""
    )

    uploaded_photo = st.file_uploader(
        "📷 Upload leaf image",
        type=[
            "jpg",
            "jpeg",
            "png",
            "webp",
        ],
        key="disease_photo",
    )

    if uploaded_photo:

        try:

            image = Image.open(
                uploaded_photo
            ).convert("RGB")

        except Exception:

            st.error(
                "The uploaded file could not be read as an image."
            )

            st.stop()

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

            st.markdown("### 🔬 Ready to analyze")

            st.caption(
                "For better results, use a clear image where "
                "the leaf is visible and well lit."
            )

            analyze_disease = st.button(
                "🔬 Analyze Leaf",
                type="primary",
                use_container_width=True,
            )

        if analyze_disease:

            try:

                with st.spinner(
                    "Running disease AI..."
                ):

                    model = get_disease_model()

                    predictions = disease_model.predict(
                        image,
                        model,
                        top_k=3,
                    )

                st.session_state.disease_results = predictions

            except Exception as exc:

                st.session_state.disease_results = None

                st.error(
                    "The disease model could not run."
                )

                with st.expander(
                    "Technical error"
                ):
                    st.code(
                        str(exc)
                    )

    predictions = st.session_state.get(
        "disease_results"
    )

    if predictions:

        top = predictions[0]

        st.divider()

        st.subheader("🧠 AI screening result")

        a, b = st.columns(2)

        a.metric(
            "Plant",
            top["plant"],
        )

        b.metric(
            "Confidence",
            f"{top['confidence'] * 100:.1f}%",
        )

        confidence = score_percent(
            top["confidence"]
        )

        render_html(
            f"""
<div class="factor-card">
<div class="factor-title">Prediction confidence</div>
<div class="factor-value">{confidence}%</div>

<div class="progress">
<div class="progress-bar"
style="width:{confidence}%">
</div>
</div>

<div class="factor-range">
Model confidence is not the same as diagnostic certainty.
</div>
</div>
"""
        )

        disease_name = top["disease"]

        if disease_name.lower() == "healthy":

            st.success(
                f"🌿 Top prediction: **Healthy {top['plant']}**"
            )

        else:

            st.warning(
                f"⚠️ Top prediction: **{disease_name}**"
            )

        treatment = DISEASE_TREATMENTS.get(
            disease_name,
            DEFAULT_TREATMENT,
        )

        render_html(
            f"""
<div class="card">
<div class="card-title">💡 General guidance</div>
<div style="margin-top:8px;">
{safe_text(treatment)}
</div>
</div>
"""
        )

        if len(predictions) > 1:

            st.subheader("🔎 Other model predictions")

            for prediction in predictions[1:]:

                st.write(
                    f"• **{prediction['plant']}** — "
                    f"{prediction['disease']} "
                    f"({prediction['confidence'] * 100:.1f}%)"
                )

        st.info(
            "⚠️ This is an AI screening tool. Real-world field "
            "photos can produce incorrect predictions. Consider "
            "local agricultural or plant-diagnostic guidance "
            "before taking treatment action."
        )


# ============================================================
# ABOUT
# ============================================================

elif page == "ℹ️ About":

    st.header("ℹ️ About CropWise")

    render_html(
        """
<div class="card">
<div class="card-title">🌱 What is CropWise?</div>
<div class="card-subtitle">
CropWise is an environmental screening prototype that
connects location data with crop requirements and optional
plant-disease image screening.
</div>
</div>
"""
    )

    st.subheader("📡 Data pipeline")

    pipeline = st.columns(5)

    pipeline_data = [
        ("📍", "Location", "Latitude + longitude"),
        ("🌡️", "Climate", "NASA POWER"),
        ("🪨", "Soil", "SoilGrids / ISRIC"),
        ("🌾", "Suitability", "Transparent scoring"),
        ("🔬", "Disease AI", "MobileNetV2"),
    ]

    for col, item in zip(
        pipeline,
        pipeline_data,
    ):

        icon, title, description = item

        with col:

            render_html(
                f"""
<div class="step">
<div style="font-size:25px;">{icon}</div>
<div class="step-title">{title}</div>
<div class="card-subtitle">
{description}
</div>
</div>
"""
            )

    st.divider()

    st.subheader("⚠️ Important limitations")

    st.markdown(
        """
CropWise provides **screening indicators**, not guaranteed
farm outcomes or yield predictions.

Actual agricultural suitability can also depend on:

- Soil texture
- Soil nutrients
- Salinity
- Irrigation
- Sunlight
- Elevation
- Season
- Local crop varieties
- Pests and diseases
- Farming practices
- Local weather conditions

The disease classifier is also an AI screening tool and can
make mistakes, particularly with field photographs that differ
from its training data.
"""
    )

    st.subheader("🧪 Scoring approach")

    st.markdown(
        """
CropWise compares three environmental factors:

**Temperature + rainfall + soil pH**

Available factors receive equal weight.

The system is intentionally transparent so users can see
which environmental conditions contributed to the result.
"""
    )


# ============================================================
# FOOTER
# ============================================================

st.divider()

render_html(
    """
<div class="footer">
🌱 CropWise • Team 17 • Reboot the Earth 2026
<br>
Environmental screening prototype
</div>
"""
)
