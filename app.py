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
from disease_model import load_model, predict


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="CropWise | Reboot the Earth 2026",
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

if "page" not in st.session_state:
    st.session_state.page = PAGES[0]

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

if "last_map_click" not in st.session_state:
    st.session_state.last_map_click = None

if "latitude_input" not in st.session_state:
    st.session_state.latitude_input = DEFAULT_LAT

if "longitude_input" not in st.session_state:
    st.session_state.longitude_input = DEFAULT_LON


# ============================================================
# HELPERS
# ============================================================

def safe_text(value):
    if value is None:
        return "—"
    return html.escape(str(value))


def score_percent(score):
    if score is None:
        return 0
    return int(round(float(score) * 100))


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
    if score >= 0.5:
        return "Moderate"
    return "Poor"


def format_factor_value(value, unit):
    if value is None:
        return "Unavailable"
    if unit == "°C":
        return f"{value:.1f} °C"
    if unit == "mm/year":
        return f"{value:,.0f} mm/year"
    if unit == "pH":
        return f"{value:.2f}"
    return str(value)


def reset_analysis():
    st.session_state.analysis = None
    st.session_state.crop_results = None
    st.session_state.disease_results = None


# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown(
    """
    <style>

    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 2rem;
        max-width: 1400px;
    }

    .hero {
        padding: 1.5rem 1.7rem;
        border-radius: 22px;
        background: linear-gradient(
            135deg,
            #e8f5e9 0%,
            #f7fff8 50%,
            #e0f2f1 100%
        );
        border: 1px solid #c8e6c9;
        margin-bottom: 1rem;
    }

    .hero h1 {
        margin: 0;
        font-size: 2.4rem;
        font-weight: 800;
        color: #1b4332 !important;
        opacity: 1 !important;
        visibility: visible !important;
    }

    .hero p {
        margin-top: 0.45rem;
        margin-bottom: 0;
        color: #48604f !important;
        font-size: 1.05rem;
        opacity: 1 !important;
        visibility: visible !important;
    }

    .metric-card {
        padding: 1rem;
        border-radius: 16px;
        border: 1px solid #e0e0e0;
        background: white;
        min-height: 120px;
    }

    .metric-title {
        font-size: 0.85rem;
        color: #666;
        margin-bottom: 0.25rem;
    }

    .metric-value {
        font-size: 1.55rem;
        font-weight: 750;
    }

    .factor-card {
        padding: 1rem;
        border-radius: 16px;
        border: 1px solid #e6e6e6;
        background: #ffffff;
        margin-bottom: 0.7rem;
    }

    .factor-title {
        font-weight: 700;
        font-size: 1rem;
    }

    .factor-detail {
        color: #666;
        font-size: 0.88rem;
        margin-top: 0.25rem;
    }

    .success-box {
        padding: 1.2rem;
        border-radius: 18px;
        background: #e8f5e9;
        border: 1px solid #a5d6a7;
    }

    .warning-box {
        padding: 1.2rem;
        border-radius: 18px;
        background: #fff8e1;
        border: 1px solid #ffe082;
    }

    .danger-box {
        padding: 1.2rem;
        border-radius: 18px;
        background: #ffebee;
        border: 1px solid #ef9a9a;
    }

    .about-card {
        padding: 1.2rem;
        border-radius: 18px;
        border: 1px solid #e5e5e5;
        background: white;
        margin-bottom: 1rem;
    }

    footer {
        visibility: hidden;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:
    st.markdown(
        """
        <div style="
            text-align:center;
            padding:0.5rem 0 1rem 0;
        ">
            <div style="font-size:3rem;">🌱</div>
            <h2 style="margin:0;">CropWise</h2>
            <p style="color:#777;margin-top:0.2rem;">
                Smart land & crop suitability
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.divider()
    st.markdown("### Navigation")

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
    st.caption(
        "Reboot the Earth 2026\n\n"
        "Challenge 1 • Team 17"
    )


# ============================================================
# HERO
# ============================================================

