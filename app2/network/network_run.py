# run tcpdump -> relevant packet info -> save to file
import multiprocessing as mp
from scapy.all import conf, get_if_addr, AsyncSniffer, L2ListenTcpdump, Packet
from scapy.layers.inet import UDP, IP
import time

from app2.network.parsing.packet_constants import ZoomMediaWrapper
from app2.network.parsing.zoom_packet import ZoomPacket


def filter_packet_function(packet: Packet):
    local_machine_ip_addr = get_if_addr(conf.iface)
    if (IP in packet
        and UDP in packet
        and hasattr(packet[UDP], "load")
        and packet[IP].dst == local_machine_ip_addr):
        udp_packet = ZoomPacket(packet)
        if (
            udp_packet.get_media_type() != ZoomMediaWrapper.INVALID
        ):
            return True
    
    return False

def capture_packets(queue: mp.Queue):
    t = AsyncSniffer(timeout=120, 
                    lfilter=filter_packet_function, 
                    prn=lambda pkt: queue.put(pkt),
                    opened_socket=L2ListenTcpdump())
    t.start()
    return t

def compute_metrics(queue: mp.Queue):
    packet: Packet = queue.get()
    print(packet)
    
def run_processes():
    queue = mp.Queue()
    capture_packets(queue)
    while True:
        packet = ZoomPacket(queue.get())
        print(packet.get_frame(), packet.get_number_packets_per_frame())




# if __name__ == "__main__":
#     run_processes()