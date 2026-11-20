# Software Requirements Specification

Online Expense Tracker, single currency (INR). Prepared for the software engineering course project, revision 1.4.

## 1. Problem statement

Students and salaried people often track spending in a notebook or in a spreadsheet that grows until nobody opens it. Both approaches fail at the same place: at the end of the month nobody can say how much was spent in which category, and whether that is more or less than the month before. We are building a small web application where a person signs in, records expenses as they happen, sets a monthly limit per category, and sees one page that answers the month questions. The system is meant for one currency, INR, because adding exchange rates and multi-currency conversion would add work that the course does not ask for and that our team cannot test properly in three sprints.

## 2. Scope

### In scope

- Account registration, login, logout, password change.
- Expense create, read, update, delete with a confirm step.
- Expense listing with filters on date range, category and payment method, note search, sort by date or amount, and pagination at 15 rows per page.
- A quick-add form placed above the expense table.
- Categories: a default set, user added ones, rename, and delete that is blocked while expenses still use the category.
- Monthly budget per category with a progress bar that changes colour at 80 percent and 100 percent.
- Dashboard with a month switcher, total spent, difference from the previous month, spending per category, daily spending chart, five recent expenses, and the list of categories over budget.
- CSV export of the list as it is currently filtered, and CSV import with a preview, per row errors and a confirm step.
- Flash messages, inline field errors, empty states, 404 and 500 pages.
- Seed script with one demo user, eight categories, about fifty expenses across three months and some budgets.

### Out of scope

- More than one currency, currency conversion, or any symbol other than the rupee.
- Income tracking, savings goals, recurring expenses, splitting bills with other people.
- Email, password reset by mail, social login, two factor login.
- Roles or an administrator account. Every signed in user sees only their own data.
- Mobile applications, offline use, printing reports, PDF export.
- Notifications and reminders of any kind.
- Deployment to a public server. We run it locally for the course.

## 3. Actors

| Actor | What they do |
| --- | --- |
| Guest | Registers an account and signs in. Sees nothing else. |
| Signed in user | Adds, edits and deletes expenses, manages categories and budgets, reads the dashboard, imports and exports CSV. |
| Seed script | Not a person. It fills a fresh database so demos and tests have data. |

There is one human actor with two states. We keep the table anyway because the guest and the signed in user see different pages and our use case diagram needs both.

## 4. Functional requirements

### Accounts

- **FR-1** The system shall let a guest register with a username and a password of at least 8 characters. A username that already exists is rejected with a message on the field.
- **FR-2** The system shall let a registered user log in and log out. The login state is held in the server session.
- **FR-3** The system shall let a signed in user change their password after supplying the current one.
- **FR-4** The system shall require a valid CSRF token on every form that changes data.

### Expenses

- **FR-5** The system shall let a user add an expense with amount, category, date, payment method and an optional note.
- **FR-6** The system shall let a user edit any field of an expense they own.
- **FR-7** The system shall let a user delete an expense only after a confirm step.
- **FR-8** The system shall reject an amount that is zero, negative, non numeric or larger than 99999999 with a message under the field.
- **FR-9** The system shall reject a date that cannot be parsed or falls outside 2000-01-01 to 2100-12-31.
- **FR-10** The list page shall filter by date range, category and payment method, search inside the note, and sort by date or amount in either direction.
- **FR-11** The list page shall show 15 expenses per page and provide previous and next links with a page count.
- **FR-12** The list page shall include a quick-add form above the table that adds an expense and returns to the same filters.

### Categories and budgets

- **FR-13** The system shall create a fresh account with a default set of eight categories.
- **FR-14** The system shall let a user add a category and rename an existing one.
- **FR-15** The system shall refuse to delete a category that still has expenses and shall ask the user which other category should receive them.
- **FR-16** The system shall let a user move all expenses of one category into another in a single action.
- **FR-17** The system shall store one monthly budget per category per month and show a progress bar for spent against budget.
- **FR-18** The progress bar shall turn ochre at 80 percent of the budget and brick at 100 percent or above.

### Dashboard and data

