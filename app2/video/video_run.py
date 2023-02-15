# screen capture -> compute metrics -> save 
import logging
import multiprocessing
import numpy as np
import Quartz
import Quartz.CoreGraphics as cg
import time

from collections import defaultdict
from datetime import datetime
from matplotlib import pyplot as plt
from typing import Dict, List

from app2.video.metrics.image_score import MetricType, get_no_ref_score
from app2.video.video_metrics import VideoMetrics

# close until no more to capture
FINISH = 1
log = logging.getLogger(__name__)

def get_zoom_window_id() -> int:
    """
    Returns the window ID of Zoom Meeting. Otherwise, -1 if there is no such meeting
    """
    windows = Quartz.CGWindowListCopyWindowInfo(Quartz.kCGWindowListExcludeDesktopElements | Quartz.kCGWindowListOptionOnScreenOnly, Quartz.kCGNullWindowID)
    for win in windows:
        if win[Quartz.kCGWindowOwnerName] == 'zoom.us' and win.get(Quartz.kCGWindowName, '') == 'Zoom Meeting':
            return int(win.get(Quartz.kCGWindowNumber, ''))
    return -1
        
def capture_image(window_num: int) -> np.ndarray:
    """
    Param: window_num > 0
    Gets the raw image data of the window given window_num
    """
    cg_image = Quartz.CGWindowListCreateImage(Quartz.CGRectNull, Quartz.kCGWindowListOptionIncludingWindow, window_num, Quartz.kCGWindowImageBoundsIgnoreFraming)

    bpr = cg.CGImageGetBytesPerRow(cg_image)
    width = cg.CGImageGetWidth(cg_image)
    height = cg.CGImageGetHeight(cg_image)

    cg_dataprovider = cg.CGImageGetDataProvider(cg_image)
    cg_data = cg.CGDataProviderCopyData(cg_dataprovider)
    np_raw_data = np.frombuffer(cg_data, dtype=np.uint8)

    np_data = np.lib.stride_tricks.as_strided(np_raw_data,
                                            shape=(height, width, 3),
                                            strides=(bpr, 4, 1),
                                            writeable=False)
    return np_data
    

def capture_images(frame_rate: float, duration_seconds: float, data_queue):
    """
    Params: frame_rate: frames per second
    Param: data_queue is mp.Manager.Queue containing np.arrays of images

    Assume that the video call has already started
    """
    print(f"started {__name__}.{capture_image.__name__}")
    window_num: int = get_zoom_window_id()
    time_between_frame: float = 1/frame_rate
    
    capture_start_time = datetime.now()
    while (datetime.now() - capture_start_time).total_seconds() <= duration_seconds: # for now run for only five seconds
        image_start_time = datetime.now()
        raw_data: np.ndarray = capture_image(window_num)
        data_queue.put((image_start_time, raw_data))
        image_finish_time = datetime.now()

        diff = (image_finish_time - image_start_time).total_seconds()
        if(diff < time_between_frame):
            time.sleep(time_between_frame - diff)
    data_queue.put(FINISH)
    # data_queue.close()
    print(f"finished {__name__}.{capture_image.__name__}")

def compute_metrics(data_queue, result_queue):
    """
    Param: data_queue is mp.Manager.Queue containing the raw numpy array of video frames
    Param: result_queue is mp.Manager.Queue containing the VideoMetrics record
    """
    print(f"started {__name__}.{compute_metrics.__name__}")
    count_images: int = 0
    num_image_process_print: int = 100

    while True:
        try:
            res = data_queue.get()
            if type(res) == int and res == FINISH:
                break
            image_capture_time, image_data = res
            metric_record: "VideoMetrics" = VideoMetrics(
                time=image_capture_time,
                metrics= {metric_type: get_no_ref_score(image_data, metric_type) for metric_type in MetricType}
            )
            result_queue.put(metric_record)
            count_images += 1
            if count_images % num_image_process_print == 0:
                print(f"processed {count_images} images")
        except ValueError as e:
            print(f"error in {__name__}.{compute_metrics.__name__}: {e}")
            break
    result_queue.put(FINISH)
    print(f"finished {__name__}.{compute_metrics.__name__}")

def graph_metrics(graph_dir: str, result_queue: multiprocessing.Queue) -> None:
    # get the time and size
    times: List[datetime] = []
    image_scores: Dict[MetricType, List[float]] = defaultdict(list)
    
    print(f"started {__name__}.{graph_metrics.__name__}")
    while True:
        try:
            metric_record = result_queue.get()
            if type(metric_record) == int and metric_record == FINISH:
                break
            times.append(metric_record.time)
            for metric_type in MetricType:
                image_scores[metric_type].append(metric_record.metrics[metric_type])
        except ValueError as e:
            print(f"error in {__name__}.{graph_metrics.__name__}: {e}")
            break

    # start plotting
    SMALL_SIZE = 250

    plt.rc("font", size=SMALL_SIZE)  # controls default text sizes
    plt.rc("axes", titlesize=SMALL_SIZE)  # fontsize of the axes title
    plt.rc("axes", labelsize=SMALL_SIZE)  # fontsize of the x and y labels
    plt.rc("xtick", labelsize=SMALL_SIZE)  # fontsize of the tick labels
    plt.rc("ytick", labelsize=SMALL_SIZE)  # fontsize of the tick labels

    fig, ax = plt.subplots(len(MetricType), 1, figsize=(200, 100))
    fig.tight_layout(pad=5.0)

    for row_idx, metric_type in enumerate(MetricType):
        ax[row_idx].grid(True, color='r')
        ax[row_idx].plot_date(times, image_scores[metric_type], ms=30)
        ax[row_idx].set_title("Timeline of Frame Score")
        ax[row_idx].set_xlabel("Unix Time")
        ax[row_idx].set_ylabel(f"{metric_type.value} Score")

    image_filename = (
        graph_dir + "/" + "frame_timeline.png"
    )
    fig.savefig(image_filename)
    print("finished " + graph_metrics.__name__)

# def run_video_processes(graph_dir: str):
#     packet_queue = multiprocessing.Queue()
#     metrics_queue = multiprocessing.Queue()

#     process_capture = multiprocessing.Process(target=capture_images, args=(30, packet_queue,))
#     process_analysis = multiprocessing.Process(target=compute_metrics, args=(packet_queue, metrics_queue,))
#     process_graph = multiprocessing.Process(target=graph_metrics, args=(graph_dir, metrics_queue,))

#     process_capture.start()
#     process_analysis.start()
#     process_graph.start()

#     process_capture.join()
#     process_analysis.join()
#     process_graph.join()
