# ===================================================
# Autor: Moisés Silva de Azevedo
#
# Universidade Federal do Mato Grosso do Sul,
# Câmpus de Três Lagoas (UFMS/CPTL),
# Sistemas de Informaçao,
# Computaçao Distribuída,
# Novembro de 2025
# ===================================================
# [x] Create Product
# [x] Replicate
# [x] Fail tolerance
# [x] Get Product
# [x] Place order
#   [x] Concurrency
#   [x] Process order
#   [x] update product
#   [x] confirm
#   [x] publish update event to other branches
#   [x] Replicate to update event
#   [x] unlock
# [x] Get Order
# [ ] Authentication
#
import sqlite3
from sqlite3 import Connection, IntegrityError

import requests
import uvicorn
from database import get_db, start_database
from event_handler import consume_create, consume_update, publish_event
from fastapi import Depends, FastAPI
from models import NotifyIn, PlaceOrderIn, ProductIn
from starlette.exceptions import HTTPException
from starlette.status import HTTP_404_NOT_FOUND, HTTP_500_INTERNAL_SERVER_ERROR

api = FastAPI()
BRANCH_ID = "bb5942cb28ff48f3420f0c13e9187746"
PORT = 4444
BASE_URL = f"http://localhost:{PORT}"
SYNC_SERVICE_BASE_URL = "http://localhost:4000"
start_database()


# ===================================================
# Startup initialization:
# 1. Subscribe on sync service
# 2. Search for non-consumed events to apply updates
# ===================================================
@api.on_event("startup")
def subscribe_sync():
    result = requests.post(
        f"{SYNC_SERVICE_BASE_URL}/subscribe",
        json={"branch_id": BRANCH_ID, "branch_url": BASE_URL},
    )
    print("Subscription result: ", result.status_code, result.json())
    non_consumed_events = requests.get(
        f"{SYNC_SERVICE_BASE_URL}/event/non-consumed/{BRANCH_ID}"
    )

    non_consumed_events_data = non_consumed_events.json()
    print(
        "non-consumed events: ",
        non_consumed_events.status_code,
        non_consumed_events_data,
    )

    conn = sqlite3.connect("product_database.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    for event in non_consumed_events_data:
        if event["publisher_id"] == BRANCH_ID:
            print("Ignore event from own branch")
            continue
        if event["operation"] == "CREATE":
            consume_create(
                db=conn,
                cursor=cursor,
                notify_data=NotifyIn(
                    event_consumer_id=event["id"],
                    publisher_branch_id=event["publisher_id"],
                    operation=event["operation"],
                    sub=event["sub"],
                    initial_balance=event["initial_balance"],
                    current_balance=event["current_balance"],
                    delta=event["delta"],
                ),
                BRANCH_ID=BRANCH_ID,
            )

    conn.close()


# ===================================================
# Create product:
# 1. Create product locally
# 2. Publish event: operation=CREATE
# The sync service will handle the distribution of the event
# ===================================================
@api.post("/product")
def create_product(
    product_data: ProductIn,
    db: Connection = Depends(get_db),
):
    try:
        cursor = db.cursor()

        cursor.execute(
            "INSERT INTO product (id, current_balance) VALUES (?, ?)",
            (product_data.id, product_data.initial_balance),
        )

        db.commit()

        result = publish_event(
            BRANCH_ID=BRANCH_ID,
            SYNC_SERVICE_BASE_URL=SYNC_SERVICE_BASE_URL,
            operation="CREATE",
            sub=product_data.id,
            initial_balance=product_data.initial_balance,
            current_balance=0,
            delta=0,
        )
        print("Publish result: ", result.status_code)

        return {"message": f"{product_data.id} create"}
    except IntegrityError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ===================================================
# Listen notifications from sync service:
# 1. When an event occur, the sync service will call this route
# for every listener subscribed in the event
# 2. Handle appropriately based on event operation
# 3. Call the consume route to mark the event as consumed
# ===================================================
@api.post("/notify")
def notify(notify_data: NotifyIn, db: Connection = Depends(get_db)):
    if notify_data.publisher_branch_id == BRANCH_ID:
        print("Ignore event from own branch")
        return
    try:
        cursor = db.cursor()
        if notify_data.operation == "CREATE":
            consume_create(
                db=db, cursor=cursor, notify_data=notify_data, BRANCH_ID=BRANCH_ID
            )
        elif notify_data.operation == "UPDATE":
            consume_update(
                db=db, cursor=cursor, notify_data=notify_data, BRANCH_ID=BRANCH_ID
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}",
        )


@api.get("/product/{id}")
def select_product_by_id(id: int, db: Connection = Depends(get_db)):
    cursor = db.cursor()

    product = cursor.execute("SELECT * FROM product WHERE id = ?", (id,)).fetchone()

    if product is None:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Product not found.")
    return product


