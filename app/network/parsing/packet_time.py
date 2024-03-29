import datetime
import time

from app.common.data_time import DataTime

"""
PacketTime represents the received time of the packet. This includes 
"""


class PacketTime(DataTime):
    def __init__(self, seconds: float):
        self.__original_seconds = seconds
        self.__second_precision = time.localtime(seconds)
        self.__microseconds = int((seconds * 10**6) % 10**6)

    @property
    def second_precision(self) -> time.struct_time:
        return self.__second_precision

    @property
    def microseconds(self) -> int:
        return self.__microseconds
    
    @property
    def original_seconds(self) -> float:
        return self.__original_seconds

    def __eq__(self, other) -> bool:
        return (
            type(other) == PacketTime
            and other.second_precision == self.__second_precision
            and other.microseconds == self.__microseconds
        )

    def __hash__(self) -> int:
        return hash((self.__second_precision, self.__microseconds))

    def __str__(self) -> str:
        return time.strftime(
            "%Y-%m-%d %H:%M:%S", self.__second_precision
        ) + "." + str(self.__microseconds).zfill(6)
