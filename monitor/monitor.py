import configparser
import csv
import os
import multiprocessing as mp
import psutil
import subprocess
import time
from datetime import datetime
from matplotlib import pyplot as plt
from typing import Dict, List, Tuple

TIME_FORMAT = "%Y-%m-%d %H:%M:%S.%f"

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

def monitor_process_usage(process_ids: List[int], filename: str) -> None:
    """
    Param: process_ids contains list of ids to monitor for
    Param: filename to store the monitor process metrics in
    Param: log_queue to add to log
    Param: zoom_meeting_on_check determines whether Zoom Meeting is still in progress on the user's laptop
    """

    processes: List[psutil.Process] = []
    for pid in process_ids:
        processes.append(psutil.Process(pid=pid))

    with open(filename, mode="w") as file:
        csv_writer = csv.writer(file)
        csv_writer.writerow(["time", "memory_percentage", "cpu_percentage", "battery_impact"])

        while True:
            memory_percent_usage = 0
            cpu_percent_usage = 0
            battery_impact = 0
            try: 
                for proc in processes:
                    if proc.status() != psutil.STATUS_ZOMBIE:
                        memory_percent_usage += proc.memory_percent()
                        cpu_percent_usage += proc.cpu_percent() / mp.cpu_count()
                        battery_value: str = subprocess.run(['top', '-pid', str(proc.pid), '-l', '3', '-stats', 'power'], check=True, stdout=subprocess.PIPE).stdout.decode('UTF-8').split("\n")[-2]
                        if battery_value == "":
                            break
                        battery_impact += float(battery_value)
                        # print(subprocess.check_output(["top", "-pid", str(pid), "-l", str(3), "-stats" , "power", "|", "tail", "-1"]))
                csv_writer.writerow([datetime.now().strftime(TIME_FORMAT), memory_percent_usage, cpu_percent_usage, battery_impact])
                time.sleep(20) # collect data every 10 seconds
            except psutil.NoSuchProcess as e:
                break

def graph_metrics(graph_dir: str, csv_filename: str) -> None:
    """
    Param: graph_dir is the directory where to store the graph outputs
    Param: csv_filename is the name of the file to read the metrics from, assumes there is a header row
    """
    times: List[datetime] = []
    process_data: Dict[str, List[float]] = {}
    process_metrics: List = []
    with open(csv_filename) as csvfile:
        csvreader = csv.reader(csvfile)
        for i, row in enumerate(csvreader):
            if i == 0:
                process_metrics = row[1:]
                process_data = {process_metric: [] for process_metric in process_metrics}                                       
            else:
                times.append(datetime.strptime(row[0], TIME_FORMAT))
                
                for idx, process_metric_type in enumerate(process_metrics, 1):
                    process_data[process_metric_type].append(float(row[idx]))

    # start plotting
    SMALL_SIZE = 250

    plt.rc("font", size=SMALL_SIZE)  # controls default text sizes
    plt.rc("axes", titlesize=SMALL_SIZE)  # fontsize of the axes title
    plt.rc("axes", labelsize=SMALL_SIZE)  # fontsize of the x and y labels
    plt.rc("xtick", labelsize=SMALL_SIZE)  # fontsize of the tick labels
    plt.rc("ytick", labelsize=SMALL_SIZE)  # fontsize of the tick labels

    fig, ax = plt.subplots(len(process_data), 1, figsize=(200, 100))
    fig.tight_layout(pad=5.0)

    for row_idx, process_metric_type in enumerate(process_data):
            ax[row_idx].grid(True, color='r')
            ax[row_idx].plot_date(times, process_data[process_metric_type], ms=30)
            ax[row_idx].set_title("Timeline of Frame Score")
            ax[row_idx].set_xlabel("Unix Time")
            ax[row_idx].set_ylabel(f"{process_metric_type}")

    image_filename = (
        graph_dir + "/" + "process_usage_timeline.png"
    )
    fig.savefig(image_filename)

if __name__ == "__main__":
    ### wait until file exists with numbers
    _, output_directory = open_config()

    pid_csv = output_directory + "/pid.txt"
    pids = []
    with open(pid_csv, "r") as file:
        pids = file.readline().split(",")
    pids = [int(pid) for pid in pids]
    
    process_usage_file = output_directory + "/process_usage.csv"
    monitor_process_usage(pids, process_usage_file)
    graph_metrics(output_directory, process_usage_file)