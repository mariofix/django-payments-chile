from __future__ import annotations

import hashlib
import hmac
from dataclasses import dataclass


@dataclass
class ClienteAPI:
    @classmethod
    def genera_firma(cls, datos: dict, secret_key: str):
        datos_flow = "".join(f"{key!s}{value!s}" for key, value in datos.items())
        firma = hmac.new(key=secret_key.encode(), msg=datos_flow.encode(), digestmod=hashlib.sha256)
        return firma.hexdigest()
