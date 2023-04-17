import configparser
import csv
import json
import os
import multiprocessing as mp
import pgrep
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
    frame_rate: int = float(config["FrameRate"])
    output_directory: str = config["OutputDirectory"]

    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    return (frame_rate, output_directory)

def monitor_process_usage(app_to_process_ids: Dict[str, List[int]], filename: str) -> None:
    """
    Param: process_ids contains list of ids to monitor for
    Param: filename to store the monitor process metrics in
    Param: log_queue to add to log
    Param: zoom_meeting_on_check determines whether Zoom Meeting is still in progress on the user's laptop
    """

    processes: Dict[str, List[psutil.Process]] = {app: [] for app in app_to_process_ids}
    for app in app_to_process_ids:
        for pid in app_to_process_ids[app]:
            try:
                processes[app].append(psutil.Process(pid=pid))
            except psutil.NoSuchProcess as e:
                continue

    with open(filename, mode="w") as file:
        csv_writer = csv.writer(file)
        csv_writer.writerow(["time", "memory_percentage", "cpu_percentage"])

        while True:
            memory_percent_usage = 0
            cpu_percent_usage = 0
            battery_impact = 0
            try: 

                for proc in processes:
                    if proc.status() != psutil.STATUS_ZOMBIE:
                        memory_percent_usage += proc.memory_percent()
                        #cpu_percent_usage += sum([proc.cpu_percent() / mp.cpu_count() for i in range(3)])/3
                        #print("cpu percentage", proc.cpu_percent())
                        cpu_mem_value: str = subprocess.run(['top', '-pid', str(proc.pid), '-l', '3', '-stats', 'cpu,mem'], check=True, stdout=subprocess.PIPE).stdout.decode('UTF-8').split("\n")[-2]
                        # print(proc.pid, cpu_value)
                        print(cpu_mem_value)
                        print(mp.cpu_count())
                #         cpu_percent_usage += float(cpu_value) / mp.cpu_count()
                #         # print(subprocess.check_output(["top", "-pid", str(pid), "-l", str(3), "-stats" , "power", "|", "tail", "-1"]))
                # csv_writer.writerow([datetime.now().strftime(TIME_FORMAT), memory_percent_usage, cpu_percent_usage])
            except Exception as e:
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
        csvreader = csv.reader(csvfile, delimiter=' ')
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
            ax[row_idx].set_xlabel("Unix Time")
            ax[row_idx].set_ylabel(f"{process_metric_type}")

    image_filename = (
        graph_dir + "/" + "process_usage_timeline.png"
    )
    fig.savefig(image_filename)

def parse_mem_usage(mem_str) -> float:
    """
    returns in MB
    """ 
    if mem_str[-1] == "+" or mem_str[-1] == "-":
        mem_str = mem_str[:-1]
    if mem_str[-1] == "K":
        return float(mem_str[:-1])/1000
    else: #in M
        return float(mem_str[:-1])
    
def parse_monitor_files(
        filename: str, 
        num_users: int, 
        capture_rate: float, 
        other_applications: str,
        data_bytes_sent_per_second: str,
        device_type: str,
        mute: str,
        motion: str
    ) -> None:

    pid_cpu = {}
    pid_mem = {}
    with open(filename) as csvfile:
        csvreader = csv.reader(csvfile, delimiter=' ')
        for i, row in enumerate(csvreader):
            while '' in row:
                row.remove('')

            pid = int(row[1])
            if pid not in pid_cpu:
                pid_cpu[pid] = []
            if pid not in pid_mem:
                pid_mem[pid] = []
            
            pid_cpu[pid].append(float(row[-2]))
            pid_mem[pid].append(parse_mem_usage(row[-1]))
    
    
    # total
    with open("benchmark.csv", "a") as output:
        for pid in pid_cpu:
            num_data_points = len(pid_cpu[pid])
            data = [
                filename[:filename.index(".")], 
                str(pid), 
                str(num_users),
                str(capture_rate), 
                other_applications, 
                data_bytes_sent_per_second,
                device_type,
                mute,
                motion,
                str(sum(pid_cpu[pid]) / num_data_points),
                str(sum(pid_mem[pid]) / num_data_points)
            ]
            output.write(",".join(data)+"\n")
        
if __name__ == "__main__":
    config_setting = json.load(open("monitor/config.json"))
    parse_monitor_files(
        "videonetworkapp.csv", 
        config_setting["num_users"], 
        config_setting["capture_rate"], 
        config_setting["other_applications"],
        config_setting["data_bytes_sent_per_second"],
        config_setting["device_type"],
        config_setting["mute"],
        config_setting["motion"])
    parse_monitor_files(
        "zoom.csv", 
        config_setting["num_users"], 
        config_setting["capture_rate"], 
        config_setting["other_applications"],
        config_setting["data_bytes_sent_per_second"],
        config_setting["device_type"],
        config_setting["mute"],
        config_setting["motion"])
    ### wait until file exists with numbers
    # _, output_directory = open_config()

    # pid_csv = output_directory + "/pid.txt"
    # pids = []
    # with open(pid_csv, "r") as file:
    #     pids = file.readline().split(",")
    # pids = [int(pid) for pid in pids]
    
    # pids = {"videonetwork": pgrep.pgrep("videonetwork"), "zoom.us": pgrep.pgrep("videonetwork")}# for running the binary
    # print(pids)
    
    # process_usage_file = output_directory + "/process_usage.csv"
    # monitor_process_usage(pids, process_usage_file)
    # graph_metrics(output_directory, process_usage_file)