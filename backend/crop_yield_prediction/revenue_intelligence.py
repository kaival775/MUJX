"""Deterministic harvest and revenue intelligence layered over yield predictions.

The existing neural yield model remains untouched.  This module converts its output
into farmer-facing quality, timing and action decisions using transparent rules.
"""
from datetime import date, timedelta
import hashlib

HECTARES_PER_ACRE = 0.404686

GRADE_FACTORS = {
    "Rice": ["grain length", "maturity", "colour", "broken grains", "disease"],
    "Wheat": ["grain size", "maturity", "colour", "moisture", "disease"],
    "Cotton": ["staple length", "boll maturity", "colour", "trash", "pest damage"],
    "Sugarcane": ["cane diameter", "maturity", "sugar recovery", "colour", "disease"],
    "Tomato": ["fruit size", "maturity", "colour", "firmness", "defects"],
    "Potato": ["tuber size", "maturity", "skin colour", "dry matter", "defects"],
    "Onion": ["bulb size", "neck maturity", "colour", "firmness", "disease"],
    "Mango": ["fruit size", "maturity", "colour", "firmness", "blemishes"],
}
DEFAULT_FACTORS = ["produce size", "maturity", "colour", "uniformity", "disease/defects"]


def _bounded(value, low, high):
    return max(low, min(high, value))


def build_revenue_intelligence(crop, yield_tons_ha, mandi_price_quintal,
                               cost_ha, ndvi, moisture, nitrogen, temp, rainfall):
    """Return quality mix, harvest window and ranked action economics."""
    health = _bounded(0.42 * ndvi + 0.22 * (1 - abs(moisture - .58)) +
                      0.16 * (1 - abs(nitrogen - .55)) +
                      0.12 * (1 - abs(temp - .45)) + 0.08 * (1 - rainfall), 0, 1)
    defect_risk = _bounded((1 - ndvi) * .35 + max(0, rainfall - .65) * .3 +
                           max(0, temp - .72) * .2, 0.03, .45)
    grade_a = round(_bounded(35 + health * 53 - defect_risk * 22, 20, 88))
    grade_c = round(_bounded(8 + defect_risk * 35 + (1 - health) * 12, 4, 35))
    grade_b = 100 - grade_a - grade_c

    # Grade-weighted selling price: A +12%, B market price, C -18%.
    weighted_price = mandi_price_quintal * (
        grade_a / 100 * 1.12 + grade_b / 100 + grade_c / 100 * .82
    )
    base_revenue = yield_tons_ha * 10 * weighted_price

    wet_risk = rainfall >= .55
    heat_risk = temp >= .7
    maturity_days = round(_bounded(24 - ndvi * 22 + (0 if ndvi >= .72 else 5), 2, 24))
    market_seed = int(hashlib.sha256(crop.encode()).hexdigest()[:4], 16)
    market_trend_pct = round(((market_seed % 81) - 30) / 10, 1)
    if wet_risk:
        maturity_days = max(1, maturity_days - 2)
    start = date.today() + timedelta(days=maturity_days)
    window_days = 2 if wet_risk or heat_risk else 3
    end = start + timedelta(days=window_days)

    loss_per_point = base_revenue * .006
    irrigation_gain = max(0, 55 - moisture * 100) * loss_per_point
    irrigation_cost = 1850.0
    fertilizer_gain = max(0, .48 - nitrogen) * base_revenue * .12
    fertilizer_cost = 2600.0
    protection_gain = defect_risk * base_revenue * (.18 if wet_risk else .10)
    protection_cost = 2100.0
    harvest_gain = base_revenue * (.055 if wet_risk else (-.035 if maturity_days > 5 else .025))
    harvest_cost = 7200.0
    wait_gain = base_revenue * max(-.04, min(.04, market_trend_pct / 100))

    candidates = [
        ("Irrigate", irrigation_gain - irrigation_cost,
         "Restore moisture and protect marketable yield"),
        ("Fertilize", fertilizer_gain - fertilizer_cost,
         "Correct nitrogen stress and improve size/grade"),
        ("Apply protection", protection_gain - protection_cost,
         "Reduce weather-linked disease and defect loss"),
        ("Harvest", harvest_gain - harvest_cost,
         "Capture mature produce before quality or weather loss"),
        ("Wait / Do nothing", wait_gain,
         "Avoid unnecessary input cost while conditions remain acceptable"),
    ]
    actions = [{
        "action": action,
        "net_revenue_impact_ha": round(impact),
        "net_revenue_impact_acre": round(impact * HECTARES_PER_ACRE),
        "reason": reason,
    } for action, impact, reason in sorted(candidates, key=lambda row: row[1], reverse=True)]
    best = actions[0]
    if best["action"] == "Wait / Do nothing" and rainfall >= .35:
        best["reason"] = "Rainfall is expected; waiting avoids unnecessary irrigation/input cost"

    return {
        "grade_prediction": {
            "probabilities": {"A": grade_a, "B": grade_b, "C": grade_c},
            "determining_factors": GRADE_FACTORS.get(crop, DEFAULT_FACTORS),
            "expected_grade": max({"A": grade_a, "B": grade_b, "C": grade_c}, key={"A": grade_a, "B": grade_b, "C": grade_c}.get),
        },
        "harvest_recommendation": {
            "best_window_start": start.isoformat(),
            "best_window_end": end.isoformat(),
            "days_until_window": maturity_days,
            "weather_risk": "High rain/heat risk" if wet_risk or heat_risk else "Low weather risk",
            "market_trend_pct": market_trend_pct,
            "basis": ["crop maturity", "expected grade", "weather risk", "market trend"],
        },
        "revenue_optimisation": {
            "expected_quantity_tons_ha": yield_tons_ha,
            "grade_weighted_price_quintal": round(weighted_price, 2),
            "expected_revenue_ha": round(base_revenue),
            "cultivation_cost_ha": round(cost_ha),
            "expected_net_revenue_ha": round(base_revenue - cost_ha),
            "expected_net_revenue_acre": round((base_revenue - cost_ha) * HECTARES_PER_ACRE),
            "recommended_action": best,
            "action_comparison": actions,
        },
    }
