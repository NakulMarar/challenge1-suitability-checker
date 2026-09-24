"""
data_sources.py
----------------
Free, no-API-key data pulls for a given (lat, lon):

  - NASA POWER  -> long-term average temperature, rainfall, humidity
  - SoilGrids   -> soil pH (extend with more properties if you have time)

Both are called server-side (inside Streamlit's Python process), which
sidesteps any browser CORS issues you'd hit calling them from JS.

IMPORTANT: I wrote these against my best knowledge of each API's
documented shape, but I could not make live test calls from the sandbox
this was built in (its network allowlist doesn't include NASA/ISRIC).
The first time you run this with real internet access:
  1. Run `python data_sources.py <lat> <lon>` (see bottom of file) and
     read the printed raw JSON.
  2. If a field comes back None or a KeyError shows up, the shape
     differs slightly from what's assumed below -- the fix is almost
     always a one-line key rename, marked with "ADJUST" comments.
Budget 15 minutes for this on Thursday morning before you build on top
of it, so nobody is debugging it live during the pitch.
"""

import requests

NASA_POWER_URL = "https://power.larc.nasa.gov/api/temporal/climatology/point"
SOILGRIDS_URL = "https://rest.isric.org/soilgrids/v2.0/properties/query"

TIMEOUT = 10  # seconds -- fail fast rather than freeze the UI


def _extract_annual(param_dict):
    """
    NASA POWER's climatology response keys each parameter's 12 monthly
    values plus an annual aggregate, but the exact key used for
    'annual' has varied between API versions ('ANN', '13', 'ANNUAL').
    Try the known keys first; fall back to averaging whatever numeric
    monthly values are present so this degrades gracefully instead of
    crashing. ADJUST the key list below if you see a different one in
    the raw JSON.
    """
    if not isinstance(param_dict, dict):
        return None
    for key in ("ANN", "13", "ANNUAL", "Annual"):
        if key in param_dict and isinstance(param_dict[key], (int, float)):
            return param_dict[key]
    values = [v for v in param_dict.values() if isinstance(v, (int, float))]
    return sum(values) / len(values) if values else None


def fetch_climate(lat: float, lon: float) -> dict:
    """
    Returns long-term climatological averages:
      temp_c        - mean annual temperature at 2m, Celsius
      rain_mm_year  - estimated annual rainfall, mm
      humidity_pct  - mean annual relative humidity at 2m, %
    Any field that couldn't be parsed comes back as None rather than
    raising, so the caller can still show partial results.
    """
    out = {"temp_c": None, "rain_mm_year": None, "humidity_pct": None,
           "error": None}
    params = {
        "parameters": "T2M,PRECTOTCORR,RH2M",
        "community": "AG",
        "longitude": lon,
        "latitude": lat,
        "format": "JSON",
    }
    try:
        resp = requests.get(NASA_POWER_URL, params=params, timeout=TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
        param_block = data["properties"]["parameter"]  # ADJUST if renamed

        out["temp_c"] = _extract_annual(param_block.get("T2M", {}))

        rain_avg_daily = _extract_annual(param_block.get("PRECTOTCORR", {}))
        # PRECTOTCORR climatology is an average mm/day for the period;
        # multiply out to an annual total. ADJUST if POWER already
        # returns an annual total for this parameter.
        out["rain_mm_year"] = (
            rain_avg_daily * 365 if rain_avg_daily is not None else None
        )

        out["humidity_pct"] = _extract_annual(param_block.get("RH2M", {}))
    except Exception as exc:  # noqa: BLE001 -- deliberately broad for a demo
        out["error"] = f"NASA POWER fetch failed: {exc}"
    return out


def fetch_soil(lat: float, lon: float) -> dict:
    """
    Returns:
      ph      - soil pH (H2O method), 0-5cm depth
    Extend with more `property=` values (e.g. "soc" for organic carbon,
    "clay", "sand") the same way if you have time -- SoilGrids supports
    several in one call.
    """
    out = {"ph": None, "error": None}
    params = {
        "lon": lon,
        "lat": lat,
        "property": "phh2o",
        "depth": "0-5cm",
        "value": "mean",
    }
    try:
        resp = requests.get(SOILGRIDS_URL, params=params, timeout=TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
        layers = data["properties"]["layers"]  # ADJUST if renamed
        ph_layer = next(l for l in layers if l.get("name") == "phh2o")
        depth_block = ph_layer["depths"][0]
        raw_value = depth_block["values"]["mean"]

        # SoilGrids commonly stores this scaled (e.g. pH x10) to save
        # space; the scale factor is usually in unit_measure.d_factor.
        # ADJUST/remove this division if a printed raw response shows
        # values already in plain pH units (typically 3.5-9.5).
        d_factor = ph_layer.get("unit_measure", {}).get("d_factor", 10)
        out["ph"] = raw_value / d_factor if d_factor else raw_value
    except Exception as exc:  # noqa: BLE001
        out["error"] = f"SoilGrids fetch failed: {exc}"
    return out


if __name__ == "__main__":
    # Quick manual check once you have real internet access:
    #   python data_sources.py 25.28 51.53   (Doha, as an example point)
    import sys
    import json

    lat_arg = float(sys.argv[1]) if len(sys.argv) > 1 else 25.2854
    lon_arg = float(sys.argv[2]) if len(sys.argv) > 2 else 51.5310

    print("Climate:", json.dumps(fetch_climate(lat_arg, lon_arg), indent=2))
    print("Soil:", json.dumps(fetch_soil(lat_arg, lon_arg), indent=2))
