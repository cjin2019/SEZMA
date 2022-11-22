import csv
import json
from pathlib import Path

from utilities import parser
from analysis.network_data import NetworkData
from analysis.packet_time import PacketTime
from analysis.packet_constants import RTPWrapper, ZoomMediaWrapper

if __name__ == "__main__":
    config_dir = Path(__file__).parent.parent.parent
    config_file = config_dir / "config.json"

    with config_file.open() as f:
        args = json.load(f)
        args_tcpdump = args["network_capture_config"]
        parser.check_process_inputs(args_tcpdump, {"output_file": str, "duration_seconds": int})

        network_data: NetworkData = NetworkData(args_tcpdump["output_file"])
        for packet in network_data.udp_packets:
            packet_time = PacketTime(packet.time)

            if packet.get_media_type() == ZoomMediaWrapper.RTP_VIDEO:
                print(f"frame {packet.get_frame()}, rtp_header = {packet.get_next_layer().header}")
            