import requests


NASA_POWER_URL = "https://power.larc.nasa.gov/api/temporal/climatology/point"
SOILGRIDS_URL = "https://rest.isric.org/soilgrids/v2.0/properties/query"

TIMEOUT = 10


def _extract_annual(param_dict):
    if not isinstance(param_dict, dict):
        return None

    for key in ("ANN", "13", "ANNUAL", "Annual"):
        if key in param_dict and isinstance(
            param_dict[key],
            (int, float),
        ):
            return param_dict[key]

    values = [
        value
        for value in param_dict.values()
        if isinstance(value, (int, float))
    ]

    return sum(values) / len(values) if values else None


def fetch_climate(lat: float, lon: float) -> dict:

    out = {
        "temp_c": None,
        "rain_mm_year": None,
        "humidity_pct": None,
        "error": None,
    }

    params = {
        "parameters": "T2M,PRECTOTCORR,RH2M",
        "community": "AG",
        "longitude": lon,
        "latitude": lat,
        "format": "JSON",
    }

    try:

        resp = requests.get(
            NASA_POWER_URL,
            params=params,
            timeout=TIMEOUT,
        )

        resp.raise_for_status()

        data = resp.json()

        param_block = data["properties"]["parameter"]

        # Temperature
        out["temp_c"] = _extract_annual(
            param_block.get("T2M", {})
        )

        # NASA POWER precipitation is average daily precipitation.
        # Convert it to approximate annual rainfall.
        rain_avg_daily = _extract_annual(
            param_block.get("PRECTOTCORR", {})
        )

        out["rain_mm_year"] = (
            rain_avg_daily * 365
            if rain_avg_daily is not None
            else None
        )

        # Relative humidity
        out["humidity_pct"] = _extract_annual(
            param_block.get("RH2M", {})
        )

    except Exception as exc:

        out["error"] = (
            f"NASA POWER fetch failed: {exc}"
        )

    return out


def fetch_soil(lat: float, lon: float) -> dict:

    out = {
        "ph": None,
        "error": None,
    }

    params = {
        "lon": lon,
        "lat": lat,
        "property": "phh2o",
        "depth": "0-5cm",
        "value": "mean",
    }

    try:

        resp = requests.get(
            SOILGRIDS_URL,
            params=params,
            timeout=TIMEOUT,
        )

        resp.raise_for_status()

        data = resp.json()

        layers = data["properties"]["layers"]

        ph_layer = next(
            layer
            for layer in layers
            if layer.get("name") == "phh2o"
        )

        depth_block = ph_layer["depths"][0]

        raw_value = depth_block["values"]["mean"]

        d_factor = (
            ph_layer
            .get("unit_measure", {})
            .get("d_factor", 10)
        )

        out["ph"] = (
            raw_value / d_factor
            if d_factor
            else raw_value
        )

    except Exception as exc:

        out["error"] = (
            f"SoilGrids fetch failed: {exc}"
        )

    return out
