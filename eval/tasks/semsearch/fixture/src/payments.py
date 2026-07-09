"""Payment processing."""


def charge_card(amount_cents: int, token: str) -> dict:
    """Charge a card via the payment gateway."""
    return {"charged": amount_cents, "token": token[-4:]}


def issue_refund(charge_id: str, amount_cents: int) -> dict:
    return {"refunded": amount_cents, "charge": charge_id}
