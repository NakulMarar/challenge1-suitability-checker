"""
suitability.py
--------------
Transparent rule-based crop suitability scoring.

Each crop is evaluated against:
    - Temperature
    - Annual rainfall
    - Soil pH

All available factors receive equal weight.

The score is a screening indicator, not a guaranteed
agricultural yield prediction.
"""


def _score_range(value, low, high):
    """
    Return:

        1.0 -> inside preferred range
        0.5 -> slightly outside preferred range
        0.0 -> significantly outside preferred range
        None -> missing data
    """

    if value is None:
        return None

    if low <= value <= high:
        return 1.0

    span = max(high - low, 1e-6)

    if value < low:
        distance = (low - value) / span
    else:
        distance = (value - high) / span

    return 0.5 if distance <= 0.25 else 0.0


def evaluate(climate: dict, soil: dict, thresholds: dict):
    """
    Return:

        verdict
        score
        reasons

    verdict:
        Suitable
        Marginal
        Not suitable
        Unknown
    """

    factor_scores = {
        "Temperature": _score_range(
            climate.get("temp_c"),
            *thresholds["temp_c"],
        ),
        "Rainfall": _score_range(
            climate.get("rain_mm_year"),
            *thresholds["rain_mm"],
        ),
        "Soil pH": _score_range(
            soil.get("ph"),
            *thresholds["ph"],
        ),
    }

    known = {
        factor: score
        for factor, score in factor_scores.items()
        if score is not None
    }

    if not known:
        return (
            "Unknown",
            0.0,
            ["No climate or soil data could be fetched for this point."],
        )

    score = sum(known.values()) / len(known)

    reasons = []

    for factor, value in factor_scores.items():

        if value is None:
            reasons.append(
                f"{factor}: data unavailable and excluded from the score."
            )

        elif value == 1.0:
            reasons.append(
                f"{factor}: within the preferred range."
            )

        elif value == 0.5:
            reasons.append(
                f"{factor}: slightly outside the preferred range."
            )

        else:
            reasons.append(
                f"{factor}: outside the preferred range."
            )

    if score >= 0.8:
        verdict = "Suitable"
    elif score >= 0.4:
        verdict = "Marginal"
    else:
        verdict = "Not suitable"

    return verdict, score, reasons


def get_factor_scores(climate: dict, soil: dict, thresholds: dict):
    """
    Return detailed factor information for dashboard displays.
    """

    return {
        "Temperature": {
            "value": climate.get("temp_c"),
            "low": thresholds["temp_c"][0],
            "high": thresholds["temp_c"][1],
            "score": _score_range(
                climate.get("temp_c"),
                *thresholds["temp_c"],
            ),
            "unit": "°C",
        },
        "Rainfall": {
            "value": climate.get("rain_mm_year"),
            "low": thresholds["rain_mm"][0],
            "high": thresholds["rain_mm"][1],
            "score": _score_range(
                climate.get("rain_mm_year"),
                *thresholds["rain_mm"],
            ),
            "unit": "mm/year",
        },
        "Soil pH": {
            "value": soil.get("ph"),
            "low": thresholds["ph"][0],
            "high": thresholds["ph"][1],
            "score": _score_range(
                soil.get("ph"),
                *thresholds["ph"],
            ),
            "unit": "pH",
        },
    }
