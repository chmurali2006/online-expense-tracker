# Test plan

Version 2, written after sprint 3. This is the document we checked the test suite against.

## 1. Strategy

We split the tests the same way we split the code. Unit tests sit under `tests/unit` and call one function at a time with no server and no database, so they run in a fraction of a second and tell us which rule broke. Integration tests sit under `tests/integration` and drive a real Flask test client against a temporary SQLite file created for each test, so they cover the routes, the templates, the session and the CSRF check together.

Every test case below has an ID, and the ID appears in the test function name, so a reviewer can go from this table to the code in one search. We did not write a separate test case for each screen reader rule or for browser differences; the course asked for behaviour, not compliance testing.

Manual checks we do before a submission: the pages at 360px, 768px and 1280px width, the chart rendering with the local Chart.js file, and the seed script on a fresh database.

## 2. Scope

Inside the scope: all functional requirements FR-1 to FR-30 from requirements.md, the budget colour thresholds at exactly 80 and 100 percent, access control between two users, CSV import error reporting, and pagination boundaries.

Outside the scope: load and stress testing beyond one measurement at 5000 rows, cross browser testing other than Chromium and Firefox, security testing by an outsider, and accessibility audits. We note these in the limitations section of the README.

## 3. Environment

| Item | Value |
| --- | --- |
| Python | 3.11.2 on Linux |
| Flask | 3.1.3 |
| pytest / pytest-cov | 9.2.0 / 7.1.0 |
| Database | SQLite 3, one temporary file per test |
| Command | `python -m pytest --cov=app --cov-report=term-missing` |
| Result | 83 passed, 91 percent line coverage |

## 4. Test cases

The plan asked for about 35 cases. We ended with 51 because traceability pulled in extra rows for the budget thresholds and the import paths, and we preferred to keep them rather than delete passing tests.

