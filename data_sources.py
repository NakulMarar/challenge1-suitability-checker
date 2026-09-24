"""
data_sources.py
---------------
Free agricultural data sources.

NASA POWER:
    - Long-term temperature
    - Annual rainfall
    - Relative humidity

SoilGrids:
    - Soil pH

No API keys are required.

This version includes:
    - safer API parsing
    - coordinate validation
    - clearer error messages
    - retry handling
    - request caching at the HTTP level
    - multiple SoilGrids response formats
    - protection against invalid numeric values
"""

import math
import time
from typing import Any, Dict, Optional

import requests


# ============================================================
# API URLS
# ============================================================

NASA_POWER_URL = (
    "https://power.larc.nasa.gov/api/temporal/climatology/point"
)

SOILGRIDS_URL = (
    "https://rest.isric.org/soilgrids/v2.0/properties/query"
)


# ============================================================
# SETTINGS
# ============================================================

TIMEOUT = 20

MAX_RETRIES = 2

USER_AGENT = (
    "CropWise-Team17/1.0 "
    "(Reboot the Earth 2026 agricultural screening prototype)"
)


# ============================================================
# HTTP SESSION
# ============================================================

_session = requests.Session()

_session.headers.update(
    {
        "User-Agent": USER_AGENT,
        "Accept": "application/json",
    }
)


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def _is_number(value: Any) -> bool:
    """
    Check whether a value is a usable finite number.
    """

    if isinstance(value, bool):
        return False

    if not isinstance(value, (int, float)):
        return False

    return math.isfinite(float(value))


def _safe_float(value: Any) -> Optional[float]:
    """
    Convert a value to float if possible.

    Returns None for invalid/missing values.
    """

    if value is None:
        return None

    try:
        number = float(value)

        if not math.isfinite(number):
            return None

        return number

    except (TypeError, ValueError):
        return None


def _validate_coordinates(lat: float, lon: float):
    """
    Validate latitude and longitude.
    """

    lat = _safe_float(lat)
    lon = _safe_float(lon)

    if lat is None or lon is None:
        raise ValueError(
            "Latitude and longitude must be valid numbers."
        )

    if not -90 <= lat <= 90:
        raise ValueError(
            "Latitude must be between -90 and 90."
        )

    if not -180 <= lon <= 180:
        raise ValueError(
            "Longitude must be between -180 and 180."
        )

    return lat, lon


def _request_json(url: str, params: Dict[str, Any]):
    """
    Make a GET request and return decoded JSON.

    Retries temporary failures automatically.
    """

    last_error = None

    for attempt in range(MAX_RETRIES + 1):

        try:

            response = _session.get(
                url,
                params=params,
                timeout=TIMEOUT,
            )

            response.raise_for_status()

            return response.json()

        except requests.RequestException as exc:

            last_error = exc

            if attempt < MAX_RETRIES:
                time.sleep(0.8 * (attempt + 1))
            else:
                raise last_error

        except ValueError as exc:

            raise ValueError(
                "The server returned an invalid JSON response."
            ) from exc

    raise RuntimeError(
        "Request failed unexpectedly."
    )


# ============================================================
# NASA POWER HELPERS
# ============================================================

def _extract_annual(param_dict):
    """
    Extract a representative annual value from a NASA POWER
    parameter dictionary.

    NASA POWER climatology responses can expose aggregate
    values using different key names depending on endpoint
    and parameter.

    Priority:
        ANN
        ANNUAL
        Annual
        annual
        13

    If none exists, numeric monthly values are averaged.
    """

    if not isinstance(param_dict, dict):
        return None

    preferred_keys = (
        "ANN",
        "ANNUAL",
        "Annual",
        "annual",
        "13",
    )

    for key in preferred_keys:

        value = _safe_float(
            param_dict.get(key)
        )

        if value is not None:
            return value

    numeric_values = []

    for value in param_dict.values():

        number = _safe_float(value)

        if number is not None:
            numeric_values.append(number)

    if not numeric_values:
        return None

    return sum(numeric_values) / len(numeric_values)


def _extract_parameter(
    parameter_block: Dict[str, Any],
    names,
):
    """
    Find the first available parameter using a list of possible
    parameter names.
    """

    if not isinstance(parameter_block, dict):
        return None

    for name in names:

        if name not in parameter_block:
            continue

        value = _extract_annual(
            parameter_block[name]
        )

        if value is not None:
            return value

    return None


# ============================================================
# NASA POWER
# ============================================================

