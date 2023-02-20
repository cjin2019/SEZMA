from scapy.all import conf, get_if_addr, SniffSource, TransformDrain, QueueSink

if __name__ == "__main__":
    local_machine_ip_addr = get_if_addr(conf.iface)
    source = SniffSource(iface=conf.iface,
                         filter=f"udp and dst host {local_machine_ip_addr}")
    filterTransform = TransformDrain()
    sink = QueueSink()
    
