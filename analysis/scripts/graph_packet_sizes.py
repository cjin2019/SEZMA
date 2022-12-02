import json
import numpy as np
from collections import defaultdict
from matplotlib import pyplot as plt
from pathlib import Path
from scipy.signal import find_peaks, peak_prominences
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
        parser.check_process_inputs(
            args_tcpdump, {"output_file": str, "duration_seconds": int}
        )

        network_data: NetworkData = NetworkData(args_tcpdump["output_file"])
        frame_to_size = defaultdict(lambda: 0)
        sizes: List[int] = []
        times: List[PacketTime] = []

        for packet in network_data.udp_packets:

            if packet.get_media_type() == ZoomMediaWrapper.RTP_VIDEO:
                try:
                    rtp_layer = packet.get_next_layer()
                    nal_layer = rtp_layer.get_next_layer()

                    if rtp_layer.header.payload_type == RTPWrapper.VIDEO:
                        fu_a = nal_layer.get_next_layer()
                        sizes.append(len(fu_a.payload))
                        times.append(packet.time)
                        arr_num: List[int] = [
                            val for val in rtp_layer.header.extension_header[3]
                        ]
                        extension_header_vals.add((arr_num[0], arr_num[1]))

                        # if sizes[-1] > 450:
                        #     print(
                        #         f"packet_src {packet.packet_src}, timestamp {packet.time}, frame {packet.get_frame()}, arr_nums {arr_num}, num_packets = {packet.get_number_packets_per_frame()}, fu_a payload = {len(fu_a.payload)}"
                        #     )

                        frame_to_size[packet.get_frame()] += len(fu_a.payload)
                except PacketException:
                    print(packet.get_frame())
        
        SMALL_SIZE = 100
        MEDIUM_SIZE = 200
        BIGGER_SIZE = 300

        plt.rc("font", size=SMALL_SIZE)  # controls default text sizes
        plt.rc("axes", titlesize=SMALL_SIZE)  # fontsize of the axes title
        plt.rc("axes", labelsize=MEDIUM_SIZE)  # fontsize of the x and y labels
        plt.rc("xtick", labelsize=SMALL_SIZE)  # fontsize of the tick labels
        plt.rc("ytick", labelsize=SMALL_SIZE)  # fontsize of the tick labels
        plt.rc("legend", fontsize=SMALL_SIZE)  # legend fontsize
        plt.rc("figure", titlesize=BIGGER_SIZE)  # fontsize of the figure title

        fig, ax = plt.subplots(figsize=(160, 80))

        size_np: np.ndarray = np.array(sizes)
        peaks, _ = find_peaks(size_np)
        prominences = peak_prominences(size_np, peaks)[0]
        min_prominence = np.percentile(prominences, 80)
        print(prominences, min_prominence)
        peaks, _ = find_peaks(size_np, prominence=(min_prominence, None))
        for idx in peaks:
            print(f"time = {times[idx]}")
        ax.plot(list(range(size_np.size)), size_np, color = 'blue', linestyle = 'solid', marker='.', markersize=50)
        ax.plot(peaks, size_np[peaks], color = 'red', linestyle = 'None', marker='x', markersize=50, markeredgewidth=10)
        ax.set_title("Timeline of Packet Sizes Sent")
        ax.set_xlabel("Order Received")
        ax.set_ylabel("Packet Size (bytes)")

        image_filename = (
            args_tcpdump["output_file"][: args_tcpdump["output_file"].rindex(".")]
            + "_packet_size_timeline.png"
        )
        fig.savefig(image_filename)