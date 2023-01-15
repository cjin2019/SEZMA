import json
import matplotlib.colors as mcolors
from brisque import BRISQUE
from matplotlib import image as plt_img, pyplot as plt
from pathlib import Path
from typing import List, Tuple

from utilities import parser
from analysis.frame.packet_to_frame import parse_frames_from_filenames
from analysis.packet.network_data import NetworkData

def map_frame_to_color(frame: bytes) -> str:
    colors = [
        color for color in mcolors.get_named_colors_mapping() if color[:4] == "xkcd"
    ]
    frame_val: int = int.from_bytes(frame, "big")
    return colors[frame_val % len(colors)]

def get_frame_score_times(frame_dir: str, every_nth: int = 1, end_unix_time: float = float('inf')) -> Tuple[List[float], List[float]]:
    brisque_scorer = BRISQUE()
    count = 0
    scores: List[float] = []
    times: List[float] = []
    for frame in parse_frames_from_filenames(frame_dir):
        if count % every_nth == 0:
            img = plt_img.imread(frame_dir + "/" + frame.filename)
            curr_score = brisque_scorer.score(img)
            scores.append(curr_score)
            times.append(frame.time.unix_time)
        count += 1
        if count % 100 == 0:
            print(count)
        if frame.time.unix_time > end_unix_time:
            break
    return scores, times

def get_packet_size_times(packet_filename: str) -> Tuple[List[float], List[float], List[str]]:
    network_data: NetworkData = NetworkData(packet_filename)
    packets_per_frame = network_data.get_packets_per_frame()

    sizes: List[float] = []
    times: List[float] = []
    colors: List[str] = []

    for frame in packets_per_frame:
        frame_times = [packet.time.get_unix_time() for packet in packets_per_frame[frame]]
        times += frame_times

        frame_sizes = [
            packet.get_packet_size() for packet in packets_per_frame[frame]
        ]
        sizes += frame_sizes
        colors += [map_frame_to_color(frame)] * len(frame_sizes)
    
    return sizes, times, colors

def get_xticks(min_x: float, max_x: float, num_ticks: int) -> List[float]:
    """
    num_ticks >= 2
    """
    tick_dist: float = (max_x - min_x)/(num_ticks - 1)
    return [min_x + tick_dist * i for i in range(num_ticks)]

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

        packet_filename = args_tcpdump["output_file"]
        packet_sizes, packet_times, packet_frame_colors = get_packet_size_times(packet_filename)

        frame_dir = args_frames["output_frame_dir"]
        frame_scores, frame_times = get_frame_score_times(frame_dir, end_unix_time=packet_times[-1])

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

        fig, ax = plt.subplots(2, 1, figsize=(100, 160))
        
        xticks = get_xticks(min(frame_times[0], packet_times[0]), max(frame_times[-1], packet_times[-1]), 5)

        frame_plot = ax[0]
        frame_plot.scatter(frame_times, frame_scores, s=800)
        frame_plot.set_title("Timeline of Frame Score")
        frame_plot.set_xlabel("Unix Time")
        frame_plot.set_ylabel("BRISQUE Score")
        frame_plot.set_xticks(xticks)

        packet_plot = ax[1]
        packet_plot.scatter(packet_times, packet_sizes, c=packet_frame_colors, s=800)
        packet_plot.set_title("Timeline of Packets Sent per Frame")
        packet_plot.set_xlabel("Unix Time")
        packet_plot.set_ylabel("Packet Size (bytes)")
        packet_plot.set_xticks(xticks)

        image_filename = (
            args_tcpdump["output_file"][: args_tcpdump["output_file"].rindex(".")]
            + "_frame_timeline.png"
        )
        fig.savefig(image_filename)
        
