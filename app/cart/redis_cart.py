import redis
import json
from django.conf import settings

redis_client = settings.REDIS_CLIENT


CART_TTL = 60*30


def _refresh_cart_ttl_pipe(pipe, session_id):
    pipe.expire(_qty_key(session_id), CART_TTL)
    pipe.expire(_details_key(session_id), CART_TTL)
    pipe.expire(f"{_cart_key(session_id)}:promo_code", CART_TTL)


def _cart_key(session_id):
    return f"cart:{session_id}"


def _qty_key(session_id):
    return f"{_cart_key(session_id)}:qty"


def _details_key(session_id):
    return f"{_cart_key(session_id)}:details"


def add_to_cart(session_id, product_id, quantity, name, price):
    qty_key = _qty_key(session_id)
    details_key = _details_key(session_id)

    pipe = redis_client.pipeline()

    pipe.hincrby(qty_key, product_id, quantity)

    if not redis_client.hexists(details_key, product_id):
        product_data = {
            "product_id": product_id,
            "name": name,
            "price": price,
        }
        pipe.hset(details_key, product_id, json.dumps(product_data))

    _refresh_cart_ttl_pipe(pipe, session_id)
    pipe.execute()


def get_cart(session_id):
    qtys = redis_client.hgetall(_qty_key(session_id))
    details = redis_client.hgetall(_details_key(session_id))

    cart_items = []
    for pid, qty in qtys.items():
        details_json = details.get(pid)
        if not details_json:
            continue
        data = json.loads(details_json)
        data["quantity"] = int(qty)
        cart_items.append(data)

    return cart_items


def remove_from_cart(session_id, product_id):
    pipe = redis_client.pipeline()
    pipe.hdel(_qty_key(session_id))
    pipe.hdel(_details_key(session_id))

    if pipe.hlen(_qty_key(session_id)) == 0:
        pipe.delete(f"{_cart_key(session_id)}:promo_code")

    _refresh_cart_ttl_pipe(pipe, session_id)
    pipe.execute


def clear_cart(session_id):
    pipe = redis_client.pipeline()
    pipe.hdel(_qty_key(session_id))
    pipe.hdel(_details_key(session_id))
    pipe.delete(f"{_cart_key(session_id)}:promo_code")
    pipe.execute()


def increment_cart(session_id, product_id, quantity=1):
    pipe = redis_client.pipeline()
    redis_client.hincrby(_qty_key(session_id), product_id, quantity)
    _refresh_cart_ttl_pipe(pipe, session_id)
    return True


def decrement_cart(session_id, product_id, quantity=1):

    qty_key = _qty_key(session_id)
    new_qty = redis_client.hincrby(qty_key, product_id, -quantity)

    MAX_ATTEMPTS = 5
    pipe = redis_client.pipeline()
    if new_qty < 1:
        pipe.hdel(qty_key, product_id)
        pipe.hdel(_details_key(session_id), product_id)
        pipe.delete(f"{_cart_key(session_id)}:promo_code")
    else:
        _refresh_cart_ttl_pipe(pipe, session_id)
    pipe.execute()
    return True


def set_quantity(session_id, product_id, quantity):
    pipe = redis_client.pipeline()
    cart_key = _cart_key(session_id)
    existing = pipe.hget(cart_key, product_id)
    if not existing:
        return False

    data = json.loads(existing)
    data["quantity"] = quantity
    pipe.hset(cart_key, product_id, json.dumps(data))
    _refresh_cart_ttl_pipe(pipe, session_id)
    pipe.execute()
    return True


def set_cart_promo_code(session_id, promo_code):
    pipe = redis_client.pipeline()
    key = f"cart:{session_id}:promo_code"
    redis_client.set(key, promo_code)
    _refresh_cart_ttl_pipe(pipe, session_id)
    pipe.execute()


def get_cart_promo_code(session_id):
    key = f"cart:{session_id}:promo_code"
    return redis_client.get(key)


def update_cart_item(session_id, product_id, name, price, quantity):
    product_data = {
        "product_id": product_id,
        "name": name,
        "price": float(price),
        "quantity": quantity
    }
    pipe = redis_client.pipeline()
    pipe.hset(_details_key(session_id), product_id, json.dumps(product_data))
    pipe.hset(_qty_key(session_id), product_id, quantity)
    _refresh_cart_ttl_pipe(pipe, session_id)
    pipe.execute()
    return True

