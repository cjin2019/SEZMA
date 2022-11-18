from scapy.layers.inet import IP, UDP
from scapy.all import Packet

"""
UDPPacket contains data contained inside a UDP packet from tcpdump
"""
class UDPPacket:
    def __init__(self, packet: Packet):
        """
        packet: a UDP packet 
        """
        self.time:float = float(packet.time)
        self.packet_src: str = packet[IP].src
        self.packet_dst: str = packet[IP].dst
        self.packet_sport: int = packet[UDP].sport
        self.load: bytes = packet[UDP].load

        self.zoom_packet_offset = 0
        if self.packet_sport == 8801:
            self.zoom_packet_offset = 8
    
    def get_frame(self) -> bytes:
        """
        Returns the frame sequence number in bytes
        """
        start, end = 21 + self.zoom_packet_offset, 23 + self.zoom_packet_offset
        return self.load[start: end]
    
    def get_number_packets_per_frame(self) -> int:
        """
        Returns the number of packets per frame
        """
        idx = 23 + self.zoom_packet_offset
        return int(self.load[idx])
    
    def get_media_type(self) -> int:
        """
        Returns the media type
        """
        idx = 0 + self.zoom_packet_offset
        return int(self.load[idx])
    
    def get_packet_size(self) -> int:
        """
        Returns the size of the UDP packet
        """
        return len(self.load)
    
    def get_rtp_payload_type(self) -> int:
        """
        Returns the RTP Payload Type
        Check https://en.wikipedia.org/wiki/Real-time_Transport_Protocol

        98: Main Stream
        110: FEC
        """
        rtp_idx = 24 + self.zoom_packet_offset
        rtp_pt_idx = rtp_idx + 1
        rtp_octet2 = int(self.load[rtp_pt_idx])
        return rtp_octet2 & 127 
