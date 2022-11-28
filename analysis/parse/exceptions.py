from analysis.parse.packet_constants import ExceptionCodes

class PacketException(Exception):
    def __init__(self, code: "ExceptionCodes") -> None:
        self.code = code
    
    def __str__(self) -> str:
        return self.code.value