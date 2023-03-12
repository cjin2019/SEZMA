
from datetime import datetime
import time

from app2.network.parsing.packet_time import PacketTime

if __name__ == "__main__":
    # check why microsecond of 0 is not being parsed well

    packet_time = PacketTime(500)
    packet_time.__microseconds = 0
    print(packet_time)

    packet_str = str(packet_time)
    datetime.strptime(packet_str, '%Y-%m-%d %H:%M:%S.%f'),