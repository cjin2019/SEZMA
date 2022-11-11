import json
from pathlib import Path
from typing import List, Dict
from packet_time import PacketTime
from scapy.all import PacketList, get_if_addr, rdpcap, conf
from scapy.layers.inet import IP, UDP

from udp_packet import UDPPacket
from utilities import *

"""
NetworkData only supports parsing UDP packets
"""
class NetworkData:
    VIDEO_MEDIA_TYPE = 16
    def __init__(self, filename: str):
        self.filename: str = filename
        self.packets: PacketList = rdpcap(filename)
        self.local_ip_addr: str = get_if_addr(conf.iface)
        self.udp_packets = self.get_packets_from_other_zoom_server()

    
    def get_packets_from_other_zoom_server(self) -> List[UDPPacket]:
        """
        Gets the video UDP packets from other server. This can either be zoom server
        or direct communication with P2P
        """
        udp_packets: List[UDPPacket] = []
        for packet in self.packets:
            if IP in packet and UDP in packet and hasattr(packet[UDP], 'load') and packet[IP].dst == self.local_ip_addr:
                udp_packet = UDPPacket(packet)
                if udp_packet.get_media_type() == NetworkData.VIDEO_MEDIA_TYPE:
                    udp_packets.append(UDPPacket(packet))
        
        # udpPackets = [udpPacket for udpPacket in udpPackets if udpPacket.get_media_type()==16]
        return udp_packets
    
    def get_frame_period(self) -> Dict[bytes, List[float]]:
        """
        Returns a mapping of frame sequence number -> (time of first packet sent for frame, time of last packet for frame)
        """
        if len(self.udp_packets) == 0:
            return {}

        udp_packet1: UDPPacket = self.udp_packets[0]
        prev_frame: bytes = udp_packet1.get_frame()

        output = {prev_frame: [udp_packet1.time, udp_packet1.time]}
        for packet in self.udp_packets[1:]:
            curr_frame = packet.get_frame()
            curr_time = packet.time
            if curr_frame == prev_frame:
                output[prev_frame][1] = curr_time
            else:
                output[curr_frame] = [curr_time, curr_time]
            prev_frame = curr_frame

        return output

if __name__ == "__main__":
    config_dir = Path(__file__).parent.parent
    config_file = config_dir / "config.json"

    with config_file.open() as f:
        args = json.load(f)
        args_tcpdump = args["network_capture_config"]
        parser.check_process_inputs(args_tcpdump, {"output_file": str, "duration_seconds": int})

        network_data: NetworkData = NetworkData(args_tcpdump["output_file"])
        frame_periods = network_data.get_frame_period()
        for frame in frame_periods:
            print(f"frame seq number {frame}: ({frame_periods[frame][0]}, {frame_periods[frame][1]})")
            
