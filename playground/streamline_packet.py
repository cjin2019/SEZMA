import subprocess

from scapy.all import get_if_addr, conf, Packet
from scapy.layers.l2 import Ether
from scapy.layers.inet import IP, UDP

def run_tcp(timeout_sec=5) -> None:
    """
    Run tcp command with timeout given by timeout_sec
    Default timeout_sec = 5 meaning tcpdump runs for 5 seconds. 
    Otherwise, users must input timeout_sec > 0 (int).

    Runs tcpdump with sudo privileges. User must input sudo password in terminal

    sudo tcpdump -n udp -G 5 -W 1 -w sample.pcap
    https://stackoverflow.com/a/40330559
    5 = number of seconds you want to rotate
    """
    print(get_if_addr(conf.iface))
    tcp_process = subprocess.Popen(
        [
            "sudo",
            "tcpdump",
            "-xx",
            "udp",
            "and",
            "dst",
            "host",
            get_if_addr(conf.iface),
            ""
        ],
        stdout=subprocess.PIPE
    )


    try: 
        raw_data: bytes = b''
        for row in iter(tcp_process.stdout.readline, b''):
            if row[0:1] != b'\t':
                if len(raw_data) > 0:
                    print(Ether(raw_data)[IP].src)
                raw_data = b''
            else:
                raw_data += row[row.index(b':  ') + 3:].replace(b' ', b'').rstrip()
    except subprocess.TimeoutExpired:
        tcp_process.kill()

    
    # if tcp_process.stdout == None:
    #     return 

    # for row in iter(tcp_process.stdout.readline, b''):
    #     print(row.rstrip())   # process here


run_tcp()