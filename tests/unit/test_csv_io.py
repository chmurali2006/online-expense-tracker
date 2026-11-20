from app.services.csv_io import build_export, parse_csv, valid_rows

CATEGORIES = [
    {"id": 1, "name": "Food"},
    {"id": 2, "name": "Travel"},
    {"id": 3, "name": "Groceries"},
]

GOOD = "date,category,amount,payment_method,note\n2026-03-04,Food,180.00,UPI,Canteen lunch\n"


def test_TC_021_import_reports_a_reason_for_each_bad_row():
    text = (
        "date,category,amount,payment_method,note\n"
        "04-03-2026,Food,180.00,UPI,Bad date\n"
        "2026-03-05,Food,-5.00,UPI,Negative amount\n"
        "2026-03-06,Health,90.00,cash,Unknown category\n"
        "2026-03-07,Travel,45.00,cash,Auto fare to college\n"
    )
    ok, rows, error = parse_csv(text, CATEGORIES)
    assert ok and error is None
    assert len(rows) == 4
    assert rows[0]["error"] == "Bad date, use YYYY-MM-DD"
    assert rows[1]["error"] == "Amount must be more than 0"
    assert rows[2]["error"] == "Unknown category"
    assert rows[3]["error"] is None
    assert [row["line_no"] for row in rows] == [2, 3, 4, 5]
    assert len(valid_rows(rows)) == 1


def test_TC_022_empty_csv_is_rejected():
    ok, rows, error = parse_csv("", CATEGORIES)
    assert not ok
    assert rows == []
    assert error == "The file is empty"


def test_TC_023_wrong_header_is_rejected():
    ok, rows, error = parse_csv("Date;Category;Amount\n2026-03-04;Food;10\n", CATEGORIES)
    assert not ok
    assert error == "Header must be date,category,amount,payment_method,note"

    ok, rows, error = parse_csv("something\nelse\n", CATEGORIES)
    assert not ok


def test_TC_024_only_clean_rows_are_marked_valid():
    text = (
        "date,category,amount,payment_method,note\n"
        "2026-03-04,Food,180.00,UPI,Canteen lunch\n"
        "2026-03-05,Food,abc,UPI,Not a number\n"
        "2026-03-06,Food,60.00,cheque,Bad method\n"
    )
    ok, rows, _ = parse_csv(text, CATEGORIES)
    assert ok
    good = valid_rows(rows)
    assert len(good) == 1
    assert good[0]["category_id"] == 1
    assert good[0]["date"] == "2026-03-04"
    assert good[0]["payment_method"] == "UPI"


def test_TC_025_export_uses_our_header_and_row_order():
    rows = [
        {
            "date": "2026-03-05",
            "category_name": "Travel",
            "amount": 45.0,
            "payment_method": "cash",
            "note": "Auto fare to college",
        },
        {
            "date": "2026-03-04",
            "category_name": "Food",
            "amount": 180.5,
            "payment_method": "UPI",
            "note": "Canteen lunch",
        },
    ]
    text = build_export(rows)
    lines = text.strip().split("\n")
    assert lines[0] == "date,category,amount,payment_method,note"
    assert lines[1] == "2026-03-05,Travel,45.00,cash,Auto fare to college"
    assert lines[2].startswith("2026-03-04,Food,180.50")


def test_export_neutralises_spreadsheet_formulas():
    rows = [
        {
            "date": "2026-03-04",
            "category_name": "Food",
            "amount": 10.0,
            "payment_method": "cash",
            "note": '=HYPERLINK("http://evil","click")',
        }
    ]
    text = build_export(rows)
    assert "'=HYPERLINK" in text
    assert '=HYPERLINK("http://evil","click")' not in text


def test_csv_note_length_is_checked():
    ok, rows, _ = parse_csv(GOOD.replace("Canteen lunch", "x" * 201), CATEGORIES)
    assert ok
    assert rows[0]["error"] == "Note is too long, 200 characters maximum"
    assert not valid_rows(rows)


def test_csv_round_trip():
    ok, rows, _ = parse_csv(GOOD, CATEGORIES)
    assert ok and valid_rows(rows)
    assert build_export(
        [
            {
                "date": "2026-03-04",
                "category_name": "Food",
                "amount": 180.0,
                "payment_method": "UPI",
                "note": "Canteen lunch",
            }
        ]
    ).split("\n")[1].startswith("2026-03-04")
