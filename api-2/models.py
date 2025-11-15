from pydantic import BaseModel


class ProductIn(BaseModel):
    id: int
    initial_balance: int


class NotifyIn(BaseModel):
    event_consumer_id: int
    publisher_branch_id: str
    operation: str
    sub: int
    initial_balance: int
    current_balance: int
    delta: int
