import json
from pathlib import Path
import os
from collections import defaultdict
from typing import Dict, List, Tuple

from utilities import parser
from analysis.frame.frame import Frame
from analysis.frame.frame_time import FrameTime
from analysis.packet.exceptions import PacketException
from analysis.packet.network_data import NetworkData
from analysis.packet.packet_constants import RTPWrapper, ZoomMediaWrapper
from analysis.packet.rtp import RTP
from analysis.packet.udp_packet import UDPPacket


def parse_frames_from_filenames(dir: str) -> List["Frame"]:
    output: List["Frame"] = []
    for filename in sorted(os.listdir(dir)):
        output.append(Frame(filename))
    return output


def get_video_data(packets: List["UDPPacket"]) -> Tuple[Dict[bytes, List["UDPPacket"]], List[bytes]]:
    video_packets: List["UDPPacket"] = []
    for packet in packets:
        if packet.get_media_type() == ZoomMediaWrapper.RTP_VIDEO:
            try:
                rtp_layer: "RTP" = packet.get_next_layer()
                if rtp_layer.header.payload_type == RTPWrapper.VIDEO:
                    video_packets.append(packet)
            except PacketException:
                print(packet.get_frame())

    output = defaultdict(list)
    frames = []

    for packet in video_packets:
        frame = packet.get_frame()
        if len(frames) == 0 or len(frames) > 0 and frames[-1] != frame:
            frames.append(frame)
        output[frame].append(packet)
    
    return output, frames


def packet_to_frame():
    config_dir = Path(__file__).parent.parent.parent
    config_file = config_dir / "config.json"

    with config_file.open() as f:
        args = json.load(f)
        args_tcpdump = args["network_capture_config"]
        parser.check_process_inputs(
            args_tcpdump, {"output_file": str, "duration_seconds": int}
        )
        network_data: "NetworkData" = NetworkData(args_tcpdump["output_file"])
        packets: List["UDPPacket"] = network_data.get_packets_from_other_zoom_server()
        frame_to_packets, packet_frame_seq = get_video_data(packets)

        args_ffmpeg = args["frame_capture_config"]
        parser.check_process_inputs(args_ffmpeg, {"output_frame_dir": str})
        frames: List["Frame"] = parse_frames_from_filenames(
            args_ffmpeg["output_frame_dir"]
        )

        packet_idx: int = 0
        frame_idx: int = 0
        while packet_idx < len(packet_frame_seq) and frame_idx < len(frames):
            frame_time = frames[frame_idx].time
            last_packet = frame_to_packets[packet_frame_seq[packet_idx]][-1]
            packet_time = last_packet.time
            diff = frame_time.subtract(packet_time)

            if diff > 0.1:
                packet_idx += 1
            else:
                if 0.05 < diff and diff <= 0.1:
                    print(
                        diff,
                        frames[frame_idx].filename,
                        packet_time,
                        len(
                            last_packet
                            .get_next_layer()
                            .get_next_layer()
                            .get_next_layer()
                            .payload
                        ),
                    )
                frame_idx += 1


if __name__ == "__main__":
    packet_to_frame()