| ID | Req. | What we check | Input | Expected | Actual | Status |
| --- | --- | --- | --- | --- | --- | --- |
| TC-001 | FR-8 | Amount of 0 is refused | amount `0` | "Amount must be more than 0" | same | Pass |
| TC-002 | FR-8 | Smallest allowed amount | amount `0.01` | accepted as 0.01 | same | Pass |
| TC-003 | FR-8 | Very large amount | amount `1000000000000` | "Amount is too large" | same | Pass |
| TC-004 | FR-8 | Negative amount | amount `-45.50` | refused as not positive | same | Pass |
| TC-005 | FR-8 | Non numeric amount | amount `abc` | "Amount must be a number" | same | Pass |
| TC-006 | FR-9 | Date in the wrong format | date `31/02/2026` | "Use the date format YYYY-MM-DD" | same | Pass |
| TC-007 | FR-9 | Date outside the allowed range | date `1999-05-05` | range message, date `2026-13-01` also refused | same | Pass |
| TC-008 | FR-1 | Password shorter than 8 and mismatched confirm | password `short` | inline message under the field | same | Pass |
| TC-009 | FR-14 | Category name already used | name `Food` when `food` exists | duplicate message | same | Pass |
| TC-010 | FR-17 | Budget amount not positive | budget `-100` | "Budget must be more than 0" | same | Pass |
| TC-011 | FR-18 | Budget at exactly 80 percent | spent 800 of 1000 | state warn, ochre | state warn, 80.0 percent | Pass |
| TC-012 | FR-18 | Budget at exactly 100 percent | spent 1000 of 1000 | state over, brick | state over | Pass |
| TC-013 | FR-18 | Just below the warning line | spent 799 of 1000 | state ok, green | 79.9 percent, ok | Pass |
| TC-014 | FR-18 | Far above the limit | spent 1500 of 1000 | over, bar capped at 100 percent | 150 percent, width 100 | Pass |
| TC-015 | FR-17 | Category with no budget | budget 0 | no state, empty bar | none, width 0 | Pass |
| TC-016 | FR-20 | Month on month up | 18400 against 15000 | +3400.00 and +22.67 percent | same | Pass |
| TC-017 | FR-20 | Month on month down | 9000 against 12000 | -3000.00 and -25.00 percent | same | Pass |
| TC-018 | FR-20 | First month with no history | previous month missing or 0 | no percent shown | difference set, percent None | Pass |
| TC-019 | FR-23 | Daily series covers the whole month | February, one value on day 5 | 28 values, zeros elsewhere | 28, leap year 29 | Pass |
| TC-020 | FR-19 | Month switcher crossing a year | 2026-01 with -1 | 2025-12 | same | Pass |
| TC-021 | FR-25 | Bad rows reported one by one | 4 rows: bad date, -5, unknown category, good | 3 errors with reasons, 1 valid | same | Pass |
| TC-022 | FR-25 | Empty CSV | file with no content | "The file is empty" | same | Pass |
| TC-023 | FR-25 | Wrong header | `Date;Category;Amount` | header message | same | Pass |
| TC-024 | FR-26 | Only clean rows marked valid | good row, `abc` amount, `cheque` method | 1 valid of 3 | same | Pass |
| TC-025 | FR-24 | Export header and row order | two known rows | exact header and rows | same | Pass |
| TC-026 | FR-1 | Register a new account | username `riya`, password `secret123` | redirect to the list, 8 default categories, hash not plain text | same | Pass |
| TC-027 | FR-1 | Duplicate registration | same username twice | "Username already taken", one account only | same | Pass |
| TC-028 | FR-2 | Wrong password | correct user, wrong password | "Wrong username or password" on the same page | same | Pass |
| TC-029 | FR-2 | Logout ends the session | logout then open the list | redirected to the login page | same | Pass |
| TC-030 | FR-4 | POST without a CSRF token | form with no token, and a wrong token | 400 both times | 400 both times | Pass |
| TC-031 | FR-3 | Change password with a wrong current one | wrong current, then correct | error first, old password stops working after the change | same | Pass |
| TC-032 | FR-5 | Add a valid expense | 250, Food, UPI, note | "Expense added", row in the list | same | Pass |
| TC-033 | FR-8, FR-28 | Add with amount 0 | amount `0` | inline error, nothing written, other fields kept | same | Pass |
| TC-034 | FR-6 | Edit an expense | change amount to 150 and note | "Expense updated"; empty amount refused | same | Pass |
| TC-035 | FR-7 | Delete needs a confirm step | open the confirm page, then post | page shows the row, nothing removed until the post | same | Pass |
| TC-036 | NFR-3 | Another user's expense | user B opens user A's edit and delete URLs | 404 and the row still exists | same | Pass |
| TC-037 | FR-10 | Filters by date range, category and method | three expenses over two months | correct counts, empty filter message | same | Pass |
| TC-038 | FR-10 | Search in the note and sort by amount | `q=fare`, amount desc and asc | one row; 900 before 75 | same | Pass |
| TC-039 | FR-11 | Pagination boundaries | 31 rows, pages 1, 2, 3, `page=0`, `page=99` | 15 rows per page, page clamped, no blank page | same | Pass |
| TC-040 | FR-12 | Quick add keeps the filters | post to `?method=UPI&sort=amount` | row saved, same filter and order kept | same | Pass |
| TC-041 | FR-15, FR-16 | Category in use cannot be deleted | 3 expenses in Food | asks for a target, refuses an empty choice, then moves all 3 | same | Pass |
| TC-042 | FR-14 | Rename and add a category | rename Food to Meals, duplicate Travel, add Metro card | rename works, duplicate refused, new one listed | same | Pass |
| TC-043 | FR-18 | Progress bar colour at 79.9, 80 and 100 percent | budget 1000, spend 799 then 800 then 1000 | green, ochre, brick in that order | same | Pass |
| TC-044 | FR-19, FR-20, FR-22, FR-23 | Dashboard for a month with two months of data | 18400 this month, 15000 last, budget 16000 | total 18,400.00, +3,400.00, +22.67 percent, over budget list, chart script tag | same | Pass |
| TC-045 | FR-30 | Unknown URL | `/this/does/not/exist` | 404 page with a link back | same | Pass |
| TC-046 | FR-29 | Empty list | new account, no expenses | one sentence, no `<tbody>` | same | Pass |
| TC-047 | FR-30 | Server error page | list query raises | 500 page rendered | same | Pass |
| TC-048 | FR-24 | Export follows the active filters | method cash and a March range | only matching rows, attachment header | same | Pass |
| TC-049 | FR-25, FR-26 | Import preview then confirm | 5 rows, 3 bad | preview counts, nothing written, then "2 added, 3 skipped" | same | Pass |
| TC-050 | FR-25 | Empty file, wrong header, no file, not a CSV | four uploads | four different messages, 0 rows written | same | Pass |
| TC-051 | FR-26 | Cancel the import | cancel after preview | nothing written, preview gone, a later confirm does nothing | same | Pass |

