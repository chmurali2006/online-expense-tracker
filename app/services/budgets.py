"""Budget progress bar states. Ochre at 80 percent, brick at 100 percent."""


def percent_used(spent, budget):
    if not budget:
        return 0.0
    return round(float(spent) / float(budget) * 100.0, 2)


def bar_width(spent, budget):
    """The bar never runs past the end of the track."""
    if not budget:
        return 0.0
    return min(percent_used(spent, budget), 100.0)


def budget_state(spent, budget):
    if not budget:
        return "none"
    used = float(spent) / float(budget)
    if used >= 1.0:
        return "over"
    if used >= 0.8:
        return "warn"
    return "ok"


def state_label(state):
    return {"none": "no budget", "ok": "under budget", "warn": "nearly there", "over": "over budget"}[state]


def budget_row(row):
    """Takes a row from queries.budgets_for_month and adds the display fields."""
    state = budget_state(row["spent"], row["budget"])
    return {
        **row,
        "state": state,
        "label": state_label(state),
        "percent": percent_used(row["spent"], row["budget"]),
        "width": bar_width(row["spent"], row["budget"]),
        "left": round(float(row["budget"]) - float(row["spent"]), 2),
    }


def over_budget_rows(rows):
    return [budget_row(row) for row in rows if budget_state(row["spent"], row["budget"]) == "over"]
