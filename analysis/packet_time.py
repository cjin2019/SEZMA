import time

"""
PacketTime represents the received time of the packet. This includes 
"""
class PacketTime:
    def __init__(self, seconds: float):
        self.second_precision = time.localtime(seconds)
        self.microseconds = int((seconds * 10 ** 6) % 10**6)
    
    def __eq__(self, other) -> bool:
        return type(other) == PacketTime and other.second_precision == self.second_precision and other.microseconds == self.microseconds
    
    def __hash__(self) -> int:
        return hash((self.second_precision, self.microseconds))
    
    def __str__(self) -> str:
        return time.strftime("%Y-%m-%d %H:%M:%S", self.second_precision) + ".{:06d}".format(self.microseconds)