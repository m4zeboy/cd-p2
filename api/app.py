import socket
from sqlite3 import Connection, IntegrityError

import requests
import uvicorn
from database import get_db, start_database
from fastapi import Depends, FastAPI
from pydantic import BaseModel
from starlette.exceptions import HTTPException

api = FastAPI()

start_database()


@api.on_event("startup")
def subscribe_sync():
    result = requests.post(
        "http://localhost:4000/subscribe",
        json={"branch_id": socket.gethostname(), "branch_url": "http://localhost:3333"},
    )
    print("Subscription result: ", result.status_code)


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
            "branch_id": socket.gethostname(),
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


uvicorn.run(api, host="0.0.0.0", port=3333)
print("Sync service running on port 4000")