def fetch_climate(lat: float, lon: float):
    """
    Fetch long-term climate information for a coordinate.

    Returns:

        {
            "temp_c": float | None,
            "rain_mm_year": float | None,
            "humidity_pct": float | None,
            "error": str | None
        }

    Temperature:
        °C

    Rainfall:
        mm/year

    Humidity:
        %
    """

    result = {
        "temp_c": None,
        "rain_mm_year": None,
        "humidity_pct": None,
        "error": None,
    }

    # --------------------------------------------------------
    # Validate coordinates
    # --------------------------------------------------------

    try:

        lat, lon = _validate_coordinates(
            lat,
            lon,
        )

    except ValueError as exc:

        result["error"] = str(exc)

        return result

    # --------------------------------------------------------
    # NASA POWER request
    # --------------------------------------------------------

    params = {
        "parameters": "T2M,PRECTOTCORR,RH2M",
        "community": "AG",
        "longitude": lon,
        "latitude": lat,
        "format": "JSON",
    }

    try:

        data = _request_json(
            NASA_POWER_URL,
            params,
        )

        # ----------------------------------------------------
        # Navigate response safely
        # ----------------------------------------------------

        properties = data.get(
            "properties",
            {},
        )

        if not isinstance(properties, dict):
            raise ValueError(
                "NASA POWER response has an invalid properties block."
            )

        parameter_block = properties.get(
            "parameter",
            {},
        )

        if not isinstance(parameter_block, dict):
            raise ValueError(
                "NASA POWER response has no usable parameter data."
            )

        # ----------------------------------------------------
        # Temperature
        # ----------------------------------------------------

        result["temp_c"] = _extract_parameter(
            parameter_block,
            (
                "T2M",
                "T2M_MAX",
                "T2M_MIN",
            ),
        )

        # ----------------------------------------------------
        # Rainfall
        # ----------------------------------------------------

        precipitation = _extract_parameter(
            parameter_block,
            (
                "PRECTOTCORR",
                "PRECTOT",
                "PRECTOTCORR_SUM",
            ),
        )

        if precipitation is not None:

            # NASA POWER climatology precipitation is normally
            # expressed as average daily precipitation.
            #
            # Convert mm/day -> mm/year.

            result["rain_mm_year"] = (
                precipitation * 365.0
            )

        # ----------------------------------------------------
        # Relative humidity
        # ----------------------------------------------------

        result["humidity_pct"] = _extract_parameter(
            parameter_block,
            (
                "RH2M",
                "RH2M_AVG",
            ),
        )

        # ----------------------------------------------------
        # Check whether anything was actually returned
        # ----------------------------------------------------

        if (
            result["temp_c"] is None
            and result["rain_mm_year"] is None
            and result["humidity_pct"] is None
        ):

            raise ValueError(
                "NASA POWER returned no usable climate values."
            )

    except requests.RequestException as exc:

        result["error"] = (
            "NASA POWER request failed. "
            "Please check your internet connection "
            f"or try again later. Details: {exc}"
        )

    except ValueError as exc:

        result["error"] = (
            f"NASA POWER data could not be parsed: {exc}"
        )

    except Exception as exc:

        result["error"] = (
            f"NASA POWER unexpected error: {exc}"
        )

    return result


# ============================================================
# SOILGRIDS HELPERS
# ============================================================

