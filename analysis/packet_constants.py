from enum import IntEnum
from typing import Type

class ZoomMediaWrapper(IntEnum):
    RTP_VIDEO = 16
    RTP_AUDIO = 15
    RTP_SCREEN_SHARE = 13
    RTCP_SENDER_REPORT = 33
    KEEP_ALIVE = 21
    INVALID = -1

class RTPWrapper(IntEnum):
    VIDEO = 98
    FEC = 110

def contains_value(cls: Type[IntEnum] , val: int):
    return val in cls.__members__.values()
