from scapy.all import *
from scapy.layers.inet import *

def run_pipeline():
    local_machine_ip_addr = get_if_addr(conf.iface)
    conf.use_pcap = True
    # Enable filtering: only Ether, IP and UDP will be dissected
    conf.layers.filter([Ether, IP, UDP])
    # Disable filtering: restore everything to normal
    # conf.layers.unfilter()
    source = SniffSource(iface=conf.iface,
                         filter=f"udp and dst host {local_machine_ip_addr}")
    source
    p = PipeEngine(source)
    p.start()