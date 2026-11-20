from app.services.budgets import bar_width, budget_row, budget_state, percent_used


def test_TC_011_budget_at_exactly_80_percent_is_ochre():
    assert budget_state(800, 1000) == "warn"
    assert percent_used(800, 1000) == 80.0


def test_TC_012_budget_at_exactly_100_percent_is_brick():
    assert budget_state(1000, 1000) == "over"
    assert budget_state(1000.0, 1000) == "over"


def test_TC_013_budget_just_below_80_percent_is_normal():
    assert budget_state(799, 1000) == "ok"
    assert percent_used(799, 1000) == 79.9


def test_TC_014_budget_way_over_is_capped_at_100_percent_width():
    assert budget_state(1500, 1000) == "over"
    assert bar_width(1500, 1000) == 100.0
    assert percent_used(1500, 1000) == 150.0


def test_TC_015_category_without_budget_has_no_state():
    assert budget_state(900, 0) == "none"
    assert bar_width(900, 0) == 0.0


def test_budget_row_carries_display_fields():
    row = budget_row(
        {"category_id": 1, "category_name": "Food", "budget": 4000.0, "spent": 4320.0, "month": "2026-03", "id": 7}
    )
    assert row["state"] == "over"
    assert row["percent"] == 108.0
    assert row["width"] == 100.0
    assert row["left"] == -320.0
    assert row["label"] == "over budget"
