import json
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from pathlib import Path
from typing import List

from utilities import parser
from analysis.packet.network_data import NetworkData


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

        network_data: NetworkData = NetworkData(args_tcpdump["output_file"])
        packets_per_frame = network_data.get_packets_per_frame()

        # get the time and size
        times: List[float] = []
        sizes: List[int] = []
        frame_colors: List[str] = []

        # get interpacket difference
        # get time difference between packets of different frames
        # get the number of packets per frame
        time_withinpacket: List[float] = []
        time_betweenpacket: List[float] = []
        num_packets_per_frame: List[int] = []
        time_packet_start: List[float] = []

        for frame in packets_per_frame:
            num_packets: int = len(packets_per_frame[frame])
            num_packets_per_frame.append(num_packets)

            frame_color: str = map_frame_to_color(frame)
            frame_colors += [frame_color] * num_packets

            frame_times = [packet.time for packet in packets_per_frame[frame]]
            time_packet_start.append(frame_times[0])
            time_withinpacket.append(frame_times[-1] - frame_times[0])
            if len(times) > 0:
                time_betweenpacket.append(frame_times[0] - times[-1])
            times += frame_times

            frame_sizes = [
                packet.get_packet_size() for packet in packets_per_frame[frame]
            ]
            sizes += frame_sizes

        # start plotting

        # plotting the time and sizes

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

        fig, ax = plt.subplots(figsize=(600, 80))

        ax.scatter(times, sizes, c=frame_colors, s=800)
        ax.set_title("Timeline of Packets Sent per Frame")
        ax.set_xlabel("Unix Time")
        ax.set_ylabel("Packet Size (bytes)")

        image_filename = (
            args_tcpdump["output_file"][: args_tcpdump["output_file"].rindex(".")]
            + "_timeline.png"
        )
        fig.savefig(image_filename)

        fig, ax = plt.subplots(figsize=(600, 80))
        ax.scatter(time_packet_start, time_withinpacket, s=800)
        ax.set_title("Time Difference Between First and Last Packet Per Frame")
        ax.set_xlabel("Unix Time of First Packet Per Frame")
        ax.set_ylabel("Duration of Time Within Packet (s)")

        image_filename = (
            args_tcpdump["output_file"][: args_tcpdump["output_file"].rindex(".")]
            + "_within_frame.png"
        )
        fig.savefig(image_filename)

        fig, ax = plt.subplots(figsize=(600, 80))
        ax.scatter(time_packet_start[1:], time_betweenpacket, s=800)
        ax.set_title("Time Difference Between Frames")
        ax.set_xlabel("Unix Time of First Packet Per Frame")
        ax.set_ylabel("Duration of Time Sent Between Frames (s)")

        image_filename = (
            args_tcpdump["output_file"][: args_tcpdump["output_file"].rindex(".")]
            + "_between_frame.png"
        )
        fig.savefig(image_filename)

        fig, ax = plt.subplots(figsize=(600, 80))
        ax.scatter(time_packet_start, num_packets_per_frame, s=800)
        ax.set_title("Number of Packets Per Frame")
        ax.set_xlabel("Unix Time of First Packet Per Frame")
        ax.set_ylabel("Number of Packets Per Frame")

        image_filename = (
            args_tcpdump["output_file"][: args_tcpdump["output_file"].rindex(".")]
            + "_num_packets.png"
        )
        fig.savefig(image_filename)
