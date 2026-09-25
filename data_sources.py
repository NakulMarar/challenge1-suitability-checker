"""
data_sources.py
---------------
Free agricultural data sources.

NASA POWER:
    Temperature
    Rainfall
    Relative humidity

SoilGrids:
    Soil pH

No API keys are required.
"""

import requests


NASA_POWER_URL = (
    "https://power.larc.nasa.gov/api/temporal/climatology/point"
)

SOILGRIDS_URL = (
    "https://rest.isric.org/soilgrids/v2.0/properties/query"
)

TIMEOUT = 15


def _extract_annual(param_dict):
    """
    Extract an annual value from NASA POWER.

    POWER responses may use different names for annual aggregates,
    so several known formats are supported.
    """

    if not isinstance(param_dict, dict):
        return None

    annual_keys = (
        "ANN",
        "13",
        "ANNUAL",
        "Annual",
        "annual",
    )

    for key in annual_keys:
        value = param_dict.get(key)

        if isinstance(value, (int, float)):
            return float(value)

    numeric_values = []

    for value in param_dict.values():

        if isinstance(value, (int, float)):
            numeric_values.append(float(value))

    if not numeric_values:
        return None

    return sum(numeric_values) / len(numeric_values)


def fetch_climate(lat: float, lon: float):
    """
    Fetch long-term climate information.

    Returns:

        temp_c
        rain_mm_year
        humidity_pct
        error
    """

    result = {
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
        response = requests.get(
            NASA_POWER_URL,
            params=params,
            timeout=TIMEOUT,
        )

        response.raise_for_status()

        data = response.json()

        parameter_block = (
            data
            .get("properties", {})
            .get("parameter", {})
        )

        result["temp_c"] = _extract_annual(
            parameter_block.get("T2M", {})
        )

        precipitation = _extract_annual(
            parameter_block.get("PRECTOTCORR", {})
        )

        if precipitation is not None:
            # NASA POWER precipitation climatology is treated here
            # as average daily precipitation.
            result["rain_mm_year"] = precipitation * 365.0

        result["humidity_pct"] = _extract_annual(
            parameter_block.get("RH2M", {})
        )

    except requests.RequestException as exc:

        result["error"] = (
            f"NASA POWER request failed: {exc}"
        )

    except (ValueError, KeyError, TypeError) as exc:

        result["error"] = (
            f"NASA POWER response could not be parsed: {exc}"
        )

    except Exception as exc:

        result["error"] = (
            f"NASA POWER unexpected error: {exc}"
        )

    return result


def _fetch_ph_at_depth(lat: float, lon: float, depth: str):
    """Returns pH for one depth layer, or None if that depth has no
    reading at this point (a real, fairly common SoilGrids gap)."""

    params = {
        "lon": lon,
        "lat": lat,
        "property": "phh2o",
        "depth": depth,
        "value": "mean",
    }

    response = requests.get(
        SOILGRIDS_URL,
        params=params,
        timeout=TIMEOUT,
    )

    response.raise_for_status()

    data = response.json()

    layers = (
        data
        .get("properties", {})
        .get("layers", [])
    )

    ph_layer = next(
        (
            layer
            for layer in layers
            if layer.get("name") == "phh2o"
        ),
        None,
    )

    if ph_layer is None:
        raise ValueError(
            "phh2o layer was not present in the response."
        )

    depths = ph_layer.get("depths", [])

    if not depths:
        raise ValueError(
            "No soil depth data was returned."
        )

    raw_value = depths[0].get("values", {}).get("mean")

    if raw_value is None:
        return None  # this depth has no reading here -- try a deeper one

    unit_measure = ph_layer.get("unit_measure", {})
    d_factor = unit_measure.get("d_factor", 10)

    return float(raw_value) / float(d_factor) if d_factor else float(raw_value)


def fetch_soil(lat: float, lon: float):
    """
    Fetch soil pH from SoilGrids.

    Tries 0-5cm first, then falls back to 5-15cm and 15-30cm --
    SoilGrids fairly often has no reading at the shallowest depth for a
    given point (disturbed land, coastline, etc.) even when deeper
    layers do have one. Trying only 0-5cm and giving up, as an earlier
    version of this file did, meant soil pH -- and therefore a third
    of the suitability score -- came back empty far more often than
    it needed to.
    """

    result = {
        "ph": None,
        "error": None,
    }

    for depth in ("0-5cm", "5-15cm", "15-30cm"):
        try:
            ph = _fetch_ph_at_depth(lat, lon, depth)
            if ph is not None:
                result["ph"] = ph
                return result

        except requests.RequestException as exc:
            result["error"] = f"SoilGrids request failed: {exc}"
            return result

        except (ValueError, KeyError, TypeError, StopIteration) as exc:
            result["error"] = f"SoilGrids response could not be parsed: {exc}"
            return result

        except Exception as exc:
            result["error"] = f"SoilGrids unexpected error: {exc}"
            return result

    result["error"] = "SoilGrids has no pH reading for this point at 0-30cm depth."
    return result


if __name__ == "__main__":

    import json
    import sys

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

    print("\nCLIMATE")
    print(
        json.dumps(
            fetch_climate(latitude, longitude),
            indent=2,
        )
    )

    print("\nSOIL")
    print(
        json.dumps(
            fetch_soil(latitude, longitude),
            indent=2,
        )
    )
