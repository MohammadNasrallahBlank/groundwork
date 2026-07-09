"""HTTP routes for Shipping."""
from core.exceptions import to_response
from domains.shipping.service import ShippingService
from middleware.throttle import throttle_request

service = ShippingService()


@throttle_request(cost=1)
def get_shipping(request: dict) -> dict:
    try:
        return {"status": 200, "data": service.fetch(request["id"]).__dict__}
    except Exception as e:  # noqa: BLE001
        return to_response(e)


@throttle_request(cost=2)
def create_shipping(request: dict) -> dict:
    new_id = service.register(request["name"])
    return {"status": 201, "id": new_id}
