from dataclasses import dataclass

from analysis.parse.exceptions import PacketException
from analysis.parse.packet_constants import ExceptionCodes

@dataclass
class FU_AHeader:
    start: int 
    end: int
    reserved: int
    type: int

    @classmethod
    def get_header(cls, data: bytes) -> "FU_AHeader":
        oct:int = data[0]

        start: int = oct >> 7
        end: int = (oct >> 6) & 1
        reserved: int = (oct >> 5) & 1

        if reserved != 0:
            raise PacketException(ExceptionCodes.FU_A_NOT_RESERVED)
        type: int = oct & 31

        return FU_AHeader(
                start=start,
                end=end,
                reserved=reserved,
                type=type
        )

class FU_A:
    def __init__(self, data: bytes) -> None:
        self.__header = FU_AHeader.get_header(data)
        self.__payload = data[1:]
    
    @property
    def header(self) -> "FU_AHeader":
        return self.__header
    
    @property
    def payload(self) -> bytes:
        return self.__payload