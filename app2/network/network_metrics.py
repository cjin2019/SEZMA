from dataclasses import dataclass
from datetime import datetime
from typing import List

from app2.network.parsing.zoom_packet import ZoomPacket
from app2.network.parsing.packet_constants import RTPWrapper
@dataclass
class NetworkMetrics:
    """
    Currently computes metrics based on the frame
    """
    frame_sequence_number: bytes
    packet_time: datetime
    packet_size: int
    expected_number_of_packets: int
    is_fec: bool


