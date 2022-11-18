import csv
import json
from pathlib import Path

from utilities import parser
from analysis.network_data import NetworkData
from analysis.packet_time import PacketTime

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
            # if packet.get_number_packets_per_frame() > 2:
            print(f"frame = {packet.get_frame()}, rtp_type = {packet.get_rtp_payload_type().name}, avc_headers = {packet.get_avc_3d_extension()}, rbsp_payload size = {len(packet.get_raw_byte_seq_payload())}")
            # print(f"src = {packet.packet_src}, time = {packet_time}, frame = {packet.get_frame()}, packets_per_frame = {packet.get_number_packets_per_frame()}, size = {packet.get_packet_size()}")
            # print(f"frame = {packet.get_frame()}, rtp type = {packet.get_rtp_payload_type()}, nal type = {packet.get_nal_type()}, nal ref idx = {packet.get_nal_ref_idc()}")
            # print(f"frame = {packet.get_frame()}, nal_ref_idc = {packet.get_nal_ref_idc()}, nal_unit_type = {packet.get_nal_type()}, avc_values = {packet.get_avc_3d_extension()}")


