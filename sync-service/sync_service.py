# ===================================================
# Autor: Moisés Silva de Azevedo
#
# Universidade Federal do Mato Grosso do Sul,
# Câmpus de Três Lagoas (UFMS/CPTL),
# Sistemas de Informaçao,
# Computaçao Distribuída,
# Novembro de 2025
# ===================================================

from sqlite3 import Connection, IntegrityError

import requests
import uvicorn
from database import get_db, start_database
from fastapi import Depends, FastAPI, Response
from models import LockProductIn
from pydantic import BaseModel
from starlette.exceptions import HTTPException
from starlette.status import (
    HTTP_201_CREATED,
    HTTP_404_NOT_FOUND,
    HTTP_500_INTERNAL_SERVER_ERROR,
)

api = FastAPI()

start_database()


class SubscribeIn(BaseModel):
    branch_id: str
    branch_url: str


@api.post("/subscribe")
def subscribe(
    subscribe_data: SubscribeIn,
    db: Connection = Depends(get_db),
):
    try:
        cursor = db.cursor()

        subscriber = cursor.execute(
            "SELECT id FROM subscriber WHERE id = ? OR branch_url = ?",
            (subscribe_data.branch_id, subscribe_data.branch_url),
        ).fetchone()

        if subscriber is not None:
            return
        cursor.execute(
            "INSERT INTO subscriber (id, branch_url) VALUES (?, ?)",
            (subscribe_data.branch_id, subscribe_data.branch_url),
        )

        db.commit()

        return {"message": f"{subscribe_data.branch_url} subscribed"}
    except IntegrityError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        print(str(e))
        raise HTTPException(status_code=500, detail=str(e))


class EventIn(BaseModel):
    branch_id: str
    operation: str
    sub: int
    initial_balance: int
    current_balance: int
    delta: int


@api.post("/event/publish")
def publish_event(
    event_data: EventIn,
    db: Connection = Depends(get_db),
):
    try:
        cursor = db.cursor()

        cursor.execute(
            "SELECT id FROM subscriber WHERE id = ?",
            (event_data.branch_id,),
        )
        result = cursor.fetchone()

        if result is None:
            raise HTTPException(status_code=404, detail="Publisher not found.")

        publisher_id = result[0]

        subscribers = cursor.execute("SELECT id, branch_url FROM subscriber").fetchall()
        for row in subscribers:
            branch_url = row["branch_url"]
            event_id = cursor.execute(
                "INSERT INTO event (publisher_id, subscriber_id, operation, sub, initial_balance, current_balance, delta) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    publisher_id,
                    row["id"],
                    event_data.operation,
                    event_data.sub,
                    event_data.initial_balance,
                    event_data.current_balance,
                    event_data.delta,
                ),
            ).lastrowid
            db.commit()

            result = requests.post(
                f"{branch_url}/notify",
                json={
                    "event_consumer_id": event_id,
                    "publisher_branch_id": publisher_id,
                    "operation": event_data.operation,
                    "sub": event_data.sub,
                    "initial_balance": event_data.initial_balance,
                    "current_balance": event_data.current_balance,
                    "delta": event_data.delta,
                },
            )
            print(f"notify result: {result.status_code} {result.json()}")

    except HTTPException:
        raise
    except Exception as e:
        print(str(e))
        raise HTTPException(status_code=500, detail=str(e))


@api.patch("/event/consume/{id}")
def consume_event(id: int, db: Connection = Depends(get_db)):
    cursor = db.cursor()

    try:
        instance = cursor.execute(
            "SELECT id FROM event WHERE id = ?",
            (id,),
        ).fetchone()

        print(id, instance)

        if instance is None:
            raise HTTPException(status_code=HTTP_404_NOT_FOUND)
        cursor.execute(
            "UPDATE event SET consumed_at = CURRENT_TIMESTAMP WHERE id = ?",
            (id,),
        )
        db.commit()

        print(f"Event instace {id} consumed.")
    except HTTPException:
        raise
    except Exception:
        HTTPException(status_code=HTTP_500_INTERNAL_SERVER_ERROR)


@api.get("/event/non-consumed/{branch_id}")
def get_events_not_consumed(branch_id, db: Connection = Depends(get_db)):
    cursor = db.cursor()
    result = cursor.execute(
        "SELECT * FROM event WHERE subscriber_id = ? AND consumed_at IS NULL",
        (branch_id,),
    ).fetchall()
    return result


@api.get("/lock")
def get_product_lock(product_id: int = 0, db: Connection = Depends(get_db)):
    cursor = db.cursor()
    lock = cursor.execute(
        "SELECT * FROM lock WHERE product_id = ? AND released_at IS NULL",
        (product_id,),
    ).fetchone()

    print("lock: ", lock)
    if lock is None:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND)

    return lock


@api.post("/lock")
def lock_product(
    response: Response,
    product_lock_data: LockProductIn,
    db: Connection = Depends(get_db),
):
    cursor = db.cursor()

    lock_id = cursor.execute(
        "INSERT INTO lock (branch, product_id) VALUES (?, ?)",
        (
            product_lock_data.branch,
            product_lock_data.product_id,
        ),
    ).lastrowid
    db.commit()

    response.status_code = HTTP_201_CREATED
    return {"lock_id": lock_id, "detail": "Product locked."}


uvicorn.run(api, host="0.0.0.0", port=4000)
print("Sync service running on port 4000")
