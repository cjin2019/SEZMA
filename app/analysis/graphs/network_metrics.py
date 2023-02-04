import json
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict

from app.utilities import parser
from app.analysis.packet.packet_constants import RTPWrapper
from app.analysis.packet.network_data import NetworkData
from app.analysis.packet.packet_time import PacketTime


def map_frame_to_color(frame: bytes) -> str:
    colors = [
        color for color in mcolors.get_named_colors_mapping() if color[:4] == "xkcd"
    ]
    frame_val: int = int.from_bytes(frame, "big")
    return colors[frame_val % len(colors)]

def create_graphs(args_tcpdump: Dict, graph_dir: str) -> None:
    network_data: NetworkData = NetworkData(args_tcpdump["output_file"])
    packets_per_frame = network_data.get_packets_per_frame()

    # get the time and size
    times: List[datetime] = []
    sizes: List[int] = []
    frame_colors: List[str] = []

    # get interpacket difference
    # get time difference between packets of different frames
    # get the number of packets per frame
    time_withinpacket: List[float] = []
    time_betweenpacket: List[float] = []
    num_packets_per_frame: List[int] = []
    time_packet_end: List[datetime] = []

    num_fecs: List[int] = []
    num_compared_to_expected: List[int] = []

    for frame in packets_per_frame:
        packets = [packet for packet in packets_per_frame[frame] if packet.get_rtp_type() != RTPWrapper.INVALID]
        if len(packets) != len(packets_per_frame[frame]):
            print("There are invalid packets")

        num_packets: int = len(packets)
        num_packets_per_frame.append(num_packets)

        frame_times = [packet.time.get_datetime() for packet in packets_per_frame[frame]]
        time_packet_end.append(frame_times[-1])
        time_withinpacket.append((frame_times[-1] - frame_times[0]).total_seconds())
        if len(times) > 0:
            time_betweenpacket.append((frame_times[0] - times[-1]).total_seconds())
        times += [packet.time.get_datetime() for packet in packets_per_frame[frame]]

        frame_sizes = [
            packet.get_packet_size() for packet in packets_per_frame[frame]
        ]
        sizes += frame_sizes

        fecs = [packet for packet in packets if packet.get_rtp_type() == RTPWrapper.FEC]
        num_fec = len(fecs)
        num_fecs.append(num_fec)

        num_expected = packets[0].get_number_packets_per_frame()
        compared_to_expected = num_expected - len(packets)
        num_compared_to_expected.append(compared_to_expected)
        

    # start plotting

    SMALL_SIZE = 250
    # MEDIUM_SIZE = 200
    # BIGGER_SIZE = 300

    plt.rc("font", size=SMALL_SIZE)  # controls default text sizes
    plt.rc("axes", titlesize=SMALL_SIZE)  # fontsize of the axes title
    plt.rc("axes", labelsize=SMALL_SIZE)  # fontsize of the x and y labels
    plt.rc("xtick", labelsize=SMALL_SIZE)  # fontsize of the tick labels
    plt.rc("ytick", labelsize=SMALL_SIZE)  # fontsize of the tick labels
    # plt.rc("legend", fontsize=SMALL_SIZE)  # legend fontsize
    #plt.rc("figure", titlesize=BIGGER_SIZE)  # fontsize of the figure title

    fig_width = 200
    fig, ax = plt.subplots(figsize=(fig_width, 80))

    ax.plot_date(times, sizes, ms=30)
    ax.grid(True, color='r')
    ax.set_title("Timeline of Packets Sent per Frame")
    ax.set_xlabel("Unix Time")
    ax.set_ylabel("Packet Size (bytes)")

    image_filename = (
        graph_dir + "/timeline.png"
    )
    fig.savefig(image_filename)

    fig, ax = plt.subplots(figsize=(fig_width, 80))
    ax.plot_date(time_packet_end, time_withinpacket, ms=30)
    ax.set_title("Time Difference Between First and Last Packet Per Frame")
    ax.set_xlabel("Unix Time of First Packet Per Frame")
    ax.set_ylabel("Duration of Time Within Packet (s)")

    image_filename = (
        graph_dir + "/within_frame.png"
    )
    fig.savefig(image_filename)

    fig, ax = plt.subplots(figsize=(fig_width, 80))
    ax.grid(True, color='r')
    ax.plot_date(time_packet_end[1:], time_betweenpacket, ms=30)
    ax.set_title("Time Difference Between Frames")
    ax.set_xlabel("Unix Time of First Packet Per Frame")
    ax.set_ylabel("Duration of Time Sent Between Frames (s)")

    image_filename = (
        graph_dir + "/between_frame.png"
    )
    fig.savefig(image_filename)

    fig, ax = plt.subplots(figsize=(fig_width, 80))
    ax.plot_date(time_packet_end, num_packets_per_frame, ms=30)
    ax.set_title("Number of Packets Per Frame")
    ax.set_xlabel("Unix Time of First Packet Per Frame")
    ax.set_ylabel("Number of Packets Per Frame")

    image_filename = (
        graph_dir + "/num_packets.png"
    )
    fig.savefig(image_filename)

    fig, ax = plt.subplots(figsize=(fig_width, 80))
    ax.plot_date(time_packet_end, num_fecs, ms=30)
    ax.set_title("Number of FEC Packets Per Frame")
    ax.set_xlabel("Time of Last Packet Per Frame")
    ax.set_ylabel("Number of FEC Packet")

    image_filename = (
        graph_dir + "/num_fecs.png"
    )
    fig.savefig(image_filename)

    fig, ax = plt.subplots(figsize=(fig_width, 80))
    ax.plot_date(time_packet_end, num_compared_to_expected, ms=30)
    ax.set_title("Difference between expected number of packets and packets received")
    ax.set_xlabel("Time of Last Packet Per Frame")
    ax.set_ylabel("Difference")

    image_filename = (
        graph_dir + "/num_packet_difference.png"
    )
    fig.savefig(image_filename)



