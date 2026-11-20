# Online Expense Tracker

A small Flask application for recording expenses in one currency, INR, with monthly budgets per category and a dashboard for the month. Built as a software engineering course project over three Scrum sprints. The reports, backlog, design diagrams and test plan are in `docs/`.

## What you need

- Python 3.11 or newer
- Nothing else. SQLite comes with Python, Chart.js is stored in `app/static/vendor/`, and there is no build step.

## Setup and run

### Windows (PowerShell)

Run these from this folder. They call the Python inside `.venv` directly, so you do not need to activate the environment or have a global `flask` command on PATH.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m flask --app app init-db            # creates the SQLite file if it is missing
.\.venv\Scripts\python.exe -m flask --app app seed               # demo user, categories, expenses, budgets
.\.venv\Scripts\python.exe -m flask --app app reseed-demo        # restores demo sample data if it was changed or deleted
.\.venv\Scripts\python.exe -m flask --app app run                # http://127.0.0.1:5000
```

Or use the included PowerShell scripts, which do the same work:

```powershell
.\setup.ps1        # create .venv, install requirements, init db, seed demo data
.\run.ps1          # start the app (add -Debug to turn on debug mode)
.\test.ps1         # run the tests with coverage
.\reseed.ps1       # restore the demo sample data
```

If your execution policy blocks the scripts, either run `powershell -ExecutionPolicy Bypass -File .\setup.ps1` (and likewise for the others), or set it for the current session with `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`.

If you prefer activating the environment, use `.\.venv\Scripts\Activate.ps1` and then plain `flask --app app run`. The bash-style `source .venv/bin/activate` does not work in PowerShell. To turn on debug mode, use `$env:FLASK_DEBUG = "1"`; the Unix-style `FLASK_DEBUG=1` prefix is not valid in PowerShell.

### macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

flask --app app init-db            # creates the SQLite file if it is missing
flask --app app seed               # demo user, categories, expenses, budgets
flask --app app reseed-demo        # restores demo sample data if it was changed or deleted
flask --app app run                # http://127.0.0.1:5000
```

`python run.py` does the same thing. Debug mode is off by default; set `FLASK_DEBUG=1` to turn it on. The database file is `instance/expense_tracker.sqlite3`, and the schema is applied automatically the first time the app starts.

To start clean, delete that file and run `init-db` again.

## Demo login

```
username:  demo
password:  demo12345
```

The seed script gives this account 8 categories, about 50 expenses across the last 3 months and a budget for Food, Travel, Groceries and Utilities. If you edit or delete that sample data, `flask --app app reseed-demo` restores it for the demo account only; other accounts are left alone.

## Interface

The UI is plain HTML and CSS with no framework. It adapts across screen sizes: the sidebar becomes a toggleable menu below 800px, wide tables become labelled cards below 560px, and both charts resize with their containers. The dashboard shows daily spending as bars and a category pie chart with category names and percentages drawn on the slices, plus a labelled legend. Keyboard and screen-reader support includes a skip link, `aria-current` on the active page, live flash messages, labelled form fields and table cells, and visible focus rings. Print styles hide navigation and controls. Lighthouse scores 100 for accessibility, best practices and SEO on the main pages.

## Tests

```
python -m pytest --cov=app --cov-report=term-missing
```

In PowerShell, use `.\test.ps1`, or call the virtual-environment Python directly:

```powershell
.\.venv\Scripts\python.exe -m pytest --cov=app --cov-report=term-missing
```

83 tests, 91 percent line coverage. Unit tests live in `tests/unit`, integration tests in `tests/integration`. Every test case ID in `docs/test_plan.md` appears in a test name, so you can jump from the plan to the code.

## Folder layout

```
app/
  __init__.py        app factory, CSRF check, error handlers
  db.py              connection per request, applies schema.sql
  schema.sql         tables and indexes
  queries.py         every SQL statement in the project
  seed.py            demo data
  format.py          Indian grouping for amounts
  routes/            thin: read input, call a service or query, render
  services/          validation.py, budgets.py, summary.py, csv_io.py
  templates/         Jinja2 templates
  static/css         app.css, hand written
  static/js          dashboard.js
  static/vendor/     chart.umd.js, no CDN
   static/favicon.svg browser tab icon
tests/
  conftest.py
  unit/              validation, budgets, summary, csv parsing
  integration/       Flask test client against a temporary database
docs/                requirements, backlog, sprint plan, design, test plan
instance/            the SQLite file, not committed
pytest.ini
requirements.txt
run.py
setup.ps1, run.ps1, test.ps1, reseed.ps1   Windows/PowerShell helpers
```

## Notes

- Amounts are stored as `real` in SQLite. We accepted that because SQLite has no decimal type and the values are rupees with two decimals.
- All SQL sits in `app/queries.py` on purpose, so a reader can check every statement the program issues in one file.
- Passwords are hashed with werkzeug, forms carry a CSRF token, and every query filters by `user_id`.
