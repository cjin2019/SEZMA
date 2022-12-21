from abc import ABC, abstractmethod
import time


class DataTime(ABC):
    @property
    @abstractmethod
    def second_precision(self) -> time.struct_time:
        pass

    @property
    @abstractmethod
    def microseconds(self) -> int:
        pass

    def subtract(self, other: "DataTime") -> float:
        """
        Returns the difference in seconds
        """
        sec_second_precision: float = time.mktime(self.second_precision) - time.mktime(
            other.second_precision
        )
        sec_microseconds: float = (self.microseconds - other.microseconds) / 10**6
        return sec_second_precision + sec_microseconds
    
    def get_unix_time(self) -> float:
        return time.mktime(self.second_precision) + self.microseconds / 10**6