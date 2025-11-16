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


class LockProductIn(BaseModel):
    product_id: int
    branch: str
