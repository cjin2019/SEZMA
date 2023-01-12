import time
from typing import Type

from analysis.common.data_time import DataTime


class FrameTime(DataTime):
    def __init__(self, filename: str) -> None:
        dot_ridx = filename.rindex(".")
        filename_sec: str = filename[: dot_ridx - 4]
        # print(filename_sec)
        self.__second_precision: time.struct_time = time.strptime(
            filename_sec, "%Y.%m.%d.%H.%M.%S"
        )
        self.__microseconds: int = int(filename[dot_ridx - 3 : dot_ridx]) * 10**3

    @property
    def second_precision(self) -> time.struct_time:
        return self.__second_precision

    @property
    def microseconds(self) -> int:
        return self.__microseconds
    
    @property
    def unix_time(self) -> float:
        return time.mktime(self.second_precision) + self.microseconds / 10**6

    def __str__(self) -> str:
        return time.strftime(
            "%Y-%m-%d %H:%M:%S", self.__second_precision
        ) + ".{:06d}".format(self.__microseconds)