## 5. Requirement to test traceability

| Requirement | Test cases |
| --- | --- |
| FR-1 register | TC-008, TC-026, TC-027 |
| FR-2 login and logout | TC-028, TC-029 |
| FR-3 change password | TC-031, TC-036 |
| FR-4 CSRF on forms | TC-030, TC-028 |
| FR-5 add expense | TC-032, TC-040 |
| FR-6 edit expense | TC-034, TC-036 |
| FR-7 delete with confirm | TC-035, TC-036 |
| FR-8 amount rules | TC-001 to TC-005, TC-033 |
| FR-9 date rules | TC-006, TC-007 |
| FR-10 filter, search, sort | TC-037, TC-038 |
| FR-11 pagination | TC-039 |
| FR-12 quick add | TC-040 |
| FR-13 default categories | TC-026, TC-042 |
| FR-14 add and rename category | TC-009, TC-042 |
| FR-15 delete blocked in use | TC-041 |
| FR-16 move expenses | TC-041 |
| FR-17 budget per category | TC-010, TC-015, TC-043 |
| FR-18 colour thresholds | TC-011, TC-012, TC-013, TC-014, TC-043 |
| FR-19 month switcher | TC-020, TC-044 |
| FR-20 month comparison | TC-016, TC-017, TC-018, TC-044 |
| FR-21 per category and recent | TC-044 |
| FR-22 over budget list | TC-043, TC-044 |
| FR-23 daily chart | TC-019, TC-044 |
| FR-24 CSV export | TC-025, TC-048 |
| FR-25 import preview and errors | TC-021, TC-022, TC-023, TC-049, TC-050 |
| FR-26 import only valid rows | TC-024, TC-049, TC-051 |
| FR-27 flash messages | TC-032, TC-034, TC-042 |
| FR-28 inline errors | TC-033, TC-008 |
| FR-29 empty states | TC-046 |
| FR-30 404 and 500 | TC-045, TC-047 |
| NFR-1 usable at three widths | manual check, not automated |
| NFR-2 performance on a few thousand rows | manual check with 5000 rows, page under 500 ms |
| NFR-3 passwords, sessions, ownership | TC-026, TC-029, TC-030, TC-036 |
| NFR-6 coverage above 80 percent | the coverage command in section 3 |

## 6. Defect log

| ID | Found by | What happened | Cause | Fix |
| --- | --- | --- | --- | --- |
| DEF-001 | TC-025 | Exported files opened with a blank last line and our own row checks failed on the line endings | `csv.writer` writes `\r\n` by default | Pass `lineterminator="\n"` when building the export |
| DEF-002 | TC-026 | After registering, the browser showed a 500 instead of the expense list | The route redirected to an endpoint that did not exist after we renamed the list view during the first refactor | Redirect with `url_for("expenses.list")` and added the register step to the integration tests so a broken redirect fails the build |
| DEF-003 | TC-041 | Deleting a category that still held expenses returned a 500 and left rows pointing at a removed category | The first version deleted the row before counting its expenses, and SQLite refused with a foreign key error | Count first, show the move form, and only delete after the expenses have been moved in one statement |
| DEF-004 | TC-019, TC-044 | The daily chart drew one bar for each day that had spending, so March showed 6 bars and the axis lost its shape | The query returns grouped rows and we passed them straight to the chart | `daily_series` now returns one value for every day of the month and fills the gaps with 0 |

## 7. Running the suite

```
python -m pytest --cov=app --cov-report=term-missing
```

83 tests pass. Coverage is 91 percent, above the 80 percent we set as the floor in NFR-6. Lighthouse reports 100 for accessibility, best practices and SEO on the main pages. The files we read when a test fails are `tests/conftest.py` first, then the service the test calls, then `app/queries.py` if the numbers come back wrong.
