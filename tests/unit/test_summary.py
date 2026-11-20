from app.services.summary import build_month_summary, comparison, daily_series, shift_month


def test_TC_016_comparison_positive_difference():
    diff, percent = comparison(18400, 15000)
    assert diff == 3400.0
    assert percent == 22.67


def test_TC_017_comparison_negative_difference():
    diff, percent = comparison(9000, 12000)
    assert diff == -3000.0
    assert percent == -25.0


def test_TC_018_comparison_without_previous_month():
    diff, percent = comparison(5000, None)
    assert diff is None
    assert percent is None

    # Previous month exists but nothing was spent in it, so a percent would divide by zero.
    diff, percent = comparison(5000, 0)
    assert diff == 5000.0
    assert percent is None


def test_TC_019_daily_series_covers_every_day_of_the_month():
    totals = [{"day": "05", "total": 120.0}]
    series = daily_series(1, "2026-02", totals)
    assert len(series) == 28
    assert series[4] == 120.0
    assert series[0] == 0

    assert len(daily_series(1, "2026-01", [])) == 31
    assert len(daily_series(1, "2024-02", [])) == 29


def test_TC_020_month_shift_crosses_the_year_boundary():
    assert shift_month("2026-01", -1) == "2025-12"
    assert shift_month("2025-12", 1) == "2026-01"
    assert shift_month("2026-03", -3) == "2025-12"


def test_build_month_summary_returns_the_dashboard_fields(app, auth):
    from app import queries

    with app.app_context():
        user_id = queries.create_user("sum", "hash")
        queries.create_default_categories(user_id)
        categories = queries.list_categories(user_id)
        queries.insert_expense(
            user_id,
            {
                "category_id": categories[0]["id"],
                "amount": 18400.0,
                "date": "2026-03-04",
                "payment_method": "UPI",
                "note": "Hostel mess",
            },
        )
        queries.insert_expense(
            user_id,
            {
                "category_id": categories[1]["id"],
                "amount": 15000.0,
                "date": "2026-02-10",
                "payment_method": "cash",
                "note": "Bus pass",
            },
        )
        queries.set_budget(user_id, categories[0]["id"], "2026-03", 16000.0)

        summary = build_month_summary(user_id, "2026-03")

    assert summary["total"] == 18400.0
    assert summary["previous_total"] == 15000.0
    assert summary["difference"] == 3400.0
    assert summary["percent"] == 22.67
    assert summary["label"] == "March 2026"
    assert len(summary["daily"]) == 31
    assert summary["over_budget"][0]["category_name"] == "Entertainment"
    assert summary["recent"][0]["date"] == "2026-03-04"


def test_daily_chart_values_land_on_the_right_day(app):
    """A 2026-03-04 expense belongs to day 04, not to the year prefix '20'."""
    from app import queries

    with app.app_context():
        user_id = queries.create_user("daily", "hash")
        queries.create_default_categories(user_id)
        category = queries.list_categories(user_id)[0]
        queries.insert_expense(
            user_id,
            {
                "category_id": category["id"],
                "amount": 250.0,
                "date": "2026-03-04",
                "payment_method": "cash",
                "note": "Hostel mess",
            },
        )
        rows = queries.month_daily_totals(user_id, "2026-03")
        assert rows == [{"day": "04", "total": 250.0}]

        summary = build_month_summary(user_id, "2026-03")
        assert summary["daily"][3] == 250.0
        assert sum(summary["daily"]) == 250.0
