# run tcpdump -> relevant packet info -> save to file
import multiprocessing as mp
import os
from datetime import datetime
from matplotlib import pyplot as plt
from scapy.all import conf, get_if_addr, AsyncSniffer, L2ListenTcpdump, Packet
from scapy.layers.inet import UDP, IP
from typing import Dict, List

from app2.network.network_metrics import NetworkMetricsByFrame
from app2.network.parsing.exceptions import PacketException
from app2.network.parsing.packet_constants import RTPWrapper
from app2.network.parsing.zoom_packet import ZoomPacket

class Network:
    def __init__(self):
        self.__frame_metrics: Dict[bytes, NetworkMetricsByFrame] = {}

    def filter_packet_function(self, packet: Packet) -> bool:
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

    def capture_packets(self, queue: mp.Queue) -> AsyncSniffer:
        t = AsyncSniffer(lfilter=self.filter_packet_function, 
                        prn=lambda pkt: queue.put(pkt),
                        opened_socket=L2ListenTcpdump())
        t.start()
        return t

    def compute_metrics(self, queue: mp.Queue) -> None:
        packet: ZoomPacket = ZoomPacket.parse(queue.get())
        frame_squence_nume: bytes = packet.frame_sequence
        if frame_squence_nume not in self.__frame_metrics:
            self.__frame_metrics[frame_squence_nume] = NetworkMetricsByFrame(
                sequence_number=frame_squence_nume,
                packet_times=[packet.time.get_datetime()],
                packet_sizes=[packet.size],
                expected_number_of_packets=packet.number_of_packets_per_frame,
                actual_number_of_packets=1,
                num_fecs=1 if packet.video_packet_type == RTPWrapper else 0
            )
        else:
            self.__frame_metrics[frame_squence_nume].update(packet)
        
    def graph_metrics(self, graph_dir: str) -> None:
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

        for frame in self.__frame_metrics:
            metrics: "NetworkMetricsByFrame" = self.__frame_metrics[frame]
            num_packets: int = metrics.actual_number_of_packets
            num_packets_per_frame.append(num_packets)

            packet_times = metrics.packet_times
            time_packet_end.append(packet_times[-1])
            time_withinpacket.append((packet_times[-1] - packet_times[0]).total_seconds())
            if len(times) > 0:
                time_betweenpacket.append((packet_times[0] - times[-1]).total_seconds())
            times += metrics.packet_times
            
            sizes += metrics.packet_sizes

            num_fecs.append(metrics.num_fecs)
            compared_to_expected = metrics.expected_number_of_packets - metrics.actual_number_of_packets
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

    def run_network_processes(self) -> None:
        queue = mp.Queue()
        capture_start_time = datetime.now()
        t = self.capture_packets(queue)
        while (datetime.now() - capture_start_time).total_seconds() <= 15: # for now run for only five seconds
            self.compute_metrics(queue)
        
        t.stop()
        queue.close()

        graph_dir = "/sample_dir"
        if not os.path.exists(graph_dir):
            os.makedirs(graph_dir)
        self.graph_metrics(graph_dir)



# if __name__ == "__main__":
#     run_processes()