# Sprint plan

Three sprints of two weeks, one developer, Agile (Scrum) process. We kept the meetings short: a planning session at the start of each sprint, a five minute standup with ourselves every morning in the notebook, and a review with the faculty mentor at the end.

Capacity: we treated a working day as worth about 2.5 points, so a two week sprint holds roughly 25 points. The first sprint went over because we did not count testing as work. The numbers below are what actually happened.

## Sprint 1, weeks 1 and 2

**Goal.** A signed in user can add, read, edit and delete their own expenses, and nobody else can see them.

**Stories.** US-01 (3), US-02 (3), US-03 (5), US-04 (5), US-05 (3), US-06 (2). Total 21 points.

**Tasks.**

| ID | Task |
| --- | --- |
| T1.1 | Repository layout, app factory, requirements.txt, .gitignore |
| T1.2 | schema.sql and db.py with one connection per request |
| T1.3 | queries.py for users, categories and expenses |
| T1.4 | Password hashing with werkzeug and the session login |
| T1.5 | CSRF token check in before_request |
| T1.6 | Login, register and expense forms with inline errors |
| T1.7 | Sidebar layout and the dense ruled expense table |
| T1.8 | Delete confirm page |
| T1.9 | Seed script with demo data |
| T1.10 | Coverage report command |

**Finished.** All six stories and tasks T1.1 to T1.9. The list page was shown at the review with 45 seeded rows.

**Moved to sprint 2.** T1.10, the coverage report. We thought configuring pytest-cov was a fifteen minute job and it turned out we also wanted a config file, a target and a command in the README. It was picked up as task T3.8.

**Review notes.** The mentor logged in as the demo user, added an expense from the full form and then asked why there was no way to get back to the list with the values kept. We had already kept the values, but the error text was above the form instead of under the field, so we moved every error under its input that evening.

**Retrospective.**

Went well: the schema and the query file were written before any template, so no template ever had to invent a column name. Tests were written with each story instead of at the end, which meant we finished the sprint with 31 passing tests.

Did not go well: we estimated US-03 at 3 points on day one and had to raise it to 5 on day three, once amount validation covered zero, negative, non numeric and very large values. That ate the slack we had planned for the coverage work.

What we change: estimates now include the tests, and we write the test case IDs before writing the test.

**Burndown, remaining points by day.**

| Day | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Remaining | 21 | 18 | 15 | 12 | 12 | 9 | 6 | 6 | 3 | 0 |
| Ideal | 21 | 19 | 17 | 14 | 12 | 10 | 8 | 5 | 3 | 0 |

## Sprint 2, weeks 3 and 4

**Goal.** Categories can be managed safely, a monthly budget can be set per category, and the list page can be filtered, searched, sorted and paged.

**Stories.** US-07 (3), US-08 (5), US-09 (5), US-10 (5), US-11 (3), US-12 (3). Total 24 points.

**Tasks.**

| ID | Task |
| --- | --- |
| T2.1 | Category add, rename and list with expense counts |
| T2.2 | Delete blocked while in use, with the move step |
| T2.3 | Budgets table with the unique key on user, category and month |
| T2.4 | Budget page with the progress bars |
| T2.5 | Filter parameters on the list query and the filter row |
| T2.6 | Note search and sort by date or amount |
| T2.7 | Pagination at 15 rows with clamping |
| T2.8 | Quick add form above the table |
| T2.9 | Budget state unit tests at the boundaries |
| T2.10 | Export link on the list page |

**Finished.** All six stories and tasks T2.1 to T2.9. The budget page at the review showed a green, an ochre and a brick bar at the same time, which is what we wanted the reviewer to see.

**Moved to sprint 3.** T2.10. The link had nowhere to point because the export route was a sprint 3 story, so we stopped pretending it was sprint 2 work.

**Review notes.** The mentor tried to delete Groceries while it held 14 expenses and expected the app to lose them. It did not, and the move form showed the count, which was the right behaviour. The comment we took away was that the filter row stacked into six lines at 768px, so we changed it to wrap in one row.

