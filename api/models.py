# ===================================================
# Autor: Moisés Silva de Azevedo
#
# Universidade Federal do Mato Grosso do Sul,
# Câmpus de Três Lagoas (UFMS/CPTL),
# Sistemas de Informaçao,
# Computaçao Distribuída,
# Novembro de 2025
# ===================================================
from typing import List

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


class OrderItem(BaseModel):
    product_id: int
    quantity: int


class PlaceOrderIn(BaseModel):
    items: List[OrderItem]


class ProductUpdateIn(BaseModel):
    current_balance: int


class LoginIn(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str
