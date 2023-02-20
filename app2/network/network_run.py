import csv
import logging
import multiprocessing as mp
import os
import time
from datetime import datetime
from enum import Enum
from matplotlib import pyplot as plt
from scapy.all import conf, get_if_addr, sniff, ConsoleSink, QueueSink, Packet, PipeEngine, SniffSource, TransformDrain
from scapy.layers.inet import UDP, IP
from typing import Dict, List, Tuple, Union

from app2.network.network_metrics import NetworkMetrics
from app2.network.parsing.exceptions import PacketException
from app2.network.parsing.packet_constants import RTPWrapper
from app2.network.parsing.zoom_packet import ZoomPacket

log = logging.getLogger(__name__)

class SpecialQueueValues(Enum):
    FINISH = 1
    NON_ZOOM_PACKET = 2

def pipeline_run(filename: str, zoom_meeting_check: mp.Event) -> None:
    local_machine_ip_addr = get_if_addr(conf.iface)
    source = SniffSource(iface=conf.iface,
                         filter=f"udp and dst host {local_machine_ip_addr}")
    filterTransform = TransformDrain(get_zoom_packet)
    sink = QueueSink()
    source > filterTransform > sink
    p = PipeEngine(source)
    zoom_meeting_check.wait() # wait until it's on
    p.start()
    print("just started network pipeline")
    write_metrics(filename, sink, zoom_meeting_check)
    p.stop()   
    print("finished network pipeline")
    
def start_pipeline(pipe_engine: PipeEngine, queue_sink: QueueSink) -> None:
    pipe_engine.start()
    time.sleep(5)
    pipe_engine.stop()
    queue_sink.push(SpecialQueueValues.FINISH)

def write_metrics(filename: str, sink: QueueSink, zoom_meeting_check):
    start_time = None

    with open(filename, "w") as csv_file:
        csv_writer = csv.writer(csv_file)
        while zoom_meeting_check.is_set():
            received_object = sink.recv(timeout=5) # 5 second timeout this means there is only 1 person on call
            if received_object == None:
                continue
            if type(received_object) == SpecialQueueValues and received_object == SpecialQueueValues.NON_ZOOM_PACKET:
                continue
            packet: "ZoomPacket" = received_object
            metrics = NetworkMetrics(
                    frame_sequence_number = packet.frame_sequence,
                    packet_time = packet.time.get_datetime(),
                    packet_size = packet.size,
                    expected_number_of_packets= packet.number_of_packets_per_frame,
                    is_fec = packet.video_packet_type == RTPWrapper.FEC
            )

            if start_time == None:
                start_time = packet.time.get_datetime()
                csv_writer.writerow(metrics.__dict__.keys())
            csv_writer.writerow(metrics.__dict__.values())
            # if (packet.time.get_datetime() - start_time).total_seconds() > duration_second:
            #     break

def get_zoom_packet(packet: Packet) -> Union[ZoomPacket,SpecialQueueValues]:
    try:
        return ZoomPacket.parse(packet)
    except PacketException:
        return SpecialQueueValues.NON_ZOOM_PACKET

    
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
    local_machine_ip_addr = get_if_addr(conf.iface)
    print(local_machine_ip_addr)
    output = sniff( 
            filter=f"udp and dst host {local_machine_ip_addr}",
            prn=lambda pkt: queue.put(pkt),
            timeout=duration_seconds,
        )
    # time.sleep(2)
    queue.put(SpecialQueueValues.FINISH)
    print("number captured:", len(output))

    zoom_packets = []
    for packet in output:
        try:
            zoom_packets.append(ZoomPacket.parse(packet))
        except PacketException:
            continue
    print("number of zoom packets captured: ", len(zoom_packets))
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
        if type(packet) == SpecialQueueValues and packet == SpecialQueueValues.FINISH:
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

def run_network_processes(duration_seconds: int, graph_dir: str) -> None:
    manager = mp.Manager()
    packet_queue = manager.Queue()
    metric_queue = manager.list()
    capture_packets_process = mp.Process(target=capture_packets, args=(packet_queue, duration_seconds))
    compute_metrics_process = mp.Process(target=compute_metrics, args=(packet_queue, metric_queue, ))

    capture_packets_process.start()
    compute_metrics_process.start()

    capture_packets_process.join()
    compute_metrics_process.join()

    if not os.path.exists(graph_dir):
        os.makedirs(graph_dir)
    print(len(metric_queue))
    graph_metrics(graph_dir, metric_queue)


def run2():
    pipeline_run()
# if __name__ == "__main__":
#     run_processes()