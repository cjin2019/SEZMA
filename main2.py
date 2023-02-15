import configparser
import logging
import multiprocessing as mp
import os
import time
from typing import Dict, Tuple

import app2.network.network_run as network
import app2.video.video_run as video

def open_config() -> Tuple[int,int,str]:
    """
    Returns duration in seconds, frame rate, output directory for graphs and logs
    """
    config_all = configparser.ConfigParser()
    config_all.read('config.ini')
    
    config = config_all["DEFAULT"]
    duration_seconds: int = int(config["DurationSeconds"])
    frame_rate: int = int(config["FrameRate"])
    output_directory: str = config["OutputDirectory"]

    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    return (duration_seconds, frame_rate, output_directory)

def run_app():

    while video.get_zoom_window_id() == -1:
        time.sleep(0.5)
    duration_seconds, frame_rate, output_directory = open_config()

    # log_filename = output_directory + "/logging.txt"
    # logging.basicConfig(filename=log_filename, level=logging.INFO)
    # set up structures 
    # network

    manager = mp.Manager()
    packet_queue = manager.Queue()
    network_metrics = manager.list()

    frame_queue = manager.Queue()
    video_metrics = manager.Queue()

    num_compute_video_processes = 3

    capture_network_process = mp.Process(target=network.capture_packets, args=(packet_queue, duration_seconds))
    capture_video_process = mp.Process(target=video.capture_images, args=(frame_rate, duration_seconds, frame_queue,))
    compute_network_metrics_process = mp.Process(target=network.compute_metrics, args=(packet_queue, network_metrics,))
    compute_video_metrics_processes = [mp.Process(target=video.compute_metrics, args=(frame_queue, video_metrics,)) for i in range(num_compute_video_processes)]
    graph_video_metrics_process = mp.Process(target=video.graph_metrics, args=(output_directory, video_metrics,))

    # start compute first since it takes the longest
    for process in compute_video_metrics_processes:
        process.start()
    capture_network_process.start()
    capture_video_process.start()
    compute_network_metrics_process.start()
    graph_video_metrics_process.start()

    capture_network_process.join()
    compute_network_metrics_process.join()
    network.graph_metrics(graph_dir=output_directory, metric_output=network_metrics)

    capture_video_process.join()
    for process in compute_video_metrics_processes:
        process.join()
    graph_video_metrics_process.join()


if __name__ == "__main__":
    run_app()