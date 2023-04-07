import configparser
import multiprocessing as mp
import os
import queue
from os.path import dirname, join
import sys
from paramiko import SSHClient, AutoAddPolicy
from typing import List, Tuple

import app.monitor as monitor
import app.network.network_run as network
import app.video.video_run as video
import app.video.video_run2 as video2
from app.common.constants import SpecialQueueValues, TIME_FORMAT

NO_KEYFILE_PATH = "NOT GIVEN"

def open_config() -> Tuple[float,str, str, bool]:
    """
    Returns frame rate, output directory for graphs and logs, key_filepath for remote server
    """
    config_all = configparser.ConfigParser()
    module_path = dirname(sys.argv[0])
    config_all.read(join(module_path, "config.ini"))
    
    config = config_all["DEFAULT"]
    frame_rate: float = float(config["FrameRate"])
    output_directory: str = config["OutputDirectory"]
    key_filepath: str = config["KeyFilePath"]
    send_existing_output: bool = "SendOutputToServer" in config

    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    return (frame_rate, output_directory, key_filepath, send_existing_output)

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

def send_results_to_server(local_directory, key_filepath, log_queue) -> None:
    """
    Param: local_directory directory where the graphs are stored
    Param: key_filepath is where the pem file to access the server is stored
    Param: log_queue is mp.Queue that contains a string with log information
    """
    log_queue.put(f"started  {__name__}.{send_results_to_server.__name__}")
    remote_directory = "/home/ubuntu/" + local_directory[local_directory.rindex("/")+1:]

    client = SSHClient()
    client.load_system_host_keys()
    client.set_missing_host_key_policy(AutoAddPolicy())

    client.connect(hostname='128.52.141.6', username='ubuntu', key_filename=key_filepath)

    sftp = client.open_sftp()
    try:
        sftp.chdir(remote_directory)  # Test if remote_path exists
    except IOError:
        sftp.mkdir(remote_directory)  # Create remote_path
        sftp.chdir(remote_directory)

    for filename in os.listdir(local_directory):
        if filename[-3:] == "png":
            sftp.put(local_directory + "/" + filename, remote_directory + "/" + filename)

    sftp.close()
    log_queue.put(f"finished  {__name__}.{send_results_to_server.__name__}")
    log_queue.put(SpecialQueueValues.FINISH)

# def run_app():
#     frame_rate, output_directory, key_filepath = open_config()
#     num_video_compute_processes = 6
    
#     video_data_queue = mp.Queue(maxsize=20)
#     video_metrics_queue = mp.Queue()
#     log_queue = mp.Queue()
#     event_check_zoom_meeting_open = mp.Event()

#     video_csv_filename = output_directory + "/video.csv"
#     network_csv_filename = output_directory + "/network.csv"
#     log_filename = output_directory + "/log.txt"

#     num_process_before_log_finished = 3 if key_filepath != NO_KEYFILE_PATH else 2 # for graphing and then send results to server 

#     log_process = mp.Process(
#         target=log_information, 
#         args=(log_queue, log_filename, num_process_before_log_finished,))
#     zoom_check_process = mp.Process(
#         target=video.check_zoom_window_up, 
#         args=(log_queue, event_check_zoom_meeting_open,))
    
#     network_process = mp.Process(
#         target=network.pipeline_run, 
#         args=(network_csv_filename, log_queue, event_check_zoom_meeting_open,))
    
#     video_capture_process = mp.Process(
#         target=video.capture_images, 
#         args=(frame_rate, video_data_queue, log_queue, event_check_zoom_meeting_open,))
#     video_compute_processes = [
#         mp.Process(
#             target=video.compute_metrics, 
#             args=(video_data_queue, video_metrics_queue, log_queue, event_check_zoom_meeting_open,)) 
#         for i in range(num_video_compute_processes)]
#     # done processing when compute_process is done
#     video_write_process = mp.Process(
#         target=video.write_metrics, 
#         args=(video_metrics_queue, video_csv_filename, log_queue, event_check_zoom_meeting_open,))

#     start_processes(
#         log_process,
#         zoom_check_process,
#         network_process,
#         video_capture_process,
#         video_compute_processes,
#         video_write_process,
#     )

#     pids = get_pids(
#         zoom_check_process,
#         network_process,
#         video_capture_process,
#         video_compute_processes,
#         video_write_process,
#     )
#     pids += [os.getpid()]
#     pids = [str(pid) for pid in pids]

#     pid_csv = output_directory + "/pid.txt"
#     with open(pid_csv, "w") as file:
#         file.write(",".join(pids))

#     join_processes(
#         zoom_check_process,
#         network_process,
#         video_capture_process,
#         video_compute_processes,
#         video_write_process,
#         # monitor_process_usage_process,
#     )

#     network.graph_metrics(graph_dir=output_directory, csv_filename=network_csv_filename, log_queue=log_queue)
#     video.graph_metrics(graph_dir=output_directory, csv_filename=video_csv_filename, log_queue=log_queue)

#     # want to end process after finished graphing
#     if key_filepath != NO_KEYFILE_PATH:
#         send_results_to_server(output_directory, key_filepath, log_queue)

#     log_process.join()

def run_app2():
    ctx = mp.get_context("spawn")

    frame_rate, output_directory, key_filepath, send_existing_output = open_config()
    
    log_queue = mp.JoinableQueue(maxsize=30)
    event_check_zoom_meeting_open = mp.Event()

    video_csv_filename = output_directory + "/video.csv"
    network_csv_filename = output_directory + "/network.csv"
    log_filename = output_directory + "/log.txt"

    num_process_before_log_finished = 3 if key_filepath != NO_KEYFILE_PATH else 2 # for graphing and then send results to server 

    log_process = ctx.Process(
        target=log_information, 
        args=(log_queue, log_filename, num_process_before_log_finished,))
    
    if not send_existing_output:
        zoom_check_process = ctx.Process(
            target=video.check_zoom_window_up, 
            args=(log_queue, event_check_zoom_meeting_open,))
        
        network_process = ctx.Process(
            target=network.pipeline_run, 
            args=(network_csv_filename, log_queue, event_check_zoom_meeting_open,))
        
        video_process = ctx.Process(
            target=video2.pipeline_run, 
            args=(video_csv_filename, frame_rate, log_queue, event_check_zoom_meeting_open,))

        # done processing when compute_process is done

        start_processes(
            log_process,
            zoom_check_process,
            network_process,
            video_process,
        )

        pids = get_pids(
            zoom_check_process,
            network_process,
            video_process,
        )
        pids += [os.getpid()]
        pids = [str(pid) for pid in pids]

        pid_csv = output_directory + "/pid.txt"
        with open(pid_csv, "w") as file:
            file.write(",".join(pids))

        join_processes(
            zoom_check_process,
            network_process,
            video_process,
            # monitor_process_usage_process,
        )
    else:
        log_process.start()

    network.graph_metrics(graph_dir=output_directory, csv_filename=network_csv_filename, log_queue=log_queue)
    video.graph_metrics(graph_dir=output_directory, csv_filename=video_csv_filename, log_queue=log_queue)

    # want to end process after finished graphing
    if key_filepath != NO_KEYFILE_PATH:
        send_results_to_server(output_directory, key_filepath, log_queue)

    log_process.join()

if __name__ == "__main__":
    run_app2()
