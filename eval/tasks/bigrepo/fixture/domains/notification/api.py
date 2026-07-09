"""HTTP routes for Notification."""
from core.exceptions import to_response
from domains.notification.service import NotificationService
from middleware.throttle import throttle_request

service = NotificationService()


@throttle_request(cost=1)
def get_notification(request: dict) -> dict:
    try:
        return {"status": 200, "data": service.fetch(request["id"]).__dict__}
    except Exception as e:  # noqa: BLE001
        return to_response(e)


@throttle_request(cost=2)
def create_notification(request: dict) -> dict:
    new_id = service.register(request["name"])
    return {"status": 201, "id": new_id}
