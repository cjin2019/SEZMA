import app2.video.video_run as video_streamliner
import app2.network.network_run as network

if __name__ == "__main__":
    # video_streamliner.run_processes()
    network_streamliner: network.Network = network.Network()
    network_streamliner.run_network_processes()