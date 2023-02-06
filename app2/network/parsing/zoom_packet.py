from scapy.all import Packet
from scapy.layers.inet import IP, UDP

from app2.network.parsing.packet_time import PacketTime
from app2.network.parsing.packet_constants import contains_value, ZoomMediaWrapper
class ZoomPacket:
    def __init__(self, packet: Packet):
        """
        packet: a UDP packet
        """
        self.__time: float = float(packet.time)
        self.__packet_src: str = packet[IP].src
        self.__packet_dst: str = packet[IP].dst
        self.__packet_sport: int = packet[UDP].sport
        self.__load: bytes = packet[UDP].load

        self.__zoom_packet_offset = 0
        if self.__packet_sport == 8801:
            self.__zoom_packet_offset = 8

    @property
    def time(self) -> "PacketTime":
        return PacketTime(self.__time)

    @property
    def packet_src(self) -> str:
        return self.__packet_src

    @property
    def packet_dst(self) -> str:
        return self.__packet_dst

    @property
    def packet_sport(self) -> int:
        return self.__packet_sport
    
    @property
    def rtp_load(self) -> bytes:
        rtp_idx: int = 24 + self.__zoom_packet_offset

        if self.__load[rtp_idx] != 144:
            # try 26 or 28 byte offset
            # print("changed offset")
            if self.__load[28 + self.__zoom_packet_offset] == 144:
                rtp_idx += 4
            else:
                rtp_idx += 2 

        return self.__load[rtp_idx:]

    def get_frame(self) -> bytes:
        """
        Returns the frame sequence number in bytes
        """
        start, end = 21 + self.__zoom_packet_offset, 23 + self.__zoom_packet_offset
        return self.__load[start:end]

    def get_number_packets_per_frame(self) -> int:
        """
        Returns the number of packets per frame
        """
        idx = 23 + self.__zoom_packet_offset
        return self.__load[idx]

    def get_media_type(self) -> "ZoomMediaWrapper":
        """
        Returns the media type
        """
        idx = 0 + self.__zoom_packet_offset
        if not contains_value(ZoomMediaWrapper, self.__load[idx]):
            return ZoomMediaWrapper.INVALID

        return ZoomMediaWrapper(self.__load[idx])

    def get_packet_size(self) -> int:
        """
        Returns the size of the UDP packet
        """
        return len(self.__load)
    
    # def get_next_layer(self) -> "RTP":
    #     return RTP(self.rtp_load)
    
    # def get_rtp_type(self) -> "RTPWrapper":
    #     try:
    #         return self.get_next_layer().header.payload_type
    #     except PacketException as e:
    #         print(e)
    #         return RTPWrapper.INVALID

    