# run tcpdump -> relevant packet info -> save to file
import multiprocessing as mp
from scapy.all import conf, get_if_addr, AsyncSniffer, L2ListenTcpdump, Packet
from scapy.layers.inet import UDP, IP
import time

from app2.network.parsing.exceptions import PacketException
from app2.network.parsing.packet_constants import ZoomMediaWrapper
from app2.network.parsing.zoom_packet import ZoomPacket


def filter_packet_function(packet: Packet):
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

def capture_packets(queue: mp.Queue):
    t = AsyncSniffer(lfilter=filter_packet_function, 
                    prn=lambda pkt: queue.put(pkt),
                    opened_socket=L2ListenTcpdump())
    t.start()
    return t

def compute_metrics(queue: mp.Queue):
    packet: Packet = queue.get()
    print(packet)
    
def run_network_processes():
    queue = mp.Queue()
    capture_packets(queue)
    while True:
        packet = ZoomPacket.parse(queue.get())
        print(packet.frame_sequence, packet.number_of_packets_per_frame, packet.video_packet_type.name)




# if __name__ == "__main__":
#     run_processes()