- **FR-19** The dashboard shall show the month on request through a previous and next control and refuse to move past the current month.
- **FR-20** The dashboard shall show the total for the month and the difference from the previous month in rupees and in percent.
- **FR-21** The dashboard shall show spending per category for the month and the five most recent expenses.
- **FR-22** The dashboard shall list every category that is over its budget for that month.
- **FR-23** The dashboard shall plot daily spending for the month as a chart.
- **FR-24** The export shall write a CSV of the expense list exactly as it is currently filtered and sorted.
- **FR-25** The import shall show a preview of the uploaded rows before anything is written and report an error per row for a bad date, an amount that is not positive, or an unknown category.
- **FR-26** The import shall write only the rows marked valid, after the user confirms.

### Feedback and edges

- **FR-27** Successful actions shall show a short flash message, for example "Expense added".
- **FR-28** Invalid fields shall show an inline message under the field and keep the values the user typed.
- **FR-29** Empty pages shall show one plain sentence instead of an empty table.
- **FR-30** Unknown URLs shall render a 404 page and unexpected server errors a 500 page.

## 5. Non-functional requirements

| ID | Type | Requirement |
| --- | --- | --- |
| NFR-1 | Usability | Every form has its label above the field, an example placeholder such as "Auto fare to college", a visible focus ring, and inline error text in brick red. All screens work at 360px, 768px and 1280px width. |
| NFR-2 | Performance | The list, filter and dashboard pages shall answer in under 500 ms against a local database holding 5000 expenses. Date range, category and sort are covered by indexes in the schema. |
| NFR-3 | Security | Passwords are stored as hashes, never plain text. The session cookie is HttpOnly and sent only over the session interface. Every state changing POST carries a CSRF token. A user can only read or change rows that belong to them, checked in SQL, not in the template. |
| NFR-4 | Portability | The application runs on Python 3.11 or newer on Linux, macOS and Windows with one command, using SQLite from the standard library. There is no external server, no build step and no network dependency at runtime. Chart.js is stored in the project, not fetched from a CDN. |
| NFR-5 | Maintainability | Routes stay thin and only read input, call a service or query function and render a template. All SQL lives in `app/queries.py`, so a reader can check every statement the program issues in one file. |
| NFR-6 | Testability | Unit and integration tests run with one command and report at least 80 percent line coverage. Every test case in the test plan appears in a test name or in a comment next to it. |

## 6. Assumptions

- One user works at one time on one browser. We do not handle two tabs writing the same expense together.
- All money is INR and always shown with two decimals in Indian grouping, for example 1,23,456.00.
- Dates are entered and stored as YYYY-MM-DD and shown as the user's local date, with no time zone handling.
- The person using it can read English labels.
- The database file lives on the same machine as the server.

## 7. Constraints

- Flask, plain `sqlite3`, Jinja2 templates, hand written CSS, minimal vanilla JavaScript, Chart.js stored locally.
- No ORM, no CSS framework, no JavaScript framework, no icon pack, no emoji.
- Three sprints of two weeks, one developer, so the total capacity is about 70 story points.
- No named design patterns. Plain functions first, and a class only where it is clearly the easiest option.
- The report and the code must use plain language, and the documents must say what went wrong, not only what went right.

## 8. Risks

| Risk | Effect | What we do |
| --- | --- | --- |
| CSV data from a bank app does not match our columns | Import fails and the user loses interest | Preview with per row errors, import only valid rows, and a sample file in the docs. |
| Filters and pagination interact badly with export | Exported rows differ from the screen | The export reuses the same query function as the list, so there is one path to test. |
| Budget colour thresholds are easy to break in a refactor | Bar shows the wrong colour at exactly 80 or 100 percent | Boundary tests at 79.99, 80, 99.99, 100 and 120 percent in `tests/unit`. |
| SQLite locks the file when two requests write together | A write fails during a demo | One connection per request, short transactions, and a demo run on a copy of the database. |
| Scope grows in sprint 3 because the dashboard is the showpiece | Tests get rushed | Dashboard was split in the backlog, and polishing tasks were moved out on purpose. |
