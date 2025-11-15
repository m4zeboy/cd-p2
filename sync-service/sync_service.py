from sqlite3 import Connection, IntegrityError

import uvicorn
from database import get_db, start_database
from fastapi import Depends, FastAPI
from pydantic import BaseModel
from starlette.exceptions import HTTPException
from starlette.status import HTTP_204_NO_CONTENT

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
            "SELECT id FROM subscriber WHERE branch_id = ?",
            (subscribe_data.branch_id,),
        ).fetchone()

        if subscriber is not None:
            raise HTTPException(
                status_code=HTTP_204_NO_CONTENT,
            )
        cursor.execute(
            "INSERT INTO subscriber (branch_id, branch_url) VALUES (?, ?)",
            (subscribe_data.branch_id, subscribe_data.branch_url),
        )

        db.commit()

        return {"message": f"{subscribe_data.branch_url} subscribed"}
    except IntegrityError as e:
        raise HTTPException(status_code=409, detail=str(e))
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
    print(event_data.branch_id)
    try:
        cursor = db.cursor()

        cursor.execute(
            "SELECT id FROM subscriber WHERE branch_id = ?",
            (event_data.branch_id,),
        )
        result = cursor.fetchone()
        print(result)

        if result is None:
            raise HTTPException(status_code=404, detail="Publisher not found.")

        publisher_id = result[0]
        cursor.execute(
            "INSERT INTO event (publisher_id, operation, sub, initial_balance, current_balance, delta) VALUES (?, ?, ?, ?, ?, ?)",
            (
                publisher_id,
                event_data.operation,
                event_data.sub,
                event_data.initial_balance,
                event_data.current_balance,
                event_data.delta,
            ),
        )

        db.commit()
    except Exception as e:
        print(str(e))
        raise HTTPException(status_code=500, detail=str(e))


uvicorn.run(api, host="0.0.0.0", port=4000)
print("Sync service running on port 4000")
