import json
from collections import defaultdict
from pathlib import Path
from typing import Dict, List

from utilities import parser
from analysis.nal import NAL
from analysis.network_data import NetworkData
from analysis.packet_time import PacketTime
from analysis.packet_constants import RTPWrapper, ZoomMediaWrapper
from analysis.udp_packet import UDPPacket

if __name__ == "__main__":
    config_dir = Path(__file__).parent.parent.parent
    config_file = config_dir / "config.json"

    extension_header_set = set()
    with config_file.open() as f:
        args = json.load(f)
        args_tcpdump = args["network_capture_config"]
        parser.check_process_inputs(args_tcpdump, {"output_file": str, "duration_seconds": int})

        network_data: NetworkData = NetworkData(args_tcpdump["output_file"])
        frame_to_size = defaultdict(lambda: 0)

        for packet in network_data.udp_packets:

            if packet.get_media_type() == ZoomMediaWrapper.RTP_VIDEO:
                rtp_layer = packet.get_next_layer()
                nal_layer = rtp_layer.get_next_layer()
                
                if rtp_layer.header.payload_type == RTPWrapper.VIDEO:
                    fu_a = nal_layer.get_next_layer()

                    if fu_a.header.start == 1:
                        print(f"timestamp {packet.time}, frame {packet.get_frame()}, rtp_extension = {rtp_layer.header.extension_header}, fu_a_header = {fu_a.header}")

                    frame_to_size[packet.get_frame()] += len(fu_a.payload)
        
