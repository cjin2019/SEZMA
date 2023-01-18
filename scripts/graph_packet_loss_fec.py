import json
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import os
from datetime import datetime
from pathlib import Path
from typing import List

from utilities import parser
from analysis.packet.network_data import NetworkData
from analysis.packet.packet_constants import RTPWrapper
from analysis.packet.packet_time import PacketTime


def map_frame_to_color(frame: bytes) -> str:
    colors = [
        color for color in mcolors.get_named_colors_mapping() if color[:4] == "xkcd"
    ]
    frame_val: int = int.from_bytes(frame, "big")
    return colors[frame_val % len(colors)]


if __name__ == "__main__":
    config_dir = Path(__file__).parent.parent.parent
    config_file = config_dir / "config.json"

    with config_file.open() as f:
        args = json.load(f)
        args_tcpdump = args["network_capture_config"]
        parser.check_process_inputs(
            args_tcpdump, {"output_file": str, "duration_seconds": int}
        )

        args_frames = args["frame_capture_config"]
        parser.check_process_inputs(
            args_frames, {"output_frame_dir": str}
        )
        frame_dir: str = args_frames["output_frame_dir"]

        network_data: NetworkData = NetworkData(args_tcpdump["output_file"])
        packets_per_frame = network_data.get_packets_per_frame()

        # get the time and size
        times: List[datetime] = []
        num_fecs: List[int] = []
        num_compared_to_expected: List[int] = []
        sizes: List[int] = []

        for frame in packets_per_frame:
            packets = [packet for packet in packets_per_frame[frame] if packet.get_rtp_type() != RTPWrapper.INVALID]
            times.append(packets[-1].time.get_datetime())
            if len(packets) != len(packets_per_frame[frame]):
                print("There are invalid packets")
            fecs = [packet for packet in packets if packet.get_rtp_type() == RTPWrapper.FEC]
            vids = [packet for packet in packets if packet.get_rtp_type() == RTPWrapper.VIDEO]
            num_fec = len(fecs)
            num_vid = len(vids)
            num_fecs.append(num_fec)

            num_expected = packets[0].get_number_packets_per_frame()
            compared_to_expected = num_expected - (num_fec + num_vid)
            num_compared_to_expected.append(compared_to_expected)

            fec_sizes = [packet.get_packet_size() for packet in fecs]
            vid_sizes = [packet.get_packet_size() for packet in vids]
            sizes.append(sum(vid_sizes) + sum(fec_sizes))


        # start plotting

        # plotting the time and sizes

        graph_dir = frame_dir + "_graphs"
        if not os.path.exists(graph_dir):
            os.makedirs(graph_dir)

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

        fig_width = 200
        fig, ax = plt.subplots(figsize=(fig_width, 80))

        ax.plot_date(times, num_fecs, ms=30)
        ax.grid(True, color='r')
        ax.set_title("Number of FEC Packets Per Frame")
        ax.set_xlabel("Time of Last Packet Per Frame")
        ax.set_ylabel("Number of FEC Packet")

        image_filename = (
            graph_dir + "/num_fecs.png"
        )
        fig.savefig(image_filename)

        fig, ax = plt.subplots(figsize=(fig_width, 80))
        ax.plot_date(times, num_compared_to_expected, ms=30)
        ax.set_title("Difference between expected number of packets and packets received")
        ax.set_xlabel("Time of Last Packet Per Frame")
        ax.set_ylabel("Difference")

        image_filename = (
            graph_dir + "/num_packet_difference.png"
        )
        fig.savefig(image_filename)

        fig, ax = plt.subplots(figsize=(fig_width, 80))
        ax.plot_date(times, sizes, ms=30)
        ax.set_title("Total Packet Size Per Frame")
        ax.set_xlabel("Time of Last Packet Per Frame")
        ax.set_ylabel("Packet Size (bytes)")

        image_filename = (
            graph_dir + "/total_frame_size.png"
        )
        fig.savefig(image_filename)