# def run_main() -> None:
#     config_dir = Path(__file__).parent.parent.parent
#     config_file = config_dir / "config.json"

#     with config_file.open() as f:
#         args = json.load(f)
#         args_tcpdump = args["network_capture_config"]
#         parser.check_process_inputs(
#             args_tcpdump, {"output_file": str, "duration_seconds": int}
#         )

#         args_frames = args["frame_capture_config"]
#         parser.check_process_inputs(
#             args_frames, {"output_frame_dir": str}
#         )
#         frame_dir: str = args_frames["output_frame_dir"]

#         network_data: NetworkData = NetworkData(args_tcpdump["output_file"])
#         packets_per_frame = network_data.get_packets_per_frame()

#         # get the time and size
#         times: List[datetime] = []
#         sizes: List[int] = []
#         frame_colors: List[str] = []

#         # get interpacket difference
#         # get time difference between packets of different frames
#         # get the number of packets per frame
#         time_withinpacket: List[float] = []
#         time_betweenpacket: List[float] = []
#         num_packets_per_frame: List[int] = []
#         time_packet_start: List[datetime] = []

#         for frame in packets_per_frame:
#             num_packets: int = len(packets_per_frame[frame])
#             num_packets_per_frame.append(num_packets)

#             frame_color: str = map_frame_to_color(frame)
#             frame_colors += [frame_color] * num_packets

#             frame_times = [packet.time.get_datetime() for packet in packets_per_frame[frame]]
#             time_packet_start.append(frame_times[0])
#             time_withinpacket.append((frame_times[-1] - frame_times[0]).total_seconds())
#             if len(times) > 0:
#                 time_betweenpacket.append((frame_times[0] - times[-1]).total_seconds())
#             times += [packet.time.get_datetime() for packet in packets_per_frame[frame]]

#             frame_sizes = [
#                 packet.get_packet_size() for packet in packets_per_frame[frame]
#             ]
#             sizes += frame_sizes

#         # start plotting

#         # plotting the time and sizes

#         graph_dir = frame_dir + "_graphs"
#         if not os.path.exists(graph_dir):
#             os.makedirs(graph_dir)

#         SMALL_SIZE = 100
#         MEDIUM_SIZE = 200
#         BIGGER_SIZE = 300

#         plt.rc("font", size=SMALL_SIZE)  # controls default text sizes
#         plt.rc("axes", titlesize=SMALL_SIZE)  # fontsize of the axes title
#         plt.rc("axes", labelsize=MEDIUM_SIZE)  # fontsize of the x and y labels
#         plt.rc("xtick", labelsize=SMALL_SIZE)  # fontsize of the tick labels
#         plt.rc("ytick", labelsize=SMALL_SIZE)  # fontsize of the tick labels
#         plt.rc("legend", fontsize=SMALL_SIZE)  # legend fontsize
#         plt.rc("figure", titlesize=BIGGER_SIZE)  # fontsize of the figure title

#         fig_width = 200
#         fig, ax = plt.subplots(figsize=(fig_width, 80))

#         ax.plot_date(times, sizes, ms=30)
#         ax.grid(True, color='r')
#         ax.set_title("Timeline of Packets Sent per Frame")
#         ax.set_xlabel("Unix Time")
#         ax.set_ylabel("Packet Size (bytes)")

#         image_filename = (
#             graph_dir + "/timeline.png"
#         )
#         fig.savefig(image_filename)

#         fig, ax = plt.subplots(figsize=(fig_width, 80))
#         ax.plot_date(time_packet_start, time_withinpacket, ms=30)
#         ax.set_title("Time Difference Between First and Last Packet Per Frame")
#         ax.set_xlabel("Unix Time of First Packet Per Frame")
#         ax.set_ylabel("Duration of Time Within Packet (s)")

#         image_filename = (
#             graph_dir + "/within_frame.png"
#         )
#         fig.savefig(image_filename)

#         fig, ax = plt.subplots(figsize=(fig_width, 80))
#         ax.grid(True, color='r')
#         ax.plot_date(time_packet_start[1:], time_betweenpacket, ms=30)
#         ax.set_title("Time Difference Between Frames")
#         ax.set_xlabel("Unix Time of First Packet Per Frame")
#         ax.set_ylabel("Duration of Time Sent Between Frames (s)")

#         image_filename = (
#             graph_dir + "/between_frame.png"
#         )
#         fig.savefig(image_filename)

#         fig, ax = plt.subplots(figsize=(fig_width, 80))
#         ax.plot_date(time_packet_start, num_packets_per_frame, ms=30)
#         ax.set_title("Number of Packets Per Frame")
#         ax.set_xlabel("Unix Time of First Packet Per Frame")
#         ax.set_ylabel("Number of Packets Per Frame")

#         image_filename = (
#             graph_dir + "/num_packets.png"
#         )
#         fig.savefig(image_filename)

# if __name__ == "__main__":
#     run_main()
