"""Application wiring: routes -> handlers, through the middleware chain."""
from middleware.error_handler import handle
from middleware.request_logging import log_request
from domains.user.api import get_user, create_user
from domains.product.api import get_product, create_product
from domains.order.api import get_order, create_order
from domains.cart.api import get_cart, create_cart
from domains.payment.api import get_payment, create_payment
from domains.inventory.api import get_inventory, create_inventory
from domains.shipping.api import get_shipping, create_shipping
from domains.review.api import get_review, create_review
from domains.notification.api import get_notification, create_notification
from domains.discount.api import get_discount, create_discount
from domains.wishlist.api import get_wishlist, create_wishlist
from domains.address.api import get_address, create_address

ROUTES = {
    "GET /users": get_user, "POST /users": create_user,
    "GET /products": get_product, "POST /products": create_product,
    "GET /orders": get_order, "POST /orders": create_order,
    "GET /carts": get_cart, "POST /carts": create_cart,
    "GET /payments": get_payment, "POST /payments": create_payment,
    "GET /inventorys": get_inventory, "POST /inventorys": create_inventory,
    "GET /shippings": get_shipping, "POST /shippings": create_shipping,
    "GET /reviews": get_review, "POST /reviews": create_review,
    "GET /notifications": get_notification, "POST /notifications": create_notification,
    "GET /discounts": get_discount, "POST /discounts": create_discount,
    "GET /wishlists": get_wishlist, "POST /wishlists": create_wishlist,
    "GET /addresss": get_address, "POST /addresss": create_address
}


def dispatch(request: dict) -> dict:
    handler = ROUTES.get(request.get("route"))
    if handler is None:
        return {"status": 404, "error": "no route"}
    response = handle(handler)(request)
    log_request(request, response.get("status", 0))
    return response
