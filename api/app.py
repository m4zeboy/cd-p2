from sqlite3 import Connection, IntegrityError

import requests
import uvicorn
from database import get_db, start_database
from fastapi import Depends, FastAPI
from pydantic import BaseModel
from starlette.exceptions import HTTPException
from starlette.status import HTTP_204_NO_CONTENT, HTTP_500_INTERNAL_SERVER_ERROR

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


class ProductIn(BaseModel):
    id: int
    initial_balance: int


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


class NotifyIn(BaseModel):
    event_consumer_id: int
    publisher_branch_id: str
    operation: str
    sub: int
    initial_balance: int
    current_balance: int
    delta: int


@api.post("/notify")
def notify(notify_data: NotifyIn, db: Connection = Depends(get_db)):
    if notify_data.publisher_branch_id == BRANCH_ID:
        print("Ignore event from own branch")
        return
    try:
        cursor = db.cursor()
        if notify_data.operation == "CREATE":
            product = cursor.execute(
                "SELECT id FROM product WHERE id = ?", (notify_data.sub,)
            ).fetchone()
            if product is not None:
                raise HTTPException(
                    status_code=HTTP_204_NO_CONTENT, detail="Product already exists."
                )
            print(
                f"Product {notify_data.sub} not foun in brach {BRANCH_ID}. Start syncing..."
            )
            cursor.execute(
                "INSERT INTO product (id, current_balance) VALUES (?, ?)",
                (notify_data.sub, notify_data.initial_balance),
            )
            db.commit()
            print("Sync OK.")

            consume_request = requests.patch(
                f"http://localhost:4000/event/consume/{notify_data.event_consumer_id}"
            )

            print(consume_request.status_code)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}",
        )


uvicorn.run(api, host="0.0.0.0", port=PORT)
print("Sync service running on port 4000")
