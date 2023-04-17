import csv
import json
import sys

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from matplotlib import pyplot as plt
from typing import Dict, List

TIME_FORMAT = "%Y-%m-%d %H:%M:%S.%f"

@dataclass
class NetworkMetrics:
    """
    Currently computes metrics based on the frame
    """
    frame_sequence_number: bytes
    packet_time: datetime
    packet_size: int
    expected_number_of_packets: int
    is_fec: bool

class MetricType(Enum):
    # BRISQUE = "BRISQUE"
    PIQE = "PIQE"
    NIQE = "NIQE"
    LAPLACIAN = "LAPLACIAN"

def get_timeformat(time_str: str) -> str:
    return '%Y-%m-%d %H:%M:%S.%f' if "." in time_str else '%Y-%m-%d %H:%M:%S'

def group_by_frames(csv_filename: str) -> Dict[bytes, NetworkMetrics]:
    """
    Param: csv_filename is the name of the file to read the metrics from
    """

    output: Dict[bytes, Dict] = defaultdict(list)
    started = False
    with open(csv_filename) as csv_file:
        csvreader = csv.reader(csv_file)
        for row in csvreader:
            if not started:
                started = True
                continue
            
            # account for 0 microsecond case
            try: 
                network_metrics = NetworkMetrics(
                    frame_sequence_number= bytes(row[0][2:], 'utf-8'),
                    packet_time= datetime.strptime(row[1], get_timeformat(row[1])),
                    packet_size= int(row[2]),
                    expected_number_of_packets= int(row[3]),
                    is_fec= row[4] == "True"
                )
                output[network_metrics.frame_sequence_number].append(network_metrics)
            except ValueError:
                continue
    
    return output

def graph_network_metrics(graph_dir: str, csv_filename: str) -> None:
    """
    Param: graph_dir is the directory where to store the graph outputs
    Param: csv_filename is the name of the file to read the metrics from
    """
    metric_output_by_frame = group_by_frames(csv_filename)

    # get the time and size
    times: List[datetime] = []
    sizes: List[int] = []

    # get interpacket time difference
    # get time difference between packets of different frames
    # get the number of packets per frame
    time_withinpacket: List[float] = []
    time_betweenpacket: List[float] = []
    num_packets_per_frame: List[int] = []
    time_packet_end: List[datetime] = []
    
    # get the number of packets that are type FEC
    # get the difference between the expected and actual number of packets
    num_fecs: List[int] = []
    num_compared_to_expected: List[int] = []

    for frame in metric_output_by_frame:
        metrics: List[NetworkMetrics] = metric_output_by_frame[frame]
        if len(metrics) == 0:
            continue
        num_packets: int = len(metrics)
        num_packets_per_frame.append(num_packets)

        # when added to metrics_output should be in chronological order
        packet_times = [metric.packet_time for metric in metrics]
        time_packet_end.append(packet_times[-1])
        time_withinpacket.append((packet_times[-1] - packet_times[0]).total_seconds())
        if len(times) > 0:
            time_betweenpacket.append((packet_times[0] - times[-1]).total_seconds())
        times += packet_times
        sizes += [metric.packet_size for metric in metrics]

        num_fecs.append(sum([1 if metric.is_fec else 0 for metric in metrics]))
        compared_to_expected = metrics[0].expected_number_of_packets - num_packets
        num_compared_to_expected.append(compared_to_expected)
        
        # if num_compared_to_expected[-1] >= 10:
        #     print(frame)

    # start plotting

    SMALL_SIZE = 250

    plt.rc("font", size=SMALL_SIZE)  # controls default text sizes
    plt.rc("axes", titlesize=SMALL_SIZE)  # fontsize of the axes title
    plt.rc("axes", labelsize=SMALL_SIZE)  # fontsize of the x and y labels
    plt.rc("xtick", labelsize=SMALL_SIZE)  # fontsize of the tick labels
    plt.rc("ytick", labelsize=SMALL_SIZE)  # fontsize of the tick labels

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

def graph_video_metrics(graph_dir: str, csv_filename: str) -> None:
    """
    Param: graph_dir is the directory where to store the graph outputs
    Param: csv_filename is the name of the file to read the metrics from
    """
    # get the time and size
    times: List[datetime] = []
    image_scores: Dict[MetricType, List[float]] = {}
    header = []

    stall_values: List[int] = []
    
    with open(csv_filename) as csvfile:
        csvreader = csv.reader(csvfile)
        for row in csvreader:
            if row[0] == "time":
                header = row
                image_scores = {MetricType(metric_str_val): [] for metric_str_val in header[1:-1]}                                                       
                continue
            times.append(datetime.strptime(row[0], TIME_FORMAT))
            for idx in range(1, len(row)-1):
                image_scores[MetricType(header[idx])].append(float(row[idx]))
                
            # code for checking if stalling exists
            stall_values.append(int(row[-1]))
            
            # fix the issue where laplacian scores are too high (ie. in 1000s)
            if image_scores[MetricType.LAPLACIAN][-1] > 600:
                # remove the last entry
                for metric_type in image_scores:
                    image_scores[metric_type].pop()
                times.pop()
                stall_values.pop()
                break
    # start plotting
    SMALL_SIZE = 250

    plt.rc("font", size=SMALL_SIZE)  # controls default text sizes
    plt.rc("axes", titlesize=SMALL_SIZE)  # fontsize of the axes title
    plt.rc("axes", labelsize=SMALL_SIZE)  # fontsize of the x and y labels
    plt.rc("xtick", labelsize=SMALL_SIZE)  # fontsize of the tick labels
    plt.rc("ytick", labelsize=SMALL_SIZE)  # fontsize of the tick labels

    fig, ax = plt.subplots(len(MetricType), 1, figsize=(200, 100))
    fig.tight_layout(pad=5.0)

    for row_idx, metric_type in enumerate(MetricType):
        ax[row_idx].grid(True, color='r')
        ax[row_idx].plot_date(times, image_scores[metric_type], ms=30)
        ax[row_idx].set_title("Timeline of Frame Score")
        ax[row_idx].set_xlabel("Unix Time")
        ax[row_idx].set_ylabel(f"{metric_type.value} Score")

    image_filename = (
        graph_dir + "/" + "frame_timeline.png"
    )
    fig.savefig(image_filename)

    fig, ax = plt.subplots(1, 1, figsize=(200, 100))
    fig.tight_layout(pad=5.0)

    ax.grid(True, color='r')
    ax.plot_date(times, stall_values, ms=30)
    ax.set_title("Stalling In Video")
    ax.set_xlabel("Unix Time")
    ax.set_ylabel(f"Stall or Not")

    image_filename = (
        graph_dir + "/" + "stall_timeline.png"
    )
    fig.savefig(image_filename)

if __name__ == "__main__":
    config = json.load(open("config.json"))
    directory = config + "/" + sys.argv[1]
    network_file = directory + "/" + sys.argv[2]
    video_file = directory + "/" + sys.argv[3]
    graph_network_metrics(directory, network_file)
    graph_video_metrics(directory, video_file)