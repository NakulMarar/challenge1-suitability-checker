"""
suitability.py
---------------
Rule-based suitability scoring: compares fetched climate/soil data
against a crop's threshold ranges from crop_data.CROP_THRESHOLDS.

Deliberately simple (three factors, equal weight, transparent reasons)
so it's easy to explain to judges live. Swap in a weighted score or an
ML model later if time allows -- the interface (evaluate() returning
verdict/score/reasons) doesn't need to change if you do.
"""


def _score_range(value, low, high):
    """1.0 if inside [low, high], 0.5 if just outside (marginal), else 0.
    None (missing data) is excluded from scoring rather than penalized."""
    if value is None:
        return None
    if low <= value <= high:
        return 1.0
    span = max(high - low, 1e-6)
    distance = (low - value) / span if value < low else (value - high) / span
    return 0.5 if distance <= 0.25 else 0.0


def evaluate(climate: dict, soil: dict, thresholds: dict):
    """
    Returns (verdict: str, score: float 0-1, reasons: list[str]).
    verdict is one of "Suitable", "Marginal", "Not suitable", "Unknown".
    "Unknown" only happens if every factor came back as missing data.
    """
    factor_scores = {
        "Temperature": _score_range(climate.get("temp_c"), *thresholds["temp_c"]),
        "Rainfall": _score_range(climate.get("rain_mm_year"), *thresholds["rain_mm"]),
        "Soil pH": _score_range(soil.get("ph"), *thresholds["ph"]),
    }

    known = {k: v for k, v in factor_scores.items() if v is not None}
    if not known:
        return "Unknown", 0.0, ["No climate or soil data could be fetched for this point."]

    score = sum(known.values()) / len(known)

    reasons = []
    for factor, val in factor_scores.items():
        if val is None:
            reasons.append(f"{factor}: data unavailable, excluded from score.")
        elif val == 1.0:
            reasons.append(f"{factor}: within range.")
        elif val == 0.5:
            reasons.append(f"{factor}: just outside the ideal range (marginal).")
        else:
            reasons.append(f"{factor}: outside the suitable range.")

    if score >= 0.8:
        verdict = "Suitable"
    elif score >= 0.4:
        verdict = "Marginal"
    else:
        verdict = "Not suitable"

    return verdict, score, reasons
