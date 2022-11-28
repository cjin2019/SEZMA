import json
from collections import defaultdict
from pathlib import Path
from typing import Dict, List

from utilities import parser
from analysis.packet.exceptions import PacketException
from analysis.packet.nal import NAL
from analysis.packet.network_data import NetworkData
from analysis.packet.packet_time import PacketTime
from analysis.packet.packet_constants import RTPWrapper, ZoomMediaWrapper
from analysis.packet.udp_packet import UDPPacket

if __name__ == "__main__":
    config_dir = Path(__file__).parent.parent.parent
    config_file = config_dir / "config.json"

    extension_header_vals = set()

    with config_file.open() as f:
        args = json.load(f)
        args_tcpdump = args["network_capture_config"]
        parser.check_process_inputs(args_tcpdump, {"output_file": str, "duration_seconds": int})

        network_data: NetworkData = NetworkData(args_tcpdump["output_file"])
        frame_to_size = defaultdict(lambda: 0)

        min_size = float('inf')
        max_size = -1
        for packet in network_data.udp_packets:

            if packet.get_media_type() == ZoomMediaWrapper.RTP_VIDEO:
                try:
                    rtp_layer = packet.get_next_layer()
                    nal_layer = rtp_layer.get_next_layer()
                    
                    if rtp_layer.header.payload_type == RTPWrapper.VIDEO:
                        fu_a = nal_layer.get_next_layer()

                        if packet.get_number_packets_per_frame() > 0:
                            min_size = min(len(fu_a.payload), min_size)
                            max_size = max(len(fu_a.payload), max_size)
                            arr_num: List[int ]= [val for val in rtp_layer.header.extension_header[3]]
                            extension_header_vals.add((arr_num[0], arr_num[1]))

                            print(f"packet_src {packet.packet_src}, timestamp {packet.time}, frame {packet.get_frame()}, arr_nums {arr_num}, num_packets = {packet.get_number_packets_per_frame()}, fu_a payload = {len(fu_a.payload)}")

                        frame_to_size[packet.get_frame()] += len(fu_a.payload)
                except PacketException:
                    print(packet.get_frame())
        

        print(min_size, max_size)