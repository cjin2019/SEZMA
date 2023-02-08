from dataclasses import dataclass
from datetime import datetime
from typing import List

from app2.network.parsing.zoom_packet import ZoomPacket
from app2.network.parsing.packet_constants import RTPWrapper
@dataclass
class NetworkMetricsByFrame:
    """
    Currently computes metrics based on the frame
    """
    sequence_number: bytes
    packet_times: List[datetime]
    packet_sizes: List[int]
    expected_number_of_packets: int
    actual_number_of_packets: int
    num_fecs: int

    def update(self, packet: "ZoomPacket") -> None:
        """
        Updates the metrics with new packet_time, packet_size, actual_number_of_packets
        """
        self.packet_times.append(packet.time.get_datetime())
        self.packet_sizes.append(packet.size)
        self.actual_number_of_packets += 1
        if packet.video_packet_type == RTPWrapper.FEC:
            self.num_fecs += 1


