"""Core totals logic."""


def compute_total(items: list[dict]) -> int:
    """Sum the price*qty of every line item, in cents."""
    return sum(i["price"] * i["qty"] for i in items)


def compute_tax(subtotal: int, rate: float) -> int:
    return round(subtotal * rate)
