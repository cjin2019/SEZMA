from dataclasses import dataclass
from scapy.all import Packet, conf, get_if_addr
from scapy.layers.inet import IP, UDP

from app2.network.parsing.exceptions import PacketException
from app2.network.parsing.packet_time import PacketTime
from app2.network.parsing.packet_constants import contains_value, ExceptionCodes, RTPWrapper, ZoomMediaWrapper


@dataclass
class UDPPacketHeader:
    time: "PacketTime"
    src_ip_address: str
    dst_ip_address: str
    src_port: int

@dataclass
class ZoomMediaHeader:
    frame_sequence: bytes
    number_of_packets_per_frame: int
    media_type: "ZoomMediaWrapper"

@dataclass
class RTPHeader:
    payload_type: "RTPWrapper"


class ZoomPacket:
    """
    ZoomPacket stores useful field information from the UDP Zoom packets received
    """
    @classmethod
    def parse(cls, packet: Packet) -> "ZoomPacket":
        """
        packet: a UDP Zoom packet

        May throw PacketException if fails to parse
        """

        try:
            # UDP Layer
            udp_layer: "UDPPacketHeader" = UDPPacketHeader(
                time=PacketTime(float(packet.time)),
                src_ip_address=packet[IP].src,
                dst_ip_address=packet[IP].dst,
                src_port=packet[UDP].sport,
            )

            if packet[IP].dst != get_if_addr(conf.iface):
                raise PacketException(ExceptionCodes.OTHER, "not the right destination")

            # Zoom Media Layer
            load: bytes = packet[UDP].load
            zoom_packet_offset = 0
            if udp_layer.src_port == 8801:
                zoom_packet_offset = 8

            frame_seq: bytes = load[21 + zoom_packet_offset: 23 + zoom_packet_offset]
            number_packets_per_frame: int = load[23 + zoom_packet_offset]
            if not contains_value(ZoomMediaWrapper, load[zoom_packet_offset]):
                raise PacketException(ExceptionCodes.INVALID_ZOOM_MEDIA_TYPE)
            media_type: "ZoomMediaWrapper" = ZoomMediaWrapper(load[zoom_packet_offset])

            zoom_media_layer: "ZoomMediaHeader" = ZoomMediaHeader(
                frame_sequence=frame_seq,
                number_of_packets_per_frame=number_packets_per_frame,
                media_type=media_type
            )

            # RTP Layer
            rtp_idx: int = 24 + zoom_packet_offset
            if load[rtp_idx] != 144:
                if load[28 + zoom_packet_offset] == 144:
                    rtp_idx += 4
                else:
                    rtp_idx += 2 
            rtp_raw_bytes = load[rtp_idx:]

            if len(rtp_raw_bytes) == 0:
                raise PacketException(ExceptionCodes.NOT_ENOUGH_DATA)
            oct1: int = rtp_raw_bytes[0]
            version: int = oct1 >> 6
            if version != 2:
                raise PacketException(ExceptionCodes.INVALID_RTP_VERSION)

            oct2: int = rtp_raw_bytes[1]
            payload_type_val: int = oct2 & 127
            if not contains_value(RTPWrapper, payload_type_val):
                raise PacketException(ExceptionCodes.UNSUPPORTED_RTP_TYPE)
            payload_type: "RTPWrapper" = RTPWrapper(payload_type_val)

            rtp_layer: "RTPHeader" = RTPHeader(
                payload_type=payload_type
            )

            return ZoomPacket(
                udp_layer=udp_layer,
                zoom_media_layer=zoom_media_layer,
                rtp_layer=rtp_layer,
                udp_load=load,
            )
        except Exception as e:
            if type(e) == PacketException:
                raise e
            raise PacketException(ExceptionCodes.OTHER, str(e))
    
    def __init__(self, udp_layer: "UDPPacketHeader", zoom_media_layer: "ZoomMediaHeader", rtp_layer: "RTPHeader", udp_load: bytes) -> None:
        self.__udp_layer: "UDPPacketHeader" = udp_layer
        self.__zoom_media_layer: "ZoomMediaHeader" = zoom_media_layer
        self.__rtp_layer: "RTPHeader" = rtp_layer
        self.__udp_load: bytes = udp_load
        
    @property
    def time(self) -> "PacketTime":
        return self.__udp_layer.time

    @property
    def src_ip_address(self) -> str:
        return self.__udp_layer.src_ip_address

    @property
    def dst_ip_address(self) -> str:
        return self.__udp_layer.dst_ip_address

    @property
    def src_port(self) -> int:
        return self.__udp_layer.src_port
    
    @property
    def frame_sequence(self) -> bytes:
        return self.__zoom_media_layer.frame_sequence
    
    @property
    def number_of_packets_per_frame(self) -> int:
        return self.__zoom_media_layer.number_of_packets_per_frame
    
    @property
    def media_type(self) -> "ZoomMediaWrapper":
        return self.__zoom_media_layer.media_type
    
    @property
    def video_packet_type(self) -> "RTPWrapper":
        return self.__rtp_layer.payload_type
    
    @property
    def size(self) -> int:
        """
        Returns the size of the UDP packet
        """
        return len(self.__udp_load)

    