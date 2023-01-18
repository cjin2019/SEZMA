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
from analysis.packet.rtp import RTP
from analysis.packet.udp_packet import UDPPacket

if __name__ == "__main__":
    config_dir = Path(__file__).parent.parent.parent
    config_file = config_dir / "config.json"

    extension_header_vals = set()

    with config_file.open() as f:
        args = json.load(f)
        args_tcpdump = args["network_capture_config"]
        parser.check_process_inputs(
            args_tcpdump, {"output_file": str, "duration_seconds": int}
        )

        network_data: NetworkData = NetworkData(args_tcpdump["output_file"])
        packets_per_frame: Dict[bytes, List[UDPPacket]] = network_data.get_packets_per_frame()

        for frame in packets_per_frame:
            packets = packets_per_frame[frame]
            # if RTPWrapper.INVALID in packet_types:
            #     print(f"frame {int.from_bytes(frame, 'big')} contains invalid packets start: {first_packet.time} end: {last_packet.time}, rtp_initial_payload {[packet.rtp_load[:10] for packet in packets]}")
            #     continue
            
            first_packet = packets[0]
            last_packet = packets[-1]
            fecs = [packet for packet in packets if packet.get_rtp_type() == RTPWrapper.FEC]
            vids = [packet for packet in packets if packet.get_rtp_type() == RTPWrapper.VIDEO]
            exp_num_packets = first_packet.get_number_packets_per_frame()

            num_fecs = len(fecs)
            num_vids = len(vids)

            fec_packet_sizes = [packet.get_packet_size() for packet in fecs]
            vid_packet_sizes = [packet.get_packet_size() for packet in vids]
            print(f"start: {first_packet.time} end: {last_packet.time} frame {int.from_bytes(frame, 'big')} total_packet_size: {fec_packet_sizes} {vid_packet_sizes}")
            # if num_fecs > 0:
            #     print(f"fec: {num_fecs} vids: {num_vids}")
            
                # print([vid.get_next_layer().get_next_layer().get_next_layer().header.type for vid in vids])
                # print(vids[0].get_next_layer().get_next_layer().get_next_layer().header.start)
                # print(vids[-1].get_next_layer().get_next_layer().get_next_layer().header.end)

            
            if num_fecs + num_vids < exp_num_packets:
                print(f"LESS THAN {exp_num_packets}. ACTUAL = {num_fecs + num_vids}")
            elif num_fecs + num_vids > exp_num_packets:
                print(f"GREATHER THAN {exp_num_packets}, ")


        

        print(extension_header_vals)
