import configparser
import multiprocessing as mp
import os
import queue
from typing import Tuple

import app2.network.network_run as network
import app2.video.video_run as video
from app2.common.constants import SpecialQueueValues

def open_config() -> Tuple[int,str]:
    """
    Returns duration in seconds, frame rate, output directory for graphs and logs
    """
    config_all = configparser.ConfigParser()
    config_all.read('config.ini')
    
    config = config_all["DEFAULT"]
    frame_rate: int = int(config["FrameRate"])
    output_directory: str = config["OutputDirectory"]

    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    return (frame_rate, output_directory)

def log_information(data_queue, filename: str, zoom_meeting_on_check, num_processes_finished: int = 1, flush_every_nth_line: int = 1):
    """
    Param: data_queue contains list of strings to log to a file
    Param: filename the name of the file to log in
    Param: zoom_meeting_on_check determines whether Zoom Meeting is still in progress on the user's laptop
    Param: num_processes_finished is the number of processes that should finish before ending this function
    Param: flush_every_nth_line flushes n lines to the file
    """
    line_count = 0
    count_processes_done = 0

    with open(filename, mode="w") as file:
        while True:
            try:
                res = data_queue.get(timeout=50)
                if type(res) == SpecialQueueValues and res == SpecialQueueValues.FINISH:
                    count_processes_done += 1
                if type(res) == str:
                    file.write(res+'\n')
                    line_count = (line_count + 1) % flush_every_nth_line

                    if line_count == 0:
                        file.flush()
            except queue.Empty:
                # want to continue running for logging in general
                if count_processes_done >= num_processes_finished:
                    break

def start_processes(*processes) -> None:
    """
    Param: processes either a multiprocess.Process or a List[multiprocess.Process]
    """
    for val in processes:
        if type(val) == mp.Process:
            val.start()
        else:
            for process in val:
                process.start()

def join_processes(*processes) -> None:
    """
    Param: processes either a multiprocess.Process or a List[multiprocess.Process]
    """
    for val in processes:
        if type(val) == mp.Process:
            val.join()
        else:
            for process in val:
                process.join()

def run_app():
    frame_rate, output_directory = open_config()
    num_video_compute_processes = 8
    
    video_data_queue = mp.Queue()
    video_metrics_queue = mp.Queue()
    log_queue = mp.Queue()
    event_check_zoom_meeting_open = mp.Event()

    video_csv_filename = output_directory + "/video.csv"
    network_csv_filename = output_directory + "/network.csv"
    log_filename = output_directory + "/log.txt"

    log_process = mp.Process(target=log_information, args=(log_queue, log_filename, event_check_zoom_meeting_open,2))
    zoom_check_process = mp.Process(target=video.check_zoom_window_up, args=(log_queue, event_check_zoom_meeting_open,))
    
    network_process = mp.Process(target=network.pipeline_run, args=(network_csv_filename, log_queue, event_check_zoom_meeting_open,))
    
    video_capture_process = mp.Process(target=video.capture_images, args=(frame_rate, video_data_queue, log_queue, event_check_zoom_meeting_open,))
    video_compute_processes = [mp.Process(target=video.compute_metrics, args=(video_data_queue, video_metrics_queue, log_queue, event_check_zoom_meeting_open,)) for i in range(num_video_compute_processes)]
    # done processing when compute_process is done
    video_write_process = mp.Process(target=video.write_metrics, args=(video_metrics_queue, video_csv_filename, log_queue, event_check_zoom_meeting_open,))

    start_processes(
        log_process,
        zoom_check_process,
        network_process,
        video_capture_process,
        video_compute_processes,
        video_write_process,
    )

    join_processes(
        zoom_check_process,
        network_process,
        video_capture_process,
        video_compute_processes,
        video_write_process,
    )

    network.graph_metrics(graph_dir=output_directory, csv_filename=network_csv_filename, log_queue=log_queue)
    video.graph_metrics(graph_dir=output_directory, csv_filename=video_csv_filename, log_queue=log_queue)

    # want to end process after finished graphing
    log_process.join()

def run_network_only():
    frame_rate, output_directory = open_config()
    log_queue = mp.Queue()
    event_check_zoom_meeting_open = mp.Event()

    video_csv_filename = output_directory + "/video.csv"
    network_csv_filename = output_directory + "/network.csv"
    log_filename = output_directory + "/log.txt"

    log_process = mp.Process(target=log_information, args=(log_queue, log_filename, event_check_zoom_meeting_open,1))
    zoom_check_process = mp.Process(target=video.check_zoom_window_up, args=(log_queue, event_check_zoom_meeting_open,))

    network_process = mp.Process(target=network.pipeline_run, args=(network_csv_filename, log_queue, event_check_zoom_meeting_open,))

    start_processes(
        log_process,
        zoom_check_process,
        network_process,
    )

    join_processes(
        zoom_check_process,
        network_process,
    )

    network.graph_metrics(graph_dir=output_directory, csv_filename=network_csv_filename, log_queue=log_queue)

    # want to end process after finished graphing
    log_process.join()
if __name__ == "__main__":
    run_network_only()


    # run_app()
    
# OLD CODE

# def run_app():

#     while video.get_zoom_window_id() == -1:
#         time.sleep(0.5)
#     duration_seconds, frame_rate, output_directory = open_config()

#     # log_filename = output_directory + "/logging.txt"
#     # logging.basicConfig(filename=log_filename, level=logging.INFO)
#     # set up structures 
#     # network

#     manager = mp.Manager()
#     packet_queue = manager.Queue()
#     network_metrics = manager.list()

#     frame_queue = manager.Queue()
#     video_metrics = manager.Queue()

#     num_compute_video_processes = 3

#     capture_network_process = mp.Process(target=network.capture_packets, args=(packet_queue, duration_seconds))
#     capture_video_process = mp.Process(target=video.capture_images, args=(frame_rate, duration_seconds, frame_queue,))
#     compute_network_metrics_process = mp.Process(target=network.compute_metrics, args=(packet_queue, network_metrics,))
#     compute_video_metrics_processes = [mp.Process(target=video.compute_metrics, args=(frame_queue, video_metrics,)) for i in range(num_compute_video_processes)]
#     graph_video_metrics_process = mp.Process(target=video.graph_metrics, args=(output_directory, video_metrics,))

#     # start compute first since it takes the longest
#     for process in compute_video_metrics_processes:
#         process.start()
#     capture_network_process.start()
#     capture_video_process.start()
#     compute_network_metrics_process.start()
#     graph_video_metrics_process.start()

#     capture_network_process.join()
#     compute_network_metrics_process.join()
#     network.graph_metrics(graph_dir=output_directory, metric_output=network_metrics)

#     capture_video_process.join()
#     for process in compute_video_metrics_processes:
#         process.join()
#     graph_video_metrics_process.join()
