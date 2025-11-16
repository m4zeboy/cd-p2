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
# [ ] Get Product
# [ ] Place order
# [ ] Concurrency
# [ ] Get Order
# [ ] Authentication
#
import sqlite3
from sqlite3 import Connection, IntegrityError

import requests
import uvicorn
from database import get_db, start_database
from event_handler import consume_create
from fastapi import Depends, FastAPI
from models import NotifyIn, ProductIn
from starlette.exceptions import HTTPException
from starlette.status import HTTP_404_NOT_FOUND, HTTP_500_INTERNAL_SERVER_ERROR

api = FastAPI()
BRANCH_ID = "bb5942cb28ff48f3420f0c13e9187746"
PORT = 4444
BASE_URL = f"http://localhost:{PORT}"
start_database()


# ===================================================
# Startup initialization:
# 1. Subscribe on sync service
# 2. Search for non-consumed events to apply updates
# ===================================================
@api.on_event("startup")
def subscribe_sync():
    result = requests.post(
        "http://localhost:4000/subscribe",
        json={"branch_id": BRANCH_ID, "branch_url": BASE_URL},
    )
    print("Subscription result: ", result.status_code, result.json())
    non_consumed_events = requests.get(
        f"http://localhost:4000/event/non-consumed/{BRANCH_ID}"
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

        event_data = {
            "branch_id": BRANCH_ID,
            "operation": "CREATE",
            "sub": product_data.id,
            "initial_balance": product_data.initial_balance,
            "current_balance": 0,
            "delta": 0,
        }

        result = requests.post(
            "http://localhost:4000/event/publish",
            json=event_data,
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


uvicorn.run(api, host="0.0.0.0", port=PORT)
print("Sync service running on port 4000")
