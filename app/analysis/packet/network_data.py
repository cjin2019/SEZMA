from typing import List, Dict
from scapy.all import PacketList, get_if_addr, rdpcap, conf
from scapy.layers.inet import IP, UDP

from app.analysis.packet.udp_packet import UDPPacket
from app.analysis.packet.packet_constants import ZoomMediaWrapper, RTPWrapper
from app.analysis.packet.exceptions import PacketException
from app.utilities import *

"""
NetworkData only supports parsing UDP packets
"""


class NetworkData:
    def __init__(self, filename: str):
        self.filename: str = filename
        self.packets: PacketList = rdpcap(filename)
        self.local_ip_addr: str = get_if_addr(conf.iface)
        self.udp_packets = self.get_packets_from_other_zoom_server()

    def get_packets_from_other_zoom_server(self) -> List["UDPPacket"]:
        """
        Gets the video UDP packets from other server. This can either be zoom server
        or direct communication with P2P
        """
        udp_packets: List["UDPPacket"] = []
        for packet in self.packets:
            if (
                IP in packet
                and UDP in packet
                and hasattr(packet[UDP], "load")
                and packet[IP].dst == self.local_ip_addr
            ):
                udp_packet = UDPPacket(packet)
                if (
                    udp_packet.get_media_type() != ZoomMediaWrapper.INVALID
                ):  # helps determine if the packet is at least a zoom packet
                    # if udp_packet.packet_src == "10.29.45.121":
                    udp_packets.append(udp_packet)
        
        return udp_packets

    def get_packets_per_frame(self) -> Dict[bytes, List["UDPPacket"]]:
        """
        Returns a mapping of frame sequence number -> [sequence of packets]
        """
        if len(self.udp_packets) == 0:
            return {}

        output = {}
        for packet in self.udp_packets:
            try:
                if (
                    packet.get_media_type() == ZoomMediaWrapper.RTP_VIDEO
                    # and packet.get_next_layer().header.payload_type == RTPWrapper.VIDEO
                ):
                    curr_frame = packet.get_frame()
                    if curr_frame not in output:
                        output[curr_frame] = []
                    output[curr_frame].append(packet)
            except PacketException as e:
                print(e)

        return output
