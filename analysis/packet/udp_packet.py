from typing import Union
from scapy.layers.inet import IP, UDP
from scapy.all import Packet

from analysis.packet.packet_constants import (
    contains_value,
    ZoomMediaWrapper,
    RTPWrapper,
)
from analysis.packet.packet_time import PacketTime
from analysis.packet.avc_3d_header import AVC3dExtension
from analysis.packet.mvc_header import MVCExtension
from analysis.packet.rtp import RTP


"""
UDPPacket contains data contained inside a UDP packet from tcpdump
"""


class UDPPacket:
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

    def get_next_layer(self) -> "RTP":
        rtp_idx: int = 24 + self.__zoom_packet_offset
        return RTP(self.__load[rtp_idx:])
