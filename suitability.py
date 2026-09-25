def _score_range(value, low, high):
    """
    Continuous suitability score.

    1.0 = inside the preferred range
    Scores gradually decrease as the value moves farther outside.
    0.0 = very far outside the range.
    """

    if value is None:
        return None

    value = float(value)
    low = float(low)
    high = float(high)

    # Perfect match
    if low <= value <= high:
        return 1.0

    # Calculate distance from the preferred range
    if value < low:
        distance = low - value
    else:
        distance = value - high

    # Width of the preferred range
    span = max(high - low, 1e-6)

    # Gradual penalty
    penalty = distance / span

    # Convert to a score.
    # 0 distance = 1.0
    # 25% of range outside = 0.75
    # 50% outside = 0.50
    # 75% outside = 0.25
    # 100%+ outside = 0.0
    score = 1.0 - penalty

    return max(0.0, min(1.0, score))


def get_factor_scores(climate, soil, thresholds):

    return {
        "Temperature": {
            "value": climate.get("temp_c"),
            "score": _score_range(
                climate.get("temp_c"),
                *thresholds["temp_c"],
            ),
            "low": thresholds["temp_c"][0],
            "high": thresholds["temp_c"][1],
            "unit": "°C",
        },

        "Rainfall": {
            "value": climate.get("rain_mm_year"),
            "score": _score_range(
                climate.get("rain_mm_year"),
                *thresholds["rain_mm"],
            ),
            "low": thresholds["rain_mm"][0],
            "high": thresholds["rain_mm"][1],
            "unit": "mm/year",
        },

        "Soil pH": {
            "value": soil.get("ph"),
            "score": _score_range(
                soil.get("ph"),
                *thresholds["ph"],
            ),
            "low": thresholds["ph"][0],
            "high": thresholds["ph"][1],
            "unit": "",
        },
    }


def evaluate(climate, soil, thresholds):

    factor_scores = get_factor_scores(
        climate,
        soil,
        thresholds,
    )

    known = {
        name: factor["score"]
        for name, factor in factor_scores.items()
        if factor["score"] is not None
    }

    if not known:
        return (
            "Unknown",
            0.0,
            [
                "No climate or soil data could be fetched "
                "for this point."
            ],
        )

    score = sum(known.values()) / len(known)

    reasons = []

    for factor, data in factor_scores.items():

        value = data["value"]
        factor_score = data["score"]

        if factor_score is None:

            reasons.append(
                f"{factor}: data unavailable, "
                "excluded from score."
            )

        elif factor_score >= 0.8:

            reasons.append(
                f"{factor}: within or very close to "
                "the preferred range."
            )

        elif factor_score >= 0.5:

            reasons.append(
                f"{factor}: somewhat outside the "
                "preferred range."
            )

        else:

            reasons.append(
                f"{factor}: substantially outside the "
                "preferred range."
            )

    # Overall verdict
    if score >= 0.75:
        verdict = "Suitable"

    elif score >= 0.45:
        verdict = "Marginal"

    else:
        verdict = "Not suitable"

    return verdict, score, reasons
