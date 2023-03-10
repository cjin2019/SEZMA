import csv
import multiprocessing as mp
import psutil
import time
from datetime import datetime
from matplotlib import pyplot as plt
from typing import Dict, List

from app2.common.constants import SpecialQueueValues, TIME_FORMAT

def monitor_process_usage(process_ids: List[int], filename: str, log_queue, zoom_meeting_on: mp.Event) -> None:
    """
    Param: process_ids contains list of ids to monitor for
    Param: filename to store the monitor process metrics in
    Param: log_queue to add to log
    Param: zoom_meeting_on_check determines whether Zoom Meeting is still in progress on the user's laptop
    """
    zoom_meeting_on.wait()
    log_queue.put(f"started {__name__}.{monitor_process_usage.__name__}")

    processes: List[psutil.Process] = []
    for pid in process_ids:
        processes.append(psutil.Process(pid=pid))

    with open(filename, mode="w") as file:
        csv_writer = csv.writer(file)
        csv_writer.writerow(["time", "memory_percentage", "cpu_percentage"])

        while zoom_meeting_on.is_set():
            memory_percent_usage = 0
            cpu_percent_usage = 0
            for proc in processes:
                if proc.status() != psutil.STATUS_ZOMBIE:
                    memory_percent_usage += proc.memory_percent()
                    cpu_percent_usage += proc.cpu_percent() / mp.cpu_count()
            csv_writer.writerow([datetime.now().strftime(TIME_FORMAT), memory_percent_usage, cpu_percent_usage])
            time.sleep(20) # collect data every 10 seconds
    log_queue.put(f"finished {__name__}.{monitor_process_usage.__name__}")

def graph_metrics(graph_dir: str, csv_filename: str, log_queue) -> None:
    """
    Param: graph_dir is the directory where to store the graph outputs
    Param: csv_filename is the name of the file to read the metrics from, assumes there is a header row
    Param: log_queue is mp.Queue that contains a string with log information or SpecialQueueValue
    """
    log_queue.put(f"started {__name__}.{graph_metrics.__name__}")
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
    log_queue.put(f"finished {__name__}.{graph_metrics.__name__}")
    log_queue.put(SpecialQueueValues.FINISH)

