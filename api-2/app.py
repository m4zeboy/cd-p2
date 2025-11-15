import sqlite3
from sqlite3 import Connection, IntegrityError

import requests
import uvicorn
from database import get_db, start_database
from event_handler import consume_create
from fastapi import Depends, FastAPI
from models import NotifyIn, ProductIn
from starlette.exceptions import HTTPException
from starlette.status import HTTP_500_INTERNAL_SERVER_ERROR

api = FastAPI()
BRANCH_ID = "771e59d2742c37ca4e28b6b1b64ee061"
PORT = 5555
BASE_URL = f"http://localhost:{PORT}"

start_database()


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
        print("Subscription result: ", result.status_code)

        return {"message": f"{product_data.id} create"}
    except IntegrityError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


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


uvicorn.run(api, host="0.0.0.0", port=PORT)
print("Sync service running on port 4000")