# ===================================================
# Place order with various items:
# 1. When an event occur, the sync service will call this route
# ===================================================
@api.post("/place-order")
def place_order(place_order_data: PlaceOrderIn, db: Connection = Depends(get_db)):
    cursor = db.cursor()

    updates_to_publish = {}

    try:
        request_id = cursor.execute(
            "INSERT INTO request (created_at) VALUES (datetime('now'))"
        ).lastrowid
        print(f"request_id: {request_id}")

        for item in place_order_data.items:
            product = cursor.execute(
                "SELECT id, current_balance FROM product WHERE id = ?",
                (item.product_id,),
            ).fetchone()

            if product is None:
                raise HTTPException(
                    status_code=HTTP_404_NOT_FOUND,
                    detail=f"Product {item.product_id} not found.",
                )

            current_balance = product[1]
            status = "NEW"

            product_request_id = cursor.execute(
                "INSERT INTO product_request (product_id, request_id, quantity, status) VALUES (?, ?, ?, ?)",
                (item.product_id, request_id, item.quantity, status),
            ).lastrowid
            db.commit()

            # Get lock
            get_lock_response = requests.get(
                f"{SYNC_SERVICE_BASE_URL}/lock?product_id={item.product_id}"
            )

            if get_lock_response.status_code != HTTP_404_NOT_FOUND:
                status = "CANCELLED_BY_LOCK"
                cursor.execute(
                    "UPDATE product_request SET status = ? WHERE id = ? ",
                    (status, product_request_id),
                )
                db.commit()
                print(f"Product {item.product_id} locked. {get_lock_response.json()}")
                continue

            # Lock product
            lock_product_response = requests.post(
                f"{SYNC_SERVICE_BASE_URL}/lock",
                json={"branch": BRANCH_ID, "product_id": item.product_id},
            )

            lock_product_response_data = lock_product_response.json()
            print(
                "lock_product_response: ",
                lock_product_response.status_code,
                lock_product_response.json(),
            )

            if current_balance - item.quantity < 0:
                status = "INSUFFICIENT_BALANCE"
                cursor.execute(
                    "UPDATE product_request SET status = ? WHERE id = ? ",
                    (status, product_request_id),
                )
                db.commit()

                unlock_response = requests.patch(
                    f"{SYNC_SERVICE_BASE_URL}/lock/{lock_product_response_data['lock_id']}/release"
                )

                print(
                    f"unlock_response: {unlock_response.status_code}, {unlock_response.json()}"
                )
                continue

            status = "IN_PROGRESS"

            cursor.execute(
                "UPDATE product_request SET status = ? WHERE id = ? ",
                (status, product_request_id),
            )
            db.commit()

            # Process order -> update product -> confirm -> publish update event to other branches -> unlock
            new_balance = current_balance - item.quantity
            cursor.execute(
                "UPDATE product SET current_balance = ? WHERE id = ?",
                (new_balance, item.product_id),
            )
            db.commit()
            print(f"Product {item.product_id}, new_balance: {new_balance}")
            cursor.execute(
                "UPDATE product_request SET status = ? WHERE id = ? ",
                ("CONFIRMED", product_request_id),
            )
            db.commit()

            updates_to_publish[item.product_id] = -item.quantity

            print(f"updates to publish: {len(updates_to_publish)}")

            for product_id, delta in updates_to_publish.items():
                print(f"Publish: UPDATE product {product_id}, delta: {delta}")
                publish_result = publish_event(
                    BRANCH_ID=BRANCH_ID,
                    SYNC_SERVICE_BASE_URL=SYNC_SERVICE_BASE_URL,
                    operation="UPDATE",
                    sub=product_id,
                    initial_balance=0,
                    current_balance=0,
                    delta=delta,
                )
                print(
                    "Publish result: ",
                    publish_result.status_code,
                    publish_result.json(),
                )

            unlock_response = requests.patch(
                f"{SYNC_SERVICE_BASE_URL}/lock/{lock_product_response_data['lock_id']}/release"
            )

            print(
                f"unlock_response: {unlock_response.status_code}, {unlock_response.json()}"
            )

        return {
            "request_id": request_id,
            "message": "Request created. Check the items' statuses",
            "confirmed_items": len(updates_to_publish),
        }

    except HTTPException:
        raise


@api.get("/order/{id}")
def get_order_details(id: int, db: Connection = Depends(get_db)):
    cursor = db.cursor()

    request = cursor.execute("SELECT * FROM request WHERE id = ?", (id,)).fetchone()

    if request is None:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Request not found")

    product_requests = cursor.execute(
        "SELECT * FROM product_request WHERE request_id = ?", (id,)
    ).fetchall()

    return {
        "request_id": request[0],
        "request_created_at": request[1],
        "items": product_requests,
    }


uvicorn.run(api, host="0.0.0.0", port=PORT)
print("Sync service running on port 4000")
