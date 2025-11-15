from sqlite3 import Connection, IntegrityError

import requests
import uvicorn
from database import get_db, start_database
from fastapi import Depends, FastAPI
from pydantic import BaseModel
from starlette.exceptions import HTTPException

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
        event_id = cursor.execute(
            "INSERT INTO event (publisher, operation, sub, initial_balance, current_balance, delta) VALUES (?, ?, ?, ?, ?, ?)",
            (
                publisher_id,
                event_data.operation,
                event_data.sub,
                event_data.initial_balance,
                event_data.current_balance,
                event_data.delta,
            ),
        ).lastrowid

        subscribers = cursor.execute("SELECT id, branch_url FROM subscriber").fetchall()
        for row in subscribers:
            branch_url = row["branch_url"]
            event_consumer_id = cursor.execute(
                "INSERT INTO event_consumer (event_id, subscriber_id) VALUES (?, ?)",
                (event_id, row["id"]),
            ).lastrowid

            result = requests.post(
                f"{branch_url}/notify",
                json={
                    "event_consumer_id": event_consumer_id,
                    "publisher_branch_id": publisher_id,
                    "operation": event_data.operation,
                    "sub": event_data.sub,
                    "initial_balance": event_data.initial_balance,
                    "current_balance": event_data.current_balance,
                    "delta": event_data.delta,
                },
            )
            print(f"notify result: {result.status_code} {result.json()}")

        db.commit()
    except HTTPException:
        raise
    except Exception as e:
        print(str(e))
        raise HTTPException(status_code=500, detail=str(e))


uvicorn.run(api, host="0.0.0.0", port=4000)
print("Sync service running on port 4000")
