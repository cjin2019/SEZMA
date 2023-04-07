from enum import Enum

class SpecialQueueValues(Enum):
    FINISH = 1
    NON_ZOOM_PACKET = 2

TIME_FORMAT = "%Y-%m-%d %H:%M:%S.%f"
def get_timeformat(time_str: str) -> str:
    return '%Y-%m-%d %H:%M:%S.%f' if "." in time_str else '%Y-%m-%d %H:%M:%S'