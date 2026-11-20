def format_inr(value):
    """1,23,456.00 for 123456. Indian grouping, always two decimals."""
    if value is None:
        return "-"
    amount = round(float(value) + 1e-9, 2)
    sign = "-" if amount < 0 else ""
    whole, cents = f"{abs(amount):.2f}".split(".")
    if len(whole) > 3:
        head, tail = whole[:-3], whole[-3:]
        parts = []
        while len(head) > 2:
            parts.insert(0, head[-2:])
            head = head[:-2]
        if head:
            parts.insert(0, head)
        whole = ",".join(parts) + "," + tail
    return f"{sign}{whole}.{cents}"


def format_signed(value):
    """Used for the month on month difference, keeps the + in front."""
    if value is None:
        return "-"
    amount = round(float(value), 2)
    text = format_inr(abs(amount))
    if amount > 0:
        return "+" + text
    if amount < 0:
        return "-" + text
    return text


def format_percent(value):
    if value is None:
        return "-"
    return f"{value:+.2f}%"
