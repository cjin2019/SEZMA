import logging
import multiprocessing as mp
import os
from datetime import datetime
from matplotlib import pyplot as plt
from scapy.all import conf, get_if_addr, sniff, L2ListenTcpdump, Packet
from scapy.layers.inet import UDP, IP
from typing import Dict, List

from app2.network.network_metrics import NetworkMetrics
from app2.network.parsing.exceptions import PacketException
from app2.network.parsing.packet_constants import RTPWrapper
from app2.network.parsing.zoom_packet import ZoomPacket

FINISH = 1
log = logging.getLogger(__name__)

def filter_packet_function(packet: Packet) -> bool:
    local_machine_ip_addr = get_if_addr(conf.iface)
    if (IP in packet
        and UDP in packet
        and hasattr(packet[UDP], "load")
        and packet[IP].dst == local_machine_ip_addr):
        try:
            ZoomPacket.parse(packet)
            return True
        except PacketException:
            return False
    
    return False

def capture_packets(queue, duration_seconds: float) -> None:
    """
    Param: queue = mp.Manager.Queue
    """
    print(f"started {__name__}.{capture_packets.__name__}")
    sniff(lfilter=filter_packet_function, 
            prn=lambda pkt: queue.put(pkt),
            opened_socket=L2ListenTcpdump(),
            timeout=duration_seconds,
        )
    queue.put(FINISH)
    print(f"finished {__name__}.{capture_packets.__name__}")

def compute_metrics(packet_queue, metric_output: List["NetworkMetrics"]):
    """
    Param: packet_queue = mp.Manager.Queue containing Packet from scapy.all module
    Param: metric_output = mp.Manager.list where it is a list of NetworkMetric
    Adds NetworkMetrics to metric_output 
    """
    print(f"started {__name__}.{compute_metrics.__name__}")
    while True:
        packet = packet_queue.get()
        if type(packet) == int and packet == FINISH:
            break

        packet = ZoomPacket.parse(packet)

        frame_squence_num: bytes = packet.frame_sequence
        metric_output.append(
            NetworkMetrics(
                frame_sequence_number = frame_squence_num,
                packet_time = packet.time.get_datetime(),
                packet_size = packet.size,
                expected_number_of_packets= packet.number_of_packets_per_frame,
                is_fec = packet.video_packet_type == RTPWrapper.FEC
            )
        )
    print(f"finished {__name__}.{compute_metrics.__name__}")

def group_by_frame(metric_output) -> Dict[bytes, List["NetworkMetrics"]]:
    """
    Param: metric_output = mp.Manager.list where it is a list of NetworkMetric
    """
    output: Dict[bytes, List["NetworkMetrics"]] = {}
    for metric in metric_output:
        if metric.frame_sequence_number not in output:
            output[metric.frame_sequence_number] = []
        output[metric.frame_sequence_number].append(metric)
    
    return output
def graph_metrics(graph_dir: str, metric_output) -> None:
    """
    Param: metric_output = mp.Manager.list where it is a list of NetworkMetric
    """

    print(f"started  {__name__}.{graph_metrics.__name__}")
    metric_output_by_frame = group_by_frame(metric_output)

    # get the time and size
    times: List[datetime] = []
    sizes: List[int] = []

    # get interpacket difference
    # get time difference between packets of different frames
    # get the number of packets per frame
    time_withinpacket: List[float] = []
    time_betweenpacket: List[float] = []
    num_packets_per_frame: List[int] = []
    time_packet_end: List[datetime] = []

    num_fecs: List[int] = []
    num_compared_to_expected: List[int] = []

    for frame in metric_output_by_frame:
        metrics: List["NetworkMetrics"] = metric_output_by_frame[frame]
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
    print(f"finished {__name__}.{graph_metrics.__name__}")

# def run_network_processes(self, graph_dir: str) -> None:
#     packet_queue = mp.Queue()
#     metric_records = mp.Manager()
#     capture_packets_process = mp.Process(target=capture_packets, args=(queue,))
#     compute_metrics = mp.Process(target=capture_packets, )

#     if not os.path.exists(graph_dir):
#         os.makedirs(graph_dir)
#     graph_metrics(graph_dir, me)



# if __name__ == "__main__":
#     run_processes()