import csv
import json
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

    with config_file.open() as f:
        args = json.load(f)
        args_tcpdump = args["network_capture_config"]
        parser.check_process_inputs(args_tcpdump, {"output_file": str, "duration_seconds": int})

        network_data: NetworkData = NetworkData(args_tcpdump["output_file"])
        for packet in network_data.udp_packets:
            packet_time = PacketTime(packet.time)

            if packet.get_media_type() == ZoomMediaWrapper.RTP_VIDEO:
                next_layer = packet.get_next_layer()
                if next_layer.header.payload_type == RTPWrapper.VIDEO:
                    nal = NAL(next_layer.payload)

                    if(nal.get_extension_header().non_idr_flag == 1):
                        print(f"time = {packet_time}, frame = {packet.get_frame()}, nal_avc3d_extension = {nal.get_extension_header()}")
        
        data: Dict[bytes, List["UDPPacket"]] = network_data.get_packets_per_frame()
        
        max_frame = None
        max_start_time = 0
        max_end_time = 0
        max_num_packets = 0

        for frame in data:
            start_time: "PacketTime" = PacketTime(data[frame][0].time)
            end_time: "PacketTime" = PacketTime(data[frame][-1].time)

            if len(data[frame]) > max_num_packets:
                max_frame = frame
                max_start_time = start_time
                max_end_time = end_time
                max_num_packets = len(data[frame])

            print(f"frame {int.from_bytes(frame, 'big')}, start_time = {start_time}, end_time = {end_time}, num_packets = {len(data[frame])}")

            last_packet: "UDPPacket" = data[frame][-1]
            if last_packet.get_media_type() == ZoomMediaWrapper.RTP_VIDEO:
                next_layer = last_packet.get_next_layer()
                if next_layer.header.payload_type == RTPWrapper.FEC:
                    print("FEC")
                if next_layer.header.payload_type == RTPWrapper.VIDEO:
                    nal_layer = next_layer.get_next_layer()
                    print(f"frame {int.from_bytes(frame, 'big')}, nal_header = {nal_layer.header}, nal_extension_header = {nal_layer.get_extension_header()}")
        
        print(f"frame {max_frame}, start_time = {max_start_time}, end_time = {max_end_time}, num_packets = {len(data[max_frame])}")