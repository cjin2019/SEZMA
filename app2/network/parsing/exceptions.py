from typing import Optional
from app2.network.parsing.packet_constants import ExceptionCodes

class PacketException(Exception):
    def __init__(self, code: "ExceptionCodes", msg: Optional[str] = None) -> None:
        self.code = code
        self.message = "" if msg == None else msg

    def __str__(self) -> str:
        return f"{self.code.value}: {self.message}"
