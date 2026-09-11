from .revenue_intelligence import build_revenue_intelligence


def test_intelligence_has_complete_grade_and_all_decisions():
    result = build_revenue_intelligence("Wheat", 4.2, 2450, 52000, .72, .42, .38, .48, .7)
    grades = result["grade_prediction"]["probabilities"]
    assert sum(grades.values()) == 100
    assert set(grades) == {"A", "B", "C"}
    assert len(result["grade_prediction"]["determining_factors"]) >= 5
    actions = {row["action"] for row in result["revenue_optimisation"]["action_comparison"]}
    assert actions == {"Irrigate", "Fertilize", "Apply protection", "Harvest", "Wait / Do nothing"}
    assert result["harvest_recommendation"]["best_window_start"] <= result["harvest_recommendation"]["best_window_end"]


def test_expected_revenue_uses_grade_weighted_price():
    result = build_revenue_intelligence("Tomato", 20, 1800, 90000, .8, .55, .6, .45, .2)
    revenue = result["revenue_optimisation"]
    assert revenue["expected_revenue_ha"] == round(20 * 10 * revenue["grade_weighted_price_quintal"])
    assert revenue["recommended_action"] == revenue["action_comparison"][0]
