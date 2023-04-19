import json
import multiprocessing as mp
import os
import queue
import requests

from os.path import dirname, join
import sys
from datetime import datetime
from paramiko import SSHClient, AutoAddPolicy
from typing import List, Tuple

import app.network.network_run as network
import app.video.video_run as video
from app.video.metrics.image_score import MetricType
from app.common.constants import SpecialQueueValues

def open_config() -> Tuple[float,str, str, List[MetricType]]:
    """
    Returns frame rate, output directory for graphs and logs, key_filepath for remote server
    """
    module_path = dirname(sys.argv[0])
    config = json.load(open(join(module_path, "config.json")))
    
    frame_rate: float = float(config["FrameRate"])
    output_directory: str = config["OutputDirectory"]
    ip_address: str = config["IPAddress"]
    video_metrics_to_use: List[MetricType] = [MetricType(metric_type_str) for metric_type_str in config["VideoMetricsUsed"]]
    
    # send_existing_output: bool = "SendOutputToServer" in config

    current_time = datetime.now().strftime("%Y-%m-%d_%H_%M")
    output_directory += "/" + current_time
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)
    
    if output_directory[-1] == "/":
        output_directory = output_directory[:-1]
    return (frame_rate, output_directory, ip_address, video_metrics_to_use)

def log_information(data_queue, filename: str, num_processes_finished: int = 1, flush_every_nth_line: int = 1):
    """
    Param: data_queue contains list of strings to log to a file
    Param: filename the name of the file to log in
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
                data_queue.task_done()
            except queue.Empty:
                # want to continue running for logging in general
                if count_processes_done >= num_processes_finished:
                    break
        
        file.write("all processes finished\n")
        file.flush()


def start_processes(*processes) -> None:
    """
    Param: processes either a Process or a List[Process]
    Process is either multiprocess.Process or spawned process 
    multiprocess.get_context("spawn").Process
    """
    for val in processes:
        if type(val) != list:
            val.start()
        else:
            for process in val:
                process.start()

def get_pids(*processes) -> List[int]:
    """
    Param: processes either a multiprocess.Process or a List[multiprocess.Process]
    """
    output = []
    for val in processes:
        if type(val) != list:
            output.append(val.pid)
        else:
            for process in val:
                output.append(process.pid)
    return output

def join_processes(*processes) -> None:
    """
    Param: processes either a multiprocess.Process or a List[multiprocess.Process]
    """
    for val in processes:
        if type(val) != list:
            val.join()
        else:
            for process in val:
                process.join()

def send_files_to_web_server(website_address, local_directory, log_queue) -> None:
    log_queue.put(f"started  {__name__}.{send_files_to_web_server.__name__}")
    for filename in os.listdir(local_directory):
        if filename[-3:] == "csv":
            url = website_address + "/upload"
            files = {'files': open(local_directory + "/" + filename, 'rb')}
            remote_directory = local_directory[local_directory.rindex("/")+1:]
            requests.post(url, files=files, params={"directory": remote_directory})
    log_queue.put(f"finished  {__name__}.{send_files_to_web_server.__name__}")
    log_queue.put(SpecialQueueValues.FINISH)

def delete_all_files(local_directory, log_queue) -> None:
    log_queue.put(f"started  {__name__}.{delete_all_files.__name__}")
    for filename in os.listdir(local_directory):
        # construct full file path
        file = local_directory + "/" + filename
        if os.path.isfile(file):
            print('Deleting file:', file)
            os.remove(file)
    os.rmdir(local_directory)
    log_queue.put(f"finished  {__name__}.{delete_all_files.__name__}")
    log_queue.put(SpecialQueueValues.FINISH)

def run_app2():
    ctx = mp.get_context("spawn")

    frame_rate, output_directory, ip_address, video_metrics_to_use = open_config()
    
    log_queue = mp.JoinableQueue(maxsize=30)
    event_check_zoom_meeting_open = mp.Event()

    video_csv_filename = output_directory + "/video.csv"
    network_csv_filename = output_directory + "/network.csv"
    log_filename = output_directory + "/log.txt"

    num_process_before_log_finished = 2 # graphing network, graphing video, sending results to server, and deleting on local

    log_process = ctx.Process(
        target=log_information, 
        args=(log_queue, log_filename, num_process_before_log_finished,))
    
    zoom_check_process = ctx.Process(
        target=video.check_zoom_window_up, 
        args=(log_queue, event_check_zoom_meeting_open,))
    
    network_process = ctx.Process(
        target=network.pipeline_run, 
        args=(network_csv_filename, log_queue, event_check_zoom_meeting_open,))
    
    video_process = ctx.Process(
        target=video.pipeline_run, 
        args=(video_csv_filename, frame_rate, log_queue, event_check_zoom_meeting_open,video_metrics_to_use))

    start_processes(
        log_process,
        zoom_check_process,
        network_process,
        video_process,
    )

    join_processes(
        zoom_check_process,
        network_process,
        video_process,
    )

    send_files_to_web_server(ip_address, output_directory, log_queue)

    # delete all files from directory
    delete_all_files(local_directory=output_directory, log_queue=log_queue)

    log_process.join()

if __name__ == "__main__":
    run_app2()