st.markdown(
    """
    <div class="hero">
        <h1>🌱 CropWise</h1>
        <p>
            Understand which crops fit a location using climate,
            rainfall and soil data.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)


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


# ============================================================
# ANALYZE LAND
# ============================================================

if st.session_state.page == "🗺️ Analyze Land":
    st.subheader("Analyze a location")

    col1, col2 = st.columns([2.1, 1])

    # --------------------------------------------------------
    # MAP
    # --------------------------------------------------------

    with col1:
        st.markdown("#### 📍 Select a location")

        # OpenStreetMap only — no API-key map provider.
        m = folium.Map(
            location=[
                st.session_state.lat,
                st.session_state.lon,
            ],
            zoom_start=11,
            tiles="OpenStreetMap",
            control_scale=True,
        )

        # Custom leaf marker.
        leaf_html = """
        <div style="
            position: relative;
            width: 48px;
            height: 58px;
            transform: translate(-12px, -50px);
        ">
            <div style="
                width: 42px;
                height: 42px;
                border-radius: 50%;
                background: white;
                border: 2px solid #43A047;
                box-shadow: 0 3px 10px rgba(0,0,0,0.25);
                display: flex;
                align-items: center;
                justify-content: center;
                position: absolute;
                top: 0;
                left: 0;
            ">
                <svg
                    width="25"
                    height="25"
                    viewBox="0 0 24 24"
                    fill="none"
                    xmlns="http://www.w3.org/2000/svg"
                >
                    <path
                        d="M20.7 3.3C14.1 3.5 8.8 5.1 5.7 8.2C2.8 11.1 3.1 15.7 4.2 18.1C6.6 19.2 11.2 19.5 14.1 16.6C17.2 13.5 18.8 8.2 20.7 3.3Z"
                        fill="#4CAF50"
                    />
                    <path
                        d="M4.5 19.5C7.2 15.6 10.4 12.5 15.5 9.5"
                        stroke="#1B5E20"
                        stroke-width="1.6"
                        stroke-linecap="round"
                    />
                </svg>
            </div>

            <div style="
                position: absolute;
                top: 38px;
                left: 17px;
                width: 0;
                height: 0;
                border-left: 6px solid transparent;
                border-right: 6px solid transparent;
                border-top: 10px solid #43A047;
            "></div>
        </div>
        """

        folium.Marker(
            [
                st.session_state.lat,
                st.session_state.lon,
            ],
            tooltip="Selected location",
            icon=folium.DivIcon(html=leaf_html),
        ).add_to(m)

        map_data = st_folium(
            m,
            height=470,
            width=None,
            returned_objects=["last_clicked"],
            key="cropwise_map",
        )

        # Handle map clicks.
        if map_data and map_data.get("last_clicked"):
            clicked = map_data["last_clicked"]

            new_lat = round(float(clicked["lat"]), 5)
            new_lon = round(float(clicked["lng"]), 5)

            click_key = (new_lat, new_lon)

            if st.session_state.last_map_click != click_key:
                st.session_state.last_map_click = click_key

                st.session_state.lat = new_lat
                st.session_state.lon = new_lon

                st.session_state.latitude_input = new_lat
                st.session_state.longitude_input = new_lon

                st.rerun()

    # --------------------------------------------------------
    # LOCATION CONTROLS
    # --------------------------------------------------------

    with col2:
        st.markdown("#### Coordinates")

        latitude = st.number_input(
            "Latitude",
            min_value=-90.0,
            max_value=90.0,
            step=0.0001,
            format="%.5f",
            key="latitude_input",
        )

        longitude = st.number_input(
            "Longitude",
            min_value=-180.0,
            max_value=180.0,
            step=0.0001,
            format="%.5f",
            key="longitude_input",
        )

        st.session_state.lat = latitude
        st.session_state.lon = longitude

        st.caption(
            "Click anywhere on the map or enter coordinates manually."
        )

        reset = st.button(
            "↩️ Reset location",
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

    # --------------------------------------------------------
    # CROP SELECTION
    # --------------------------------------------------------

    st.divider()
    st.subheader("🌾 Choose a crop")

    crop_names = sorted(CROP_THRESHOLDS.keys())
    default_crop = "Wheat" if "Wheat" in crop_names else crop_names[0]

    selected_crop = st.selectbox(
        "Crop",
        crop_names,
        index=crop_names.index(default_crop),
    )

    thresholds = CROP_THRESHOLDS[selected_crop]

    with st.expander("View preferred conditions"):
        c1, c2, c3 = st.columns(3)

        with c1:
            st.metric(
                "Temperature",
                f"{thresholds['temp_c'][0]}–{thresholds['temp_c'][1]} °C",
            )

        with c2:
            st.metric(
                "Rainfall",
                f"{thresholds['rain_mm'][0]:,}–{thresholds['rain_mm'][1]:,} mm",
            )

        with c3:
            st.metric(
                "Soil pH",
                f"{thresholds['ph'][0]}–{thresholds['ph'][1]}",
            )

    st.caption(
        thresholds.get(
            "notes",
            "Preferred growing conditions.",
        )
    )

    # --------------------------------------------------------
    # ANALYZE BUTTON
    # --------------------------------------------------------

    if st.button(
        "🔎 Check this location",
        type="primary",
        use_container_width=True,
    ):
        with st.spinner("Fetching climate and soil data..."):
            climate = fetch_climate(
                st.session_state.lat,
                st.session_state.lon,
            )
            soil = fetch_soil(
                st.session_state.lat,
                st.session_state.lon,
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
            "crop": selected_crop,
            "climate": climate,
            "soil": soil,
            "verdict": verdict,
            "score": score,
            "reasons": reasons,
            "factors": factors,
        }

    # --------------------------------------------------------
    # RESULTS
    # --------------------------------------------------------

    analysis = st.session_state.analysis

    if analysis:
        st.divider()
        st.subheader(f"Results for {analysis['crop']}")

        verdict = analysis["verdict"]
        score = analysis["score"]

        if verdict == "Suitable":
            box_class = "success-box"
        elif verdict == "Marginal":
            box_class = "warning-box"
        elif verdict == "Not suitable":
            box_class = "danger-box"
        else:
            box_class = "warning-box"

        st.markdown(
            f"""
            <div class="{box_class}">
                <h2 style="margin:0;">
                    {verdict_icon(verdict)} {verdict}
                </h2>
                <p style="
                    margin-top:0.5rem;
                    margin-bottom:0;
                    font-size:1.1rem;
                ">
                    Suitability score:
                    <strong>{score_percent(score)}%</strong>
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("")

        climate = analysis["climate"]
        soil = analysis["soil"]

        c1, c2, c3 = st.columns(3)

        with c1:
            temp = climate.get("temp_c")
            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-title">🌡️ Average Temperature</div>
                    <div class="metric-value">
                        {f"{temp:.1f} °C" if temp is not None else "Unavailable"}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with c2:
            rain = climate.get("rain_mm_year")
            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-title">🌧️ Annual Rainfall</div>
                    <div class="metric-value">
                        {f"{rain:,.0f} mm" if rain is not None else "Unavailable"}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with c3:
            ph = soil.get("ph")
            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-title">🧪 Soil pH</div>
                    <div class="metric-value">
                        {f"{ph:.2f}" if ph is not None else "Unavailable"}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown("")
        st.subheader("📊 Factor breakdown")

        for factor_name, factor in analysis["factors"].items():
            value = factor["value"]
            low = factor["low"]
            high = factor["high"]
            score_value = factor["score"]
            unit = factor["unit"]
            status = factor_status(score_value)

            st.markdown(
                f"""
                <div class="factor-card">
                    <div style="
                        display:flex;
                        justify-content:space-between;
                        align-items:center;
                    ">
                        <div class="factor-title">
                            {factor_name}
                        </div>
                        <div>
                            <strong>{score_percent(score_value)}%</strong>
                            &nbsp;•&nbsp; {status}
                        </div>
                    </div>
                    <div class="factor-detail">
                        Actual:
                        <strong>{format_factor_value(value, unit)}</strong>
                        &nbsp; | &nbsp;
                        Preferred:
                        <strong>{low:g}–{high:g} {unit}</strong>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.subheader("💡 Why this result?")

        for reason in analysis["reasons"]:
            st.write("•", reason)

        if climate.get("error"):
            st.warning(climate["error"])

        if soil.get("error"):
            st.warning(soil["error"])


# ============================================================
# CROP FINDER
# ============================================================

elif st.session_state.page == "🌾 Crop Finder":
    st.subheader("🌾 Crop Finder")

    st.write(
        "Find crops that match the climate and soil conditions "
        "of a location."
    )

    c1, c2 = st.columns(2)

    with c1:
        finder_lat = st.number_input(
            "Latitude",
            min_value=-90.0,
            max_value=90.0,
            step=0.0001,
            format="%.5f",
            value=float(st.session_state.lat),
            key="finder_lat",
        )

    with c2:
        finder_lon = st.number_input(
            "Longitude",
            min_value=-180.0,
            max_value=180.0,
            step=0.0001,
            format="%.5f",
            value=float(st.session_state.lon),
            key="finder_lon",
        )

    if st.button(
        "🌱 Find suitable crops",
        type="primary",
        use_container_width=True,
    ):
        with st.spinner("Analyzing the location..."):
            climate = fetch_climate(
                finder_lat,
                finder_lon,
            )

            soil = fetch_soil(
                finder_lat,
                finder_lon,
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

            st.session_state.crop_results = {
                "climate": climate,
                "soil": soil,
                "results": results,
            }

    finder = st.session_state.get("crop_results")

    if isinstance(finder, dict):
        results = finder.get("results", [])

        if results:
            st.divider()
            st.subheader("🌿 Matching crops")

            for result in results[:12]:
                score = score_percent(result["score"])

                st.markdown(
                    f"""
                    <div class="factor-card">
                        <div style="
                            display:flex;
                            justify-content:space-between;
                            align-items:center;
                        ">
                            <div>
                                <strong>{safe_text(result['crop'])}</strong>
                                <div class="factor-detail">
                                    {verdict_icon(result['verdict'])}
                                    {safe_text(result['verdict'])}
                                </div>
                            </div>
                            <div>
                                <strong>{score}%</strong>
                            </div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )


# ============================================================
# DISEASE AI
# ============================================================

elif st.session_state.page == "🔬 Disease AI":
    st.subheader("🔬 Plant Disease AI")

    st.write(
        "Upload a clear leaf image and the AI will identify "
        "possible plant diseases."
    )

    uploaded_file = st.file_uploader(
        "Upload a leaf image",
        type=["jpg", "jpeg", "png", "webp"],
    )

    if uploaded_file:
        image = Image.open(uploaded_file)

        st.image(
            image,
            caption="Uploaded image",
            use_container_width=True,
        )

        if st.button(
            "🔬 Analyze leaf",
            type="primary",
            use_container_width=True,
        ):
            with st.spinner("Loading the disease AI..."):
                try:
                    model = load_model()

                    predictions = predict(
                        image,
                        model,
                        top_k=3,
                    )

                    st.session_state.disease_results = predictions

                except Exception as exc:
                    st.error(f"Disease model error: {exc}")

    disease_results = st.session_state.get("disease_results")

    if disease_results:
        st.divider()
        st.subheader("AI results")

        best = disease_results[0]

        disease = best["disease"]
        plant = best["plant"]
        confidence = best["confidence"]

        if disease == "Healthy":
            st.success(
                f"🌿 The AI predicts that the {plant} leaf "
                f"looks healthy."
            )
        else:
            st.warning(
                f"⚠️ Possible condition: **{disease}**"
            )

        st.metric(
            "Confidence",
            f"{confidence * 100:.1f}%",
        )

        treatment = DISEASE_TREATMENTS.get(
            disease,
            DEFAULT_TREATMENT,
        )

        st.info(
            f"💡 **Suggested action:** {treatment}"
        )

        if len(disease_results) > 1:
            with st.expander("Other possibilities"):
                for result in disease_results[1:]:
                    st.write(
                        f"• {result['plant']} — "
                        f"{result['disease']} "
                        f"({result['confidence'] * 100:.1f}%)"
                    )


# ============================================================
# ABOUT
# ============================================================

elif st.session_state.page == "ℹ️ About":
    st.subheader("ℹ️ About CropWise")

    st.markdown(
        """
        <div class="about-card">
        <h3>🌱 What is CropWise?</h3>
        CropWise is a land and crop suitability tool built for
        <strong>Reboot the Earth 2026 – Challenge 1</strong>.
        It combines climate and soil information with transparent
        crop suitability rules to help users understand which crops
        may fit a location.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="about-card">
        <h3>🌍 Data sources</h3>
        <ul>
            <li><strong>NASA POWER</strong> — climate data</li>
            <li><strong>SoilGrids / ISRIC</strong> — soil pH</li>
            <li><strong>OpenStreetMap</strong> — map data</li>
            <li><strong>PlantVillage</strong> — disease dataset</li>
            <li><strong>Hugging Face</strong> — disease model</li>
        </ul>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="about-card">
        <h3>🧠 How suitability is calculated</h3>
        CropWise compares:
        <ul>
            <li>Average temperature</li>
            <li>Annual rainfall</li>
            <li>Soil pH</li>
        </ul>
        The available factors are combined into a transparent
        suitability score.
        <br><br>
        <strong>Important:</strong> The result is a screening
        indicator, not a guaranteed prediction of crop yield.
        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "🌱 CropWise • Reboot the Earth 2026 • Challenge 1 • Team 17"
)