**Retrospective.**

Went well: the budget state function was written with its tests in one sitting, and the 80 and 100 percent cases were decided before the CSS existed. Nothing about the colour thresholds was left to the template.

Did not go well: the delete category bug (DEF-003) was a 500 page in front of the mentor. We had tested the happy path only. The filter row overflow was also found in the review instead of during the week.

What we change: every route gets one test that calls it the way a user would, including the refusal path, and we open the pages at 360, 768 and 1280 every day rather than before a review.

**Burndown, remaining points by day.**

| Day | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Remaining | 24 | 22 | 19 | 16 | 13 | 13 | 9 | 6 | 3 | 0 |
| Ideal | 24 | 21 | 19 | 16 | 14 | 12 | 9 | 7 | 5 | 0 |

## Sprint 3, weeks 5 and 6

**Goal.** The month can be read at a glance on the dashboard, and data can come in and go out as CSV, with the tests cleaned up at the end.

**Stories.** US-13 (8), US-14 (3), US-15 (3), US-16 (6), US-17 (2), US-18 (4), plus task T2.10 carried over. Total 26 points.

**Tasks.**

| ID | Task |
| --- | --- |
| T3.1 | summary.py with month totals and the comparison |
| T3.2 | Dashboard template: month bar, big total, two columns |
| T3.3 | Chart.js copied into static/vendor and the daily chart |
| T3.4 | CSV export route reusing the list query |
| T3.5 | CSV import upload, preview table, per row errors, confirm |
| T3.6 | Change password page |
| T3.7 | Empty states, 404, 400 and 500 pages |
| T3.8 | Coverage report and test cleanup |
| T3.9 | Indexes in schema.sql and a timing check at 5000 rows |
| T3.10 | Export link on the list page (from sprint 2) |

**Finished.** All six stories and all ten tasks. The timing check put the filtered list at about 180 ms against 5000 rows in a local database, which is inside the 500 ms we wrote in NFR-2.

**Moved to the backlog.** Deleting a budget. We wrote it as a task out of habit and then noticed the backlog never asked for it, so we removed the task instead of building an untested screen. Setting a new amount for the same category and month updates the row, which covers the real need.

**Review notes.** Two comments we acted on. The month difference needed a label, so we added "against last month" beside the figure. The import preview needed the line number of each row from the file, not a running count of valid rows, so `line_no` was added to the parsed row and shown as its own column.

**Retrospective.**

Went well: splitting the chart out of the dashboard story kept US-13 at a size we could finish, and the dashboard was demoed with real seeded data on the first day of week six.

Did not go well: CSV import was estimated at 3 points before the preview step and re-estimated to 6, and it still took most of four days. The coverage run was left until the last day, which is how DEF-001 and DEF-004 were found under time pressure. We also found that the register route redirected to an endpoint that no longer existed (DEF-002) only because a test followed the redirect.

What we change: reserve the last two days of every sprint for tests and refactoring only, and run the full suite with coverage on every commit instead of once at the end.

**Burndown, remaining points by day.**

| Day | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Remaining | 26 | 24 | 21 | 18 | 15 | 12 | 10 | 7 | 4 | 0 |
| Ideal | 26 | 23 | 20 | 18 | 15 | 13 | 10 | 8 | 5 | 0 |

## Where the estimates were wrong

We kept a note of every re-estimate so the report can say what changed.

| Story | First estimate | Final | Why |
| --- | --- | --- | --- |
| US-03 add expense | 3 | 5 | Amount rules covered more cases than we expected, including the very large value |
| US-09 budgets | 3 | 5 | Progress bar states, thresholds and the set form were three pieces of work, not one |
| US-16 CSV import | 3 | 6 | The preview table with an error per row is most of the feature |
| US-13 dashboard | 13 | 8 | Split: the chart became US-14 at 3 points, the rest came down to 8 |
