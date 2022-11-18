from typing import Union
from scapy.layers.inet import IP, UDP
from scapy.all import Packet

from analysis.packet_constants import contains_value, ZoomMediaWrapper, RTPWrapper
from analysis.avc_3d_header import AVC3dExtension
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
        return self.load[idx]
    
    def get_media_type(self) -> "ZoomMediaWrapper":
        """
        Returns the media type
        """
        idx = 0 + self.zoom_packet_offset
        if not contains_value(ZoomMediaWrapper, self.load[idx]):
            return ZoomMediaWrapper.INVALID

        return ZoomMediaWrapper(self.load[idx])
    
    def get_packet_size(self) -> int:
        """
        Returns the size of the UDP packet
        """
        return len(self.load)
    
    def get_rtp_payload_type(self) -> "RTPWrapper":
        """
        Returns the RTP Payload Type
        Check https://en.wikipedia.org/wiki/Real-time_Transport_Protocol to find the index
        """
        rtp_idx = 24 + self.zoom_packet_offset
        rtp_pt_idx = rtp_idx + 1
        rtp_octet2 = self.load[rtp_pt_idx]
        return RTPWrapper(rtp_octet2 & 127)
    
    def get_nal_type(self) -> int:
        """
        Returns the NAL Payload Type
        """
        nal_idx: int = self.__get_nal_idx()
        return self.load[nal_idx] & 31
    
    def get_nal_ref_idc(self) -> int:
        """
        Returns the nal_ref_idc
        """
        nal_idx: int = self.__get_nal_idx()
        return self.load[nal_idx] & 32 >> 5
    
    def get_avc_3d_extension(self) -> Union["AVC3dExtension", None]:
        if not self.__has_avc_3d_extension_flag():
            return None

        avc_idx: int = self.__get_nal_idx() + 1
        avc_values: int = int.from_bytes(self.load[avc_idx: avc_idx+2], 'big')

        view_idx: int = (avc_values >> 7) & 255
        depth_flag: int = (avc_values >> 6) & 1
        non_idr_flag: int = (avc_values >> 5) & 1
        temporal_id: int = (avc_values >> 2) & 7
        anchor_pic_flag: int = (avc_values >> 1) & 1
        inter_view_flag: int = avc_values & 1

        return AVC3dExtension(view_idx, depth_flag, non_idr_flag, temporal_id, anchor_pic_flag, inter_view_flag)
    
    def get_raw_byte_seq_payload(self) -> bytes:
        """
        Returns the Raw Byte Sequence Payload for UDP Packet
        (ie. data for the frame)
        """
        rbsp_idx: int = self.__get_nal_idx() + 1 # get the avc_idx
        if self.__has_avc_3d_extension_flag():
            rbsp_idx += 2 # so far all Zoom packets have the avc_3d_extension

        return self.load[rbsp_idx:]
    
    def __has_avc_3d_extension_flag(self) -> bool:
        """
        Returns whether the avc_3d_extension_flag is set to 1
        """
        nal_idx: int = self.__get_nal_idx()
        avc_idx: int = nal_idx + 1
        return self.load[avc_idx] >> 7 == 1

    def __get_nal_idx(self) -> int:
        """
        Returns the index of the NAL unit
        Check https://en.wikipedia.org/wiki/Real-time_Transport_Protocol to find the index
        """
        rtp_idx: int = 24 + self.zoom_packet_offset
        is_extension: bool = self.load[rtp_idx] & 16 == 16
        csrc_count: int = self.load[rtp_idx] & 15
        
        after_rtp_header_main_idx: int = rtp_idx + 12 + csrc_count * 4
        if not is_extension:
            return after_rtp_header_main_idx

        rtp_header_extension_length_idx: int = after_rtp_header_main_idx + 2 # 2 bytes after defined profile
        rtp_header_extension_length: int = int.from_bytes(self.load[rtp_header_extension_length_idx: rtp_header_extension_length_idx + 2], 'big')

        after_rtp_header_extension_idx: int = after_rtp_header_main_idx + 4 + rtp_header_extension_length
        return after_rtp_header_extension_idx
