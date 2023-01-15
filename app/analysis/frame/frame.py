from app.analysis.frame.frame_time import FrameTime


class Frame:
    def __init__(self, filename: str) -> None:
        self.__filename = filename
        self.__time = FrameTime(filename)

    @property
    def filename(self) -> str:
        return self.__filename

    @property
    def time(self) -> "FrameTime":
        return self.__time
