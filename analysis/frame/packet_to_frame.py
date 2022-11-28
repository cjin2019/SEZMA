import json
from pathlib import Path
import os
from typing import List

from utilities import parser
from analysis.frame.frame_time import FrameTime
from analysis.packet.network_data import NetworkData
from analysis.packet.udp_packet import UDPPacket

def parse_frame_times_from_filenames(dir: str) -> List["FrameTime"]:
    output: List["FrameTime"] = []
    for filename in sorted(os.listdir(dir)):
        # print(filename)
        output.append(FrameTime(filename))
    
    return output

def packet_to_frame():
    config_dir = Path(__file__).parent.parent.parent
    config_file = config_dir / "config.json"

    with config_file.open() as f:
        args = json.load(f)
        args_tcpdump = args["network_capture_config"]
        parser.check_process_inputs(args_tcpdump, {"output_file": str, "duration_seconds": int})
        network_data: "NetworkData" = NetworkData(args_tcpdump["output_file"])
        packets: List["UDPPacket"] = network_data.get_packets_from_other_zoom_server()

        args_ffmpeg = args["frame_capture_config"]
        parser.check_process_inputs(args_ffmpeg, {"output_frame_dir": str})
        frame_times: List["FrameTime"] = parse_frame_times_from_filenames(args_ffmpeg["output_frame_dir"])

        packet_idx: int = 0
        frame_idx: int = 0
        while packet_idx < len(packets) and frame_idx < len(frame_times):
            packet_time = packets[packet_idx].time
            frame_time = frame_times[frame_idx]
            diff = frame_time.subtract(packet_time)

            if diff > 0.1:
                packet_idx += 1
            else:
                print(diff)
                frame_idx += 1

if __name__ == "__main__":
    packet_to_frame()
