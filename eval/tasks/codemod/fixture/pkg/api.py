"""Public API that uses core."""
from pkg.core import compute_total, compute_tax


def checkout(cart: list[dict], tax_rate: float) -> dict:
    subtotal = compute_total(cart)
    tax = compute_tax(subtotal, tax_rate)
    return {"subtotal": subtotal, "tax": tax, "total": compute_total(cart) + tax}