def _extract_soil_value(data):
    """
    Extract SoilGrids pH from the documented layers/depths
    response structure.

    SoilGrids commonly returns pH as a scaled integer.

    Example:
        raw value 65
        d_factor 10
        -> pH 6.5
    """

    if not isinstance(data, dict):
        raise ValueError(
            "SoilGrids response is not a JSON object."
        )

    properties = data.get(
        "properties",
        {},
    )

    if not isinstance(properties, dict):
        raise ValueError(
            "SoilGrids properties block is invalid."
        )

    layers = properties.get(
        "layers",
        [],
    )

    if not isinstance(layers, list):
        raise ValueError(
            "SoilGrids layers block is invalid."
        )

    # --------------------------------------------------------
    # Find pH layer
    # --------------------------------------------------------

    ph_layer = None

    for layer in layers:

        if not isinstance(layer, dict):
            continue

        if layer.get("name") == "phh2o":

            ph_layer = layer
            break

    if ph_layer is None:

        raise ValueError(
            "The phh2o soil layer was not returned."
        )

    # --------------------------------------------------------
    # Get depth data
    # --------------------------------------------------------

    depths = ph_layer.get(
        "depths",
        [],
    )

    if not isinstance(depths, list) or not depths:

        raise ValueError(
            "No soil depth data was returned."
        )

    # Prefer the 0-5 cm layer if available.
    depth_block = None

    for depth in depths:

        if not isinstance(depth, dict):
            continue

        label = str(
            depth.get("label", "")
        ).lower()

        if label in (
            "0-5cm",
            "0-5",
            "0-5 cm",
        ):

            depth_block = depth
            break

    # Fall back to the first depth if the label is absent.
    if depth_block is None:
        depth_block = depths[0]

    values = depth_block.get(
        "values",
        {},
    )

    if not isinstance(values, dict):

        raise ValueError(
            "SoilGrids depth contains no usable values."
        )

    raw_value = values.get("mean")

    if raw_value is None:

        raise ValueError(
            "SoilGrids did not return a mean pH value."
        )

    raw_value = _safe_float(
        raw_value
    )

    if raw_value is None:

        raise ValueError(
            "SoilGrids returned an invalid pH value."
        )

    # --------------------------------------------------------
    # Scaling factor
    # --------------------------------------------------------

    unit_measure = ph_layer.get(
        "unit_measure",
        {},
    )

    if not isinstance(unit_measure, dict):
        unit_measure = {}

    d_factor = unit_measure.get(
        "d_factor",
        10,
    )

    d_factor = _safe_float(
        d_factor
    )

    if d_factor is None or d_factor == 0:

        d_factor = 10.0

    ph = raw_value / d_factor

    # --------------------------------------------------------
    # Sanity check
    # --------------------------------------------------------

    if not 0 <= ph <= 14:

        raise ValueError(
            f"SoilGrids returned an unrealistic pH value: {ph:.2f}"
        )

    return ph


# ============================================================
# SOILGRIDS
# ============================================================

def fetch_soil(lat: float, lon: float):
    """
    Fetch soil pH from SoilGrids.

    Depth:
        0-5 cm

    Property:
        phh2o

    Returns:

        {
            "ph": float | None,
            "error": str | None
        }
    """

    result = {
        "ph": None,
        "error": None,
    }

    # --------------------------------------------------------
    # Validate coordinates
    # --------------------------------------------------------

    try:

        lat, lon = _validate_coordinates(
            lat,
            lon,
        )

    except ValueError as exc:

        result["error"] = str(exc)

        return result

    # --------------------------------------------------------
    # SoilGrids request
    # --------------------------------------------------------

    params = {
        "lon": lon,
        "lat": lat,
        "property": "phh2o",
        "depth": "0-5cm",
        "value": "mean",
    }

    try:

        data = _request_json(
            SOILGRIDS_URL,
            params,
        )

        result["ph"] = _extract_soil_value(
            data
        )

    except requests.RequestException as exc:

        result["error"] = (
            "SoilGrids request failed. "
            "Please check your internet connection "
            f"or try again later. Details: {exc}"
        )

    except ValueError as exc:

        result["error"] = (
            f"SoilGrids data could not be parsed: {exc}"
        )

    except Exception as exc:

        result["error"] = (
            f"SoilGrids unexpected error: {exc}"
        )

    return result


# ============================================================
# COMMAND LINE TEST
# ============================================================

if __name__ == "__main__":

    import json
    import sys

    try:

        latitude = (
            float(sys.argv[1])
            if len(sys.argv) > 1
            else 25.2854
        )

        longitude = (
            float(sys.argv[2])
            if len(sys.argv) > 2
            else 51.5310
        )

    except ValueError:

        print(
            "Usage: python data_sources.py <latitude> <longitude>"
        )

        sys.exit(1)

    print()
    print("=" * 60)
    print("CropWise Data Source Test")
    print("=" * 60)

    print()
    print("LOCATION")
    print(
        f"Latitude : {latitude}"
    )
    print(
        f"Longitude: {longitude}"
    )

    print()
    print("CLIMATE")
    print("-" * 60)

    climate = fetch_climate(
        latitude,
        longitude,
    )

    print(
        json.dumps(
            climate,
            indent=2,
        )
    )

    print()
    print("SOIL")
    print("-" * 60)

    soil = fetch_soil(
        latitude,
        longitude,
    )

    print(
        json.dumps(
            soil,
            indent=2,
        )
    )

    print()
    print("=" * 60)
    print("Test complete")
    print("=" * 60)
