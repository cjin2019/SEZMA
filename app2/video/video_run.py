# screen capture -> compute metrics -> save 
import csv
import multiprocessing as mp
import numpy as np
import os
import queue
import time
import Quartz
import Quartz.CoreGraphics as cg

from collections import defaultdict
from datetime import datetime
from matplotlib import pyplot as plt
from typing import Dict, List
from PIL import Image

from app2.common.constants import SpecialQueueValues, TIME_FORMAT
from app2.video.metrics.image_score import MetricType, get_no_ref_score
from app2.video.video_metrics import VideoMetrics

def get_zoom_window_id() -> int:
    """
    Returns the window ID of Zoom Meeting. Otherwise, -1 if there is no such meeting
    """
    windows = Quartz.CGWindowListCopyWindowInfo(Quartz.kCGWindowListExcludeDesktopElements | Quartz.kCGWindowListOptionAll, Quartz.kCGNullWindowID)
    for win in windows:
        if win[Quartz.kCGWindowOwnerName] == 'zoom.us' and win.get(Quartz.kCGWindowName, '') == 'Zoom Meeting':
            return int(win.get(Quartz.kCGWindowNumber, ''))
    return -1

def check_zoom_window_up(log_queue, zoom_meeting_on: mp.Event) -> None:
    """
    Param: log_queue is mp.Queue that contains a string with log information or SpecialQueueValue
    Param: zoom_meeting_on_check determines whether Zoom Meeting is still in progress on the user's laptop
    """
    log_queue.put(f"started {__name__}.{check_zoom_window_up.__name__}")
    has_turned_on = False
    not_on_count = 0
    max_not_on_count = 3

    while True:
        if get_zoom_window_id() != -1: # zoom window up
            if not has_turned_on: # hasn't turned on yet
                has_turned_on = True
                zoom_meeting_on.set()
            else: # already turned on --> set to 0
                not_on_count = 0 # reset to 0
        else: # zoom window not up
            if has_turned_on: # already turned on
                not_on_count += 1 # increment each time it's off
                if not_on_count >= max_not_on_count:
                    zoom_meeting_on.clear()
                    log_queue.put(f"in {__name__}.{check_zoom_window_up.__name__}, Zoom window is closed")
                    break
        time.sleep(3)
    log_queue.put(f"finished {__name__}.{check_zoom_window_up.__name__}")

def capture_image(window_num) -> Image.Image:
    """
    Param: window_num > 0
    Gets the raw image data of the window given window_num

    https://stackoverflow.com/a/53607100

    Returns PIL Image of the window with window_num
    """
    cg_image = Quartz.CGWindowListCreateImage(Quartz.CGRectNull, Quartz.kCGWindowListOptionIncludingWindow, window_num, Quartz.kCGWindowImageBoundsIgnoreFraming)
    bpr = cg.CGImageGetBytesPerRow(cg_image)
    width = cg.CGImageGetWidth(cg_image)
    height = cg.CGImageGetHeight(cg_image)

    cg_dataprovider = cg.CGImageGetDataProvider(cg_image)
    cg_data = cg.CGDataProviderCopyData(cg_dataprovider)
    return Image.frombuffer("RGBA", (width, height), cg_data, "raw", "BGRA", bpr, 1)

def capture_images(frame_rate: float, data_queue, log_queue, zoom_meeting_on_check: mp.Event) -> None:
    """
    Params: frame_rate: frames per second
    Param: data_queue is mp.Queue that contains the raw numpy array of video frames and has maxsize set to a certain value
    Param: log_queue is mp.Queue that contains a string with log information or SpecialQueueValue
    Param: zoom_meeting_on_check determines whether Zoom Meeting is still in progress on the user's laptop
    """
    zoom_meeting_on_check.wait()
    log_queue.put(f"started {__name__}.{capture_images.__name__}")
    window_num: int = get_zoom_window_id()
    
    prev_check_time = datetime.now()
    time_between_frame: float = 1/frame_rate
    # do binary search if really necessary
    
    while zoom_meeting_on_check.is_set(): 
        try:
            image_start_time = datetime.now()
            raw_data: Image.Image = capture_image(window_num)
            data_queue.put((image_start_time, raw_data), block = False)
            image_finish_time = datetime.now()

            diff = (image_finish_time - image_start_time).total_seconds()
            if(diff < time_between_frame):
                time.sleep(time_between_frame - diff)

        except queue.Full as e:
            # update the frame rate to be lower (ie. halve it) every 10 seconds
            if (datetime.now() - prev_check_time).total_seconds() > 10: 
                prev_check_time = datetime.now()
                time_between_frame = 2 * time_between_frame
                log_queue.put(f"in {__name__}.{capture_images.__name__}, decreased frame rate to {time_between_frame}s between each frame capture")
        except Exception as e:
            if get_zoom_window_id() == -1:
                # faster than checking if zoom_meeting_on_check is updated
                log_queue.put(f"in {__name__}.{capture_images.__name__}, zoom window does not exist")
                break
            log_queue.put(f"exception in {__name__}.{capture_image.__name__}: {type(e)}, {e}")
        

    log_queue.put(f"finished {__name__}.{capture_images.__name__}")

def compute_metrics(data_queue, result_queue, log_queue, zoom_meeting_on_check: mp.Event) -> None:
    """
    Param: data_queue is mp.Queue that contains the raw numpy array of video frames
    Param: result_queue is mp.Queue that contains VideoMetric results
    Param: log_queue is mp.Queue that contains a string with log information or SpecialQueueValue
    Param: zoom_meeting_on_check determines whether Zoom Meeting is still in progress on the user's laptop
    """
    zoom_meeting_on_check.wait()
    log_queue.put(f"started {__name__}.{compute_metrics.__name__}")

    # result_queue.put(["time"] + [metric_type.value for metric_type in MetricType])
    while True:
        try:
            res = data_queue.get(timeout=5) 
            
            image_capture_time, image_data = res
            image_data = np.asarray(image_data)
            metrics= {metric_type: get_no_ref_score(image_data, metric_type) for metric_type in MetricType}

            result_queue.put(VideoMetrics(
                time=image_capture_time,
                metrics=metrics,
            ))
        except Exception as e:
            if zoom_meeting_on_check.is_set():
                log_queue.put(f"error in {__name__}.{compute_metrics.__name__}: {e}, {type(e)}")
            else:
                log_queue.put(f"zoom meeting not set anymore, break: {__name__}.{compute_metrics.__name__}: {e}, {type(e)}")
                break

    log_queue.put(f"finished {__name__}.{compute_metrics.__name__}")

def write_metrics(metric_queue, filename: str, log_queue, zoom_meeting_on_check: mp.Event):
    """
    Param: metric_queue is mp.Queue that contains VideoMetric results
    Param: filename is the csv file to to write the metrics into
    Param: log_queue is mp.Queue that contains a string with log information or SpecialQueueValue
    Param: zoom_meeting_on_check determines whether Zoom Meeting is still in progress on the user's laptop
    """
    zoom_meeting_on_check.wait()
    
    log_queue.put(f"started {__name__}.{write_metrics.__name__}")
    started = False
    count_images: int = 0
    num_image_process_print: int = 100


    with open(filename, mode="w") as csv_file:
        csv_writer = csv.writer(csv_file)
        while True:
            try:
                res: "VideoMetrics" = metric_queue.get(timeout=5)
                if not started:
                    csv_writer.writerow(["time"] + [metric_type.value for metric_type in MetricType])
                    started = True
                csv_writer.writerow([res.time.strftime(TIME_FORMAT)] + [res.metrics[metric_type] for metric_type in MetricType])

                count_images += 1
                if count_images % num_image_process_print == 0:
                    log_queue.put(f"processed {count_images} images")
            except queue.Empty as e:
                if not zoom_meeting_on_check.is_set():
                    break
            except ValueError as e:
                log_queue.put(f"error in {__name__}.{write_metrics.__name__}: {e}")
                break
    log_queue.put(f"finished {__name__}.{write_metrics.__name__}")

def graph_metrics(graph_dir: str, csv_filename: str, log_queue) -> None:
    """
    Param: graph_dir is the directory where to store the graph outputs
    Param: csv_filename is the name of the file to read the metrics from
    Param: log_queue is mp.Queue that contains a string with log information or SpecialQueueValue
    """
    # get the time and size
    times: List[datetime] = []
    image_scores: Dict[MetricType, List[float]] = {}
    header = []
    
    log_queue.put(f"started {__name__}.{graph_metrics.__name__}")
    with open(csv_filename) as csvfile:
        csvreader = csv.reader(csvfile)
        for row in csvreader:
            if row[0] == "time":
                header = row
                image_scores = {MetricType(metric_str_val): [] for metric_str_val in header[1:]}                                                       
                continue
            times.append(datetime.strptime(row[0], TIME_FORMAT))
            for idx in range(1, len(row)):
                image_scores[MetricType(header[idx])].append(float(row[idx]))
    
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
    log_queue.put(f"finished {__name__}.{graph_metrics.__name__}")
    log_queue.put(SpecialQueueValues.FINISH)


#### OLD CODE

# def capture_image(window_num: int) -> Image.Image:
#     """
#     Param: window_num > 0
#     Gets the raw image data of the window given window_num

#     https://stackoverflow.com/a/53607100

#     Returns PIL Image of the window with window_num
#     """
#     cg_image = Quartz.CGWindowListCreateImage(Quartz.CGRectNull, Quartz.kCGWindowListOptionIncludingWindow, window_num, Quartz.kCGWindowImageBoundsIgnoreFraming)
#     bpr = cg.CGImageGetBytesPerRow(cg_image)
#     width = cg.CGImageGetWidth(cg_image)
#     height = cg.CGImageGetHeight(cg_image)

#     cg_dataprovider = cg.CGImageGetDataProvider(cg_image)
#     cg_data = cg.CGDataProviderCopyData(cg_dataprovider)
#     # np_raw_data = np.frombuffer(cg_data, dtype=np.uint8)

#     # np_data = np.lib.stride_tricks.as_strided(np_raw_data,
#     #                                         shape=(height, width, 3),
#     #                                         strides=(bpr, 4, 1),
#     #                                         writeable=False)
#     pil_image = Image.frombuffer("RGBA", (width, height), cg_data, "raw", "BGRA", bpr, 1)
#     # pil_image.save(f"{window_num}.png")
#     return pil_image

# def capture_images(frame_rate: float, data_queue, zoom_meeting_on_check: mp.Event) -> None:
#     """
#     Params: frame_rate: frames per second
#     Param: data_queue is mp.Manager.Queue containing np.arrays of images

#     Assume that the video call has already started
#     """
#     zoom_meeting_on_check.wait()
#     print(f"started {__name__}.{capture_image.__name__}")
#     window_num: int = get_zoom_window_id()
#     time_between_frame: float = 1/frame_rate
    
#     while zoom_meeting_on_check.is_set(): 
#         try:
#             image_start_time = datetime.now()
#             raw_data: Image.Image = capture_image(window_num)
#             data_queue.put((image_start_time, raw_data))
#             image_finish_time = datetime.now()

#             diff = (image_finish_time - image_start_time).total_seconds()
#             if(diff < time_between_frame):
#                 time.sleep(time_between_frame - diff)
#         except Exception as e:
#             print(f"exception in capture_images {type(e)}")
        

#     print(f"finished {__name__}.{capture_image.__name__}")

# def capture_images(frame_rate: float, data_queue, zoom_meeting_on_check: mp.Event) -> None:
#     """
#     Params: frame_rate: frames per second
#     Param: data_queue is mp.Manager.Queue containing np.arrays of images

#     Assume that the video call has already started
#     """
#     zoom_meeting_on_check.wait()
#     print(f"started {__name__}.{capture_image.__name__}")
#     window_num: int = get_zoom_window_id()
#     time_between_frame: float = 1/frame_rate
    
#     while zoom_meeting_on_check.is_set(): 
#         try:
#             image_start_time = datetime.now()
#             raw_data: Image.Image = capture_image(window_num)
#             data_queue.put((image_start_time, raw_data))
#             image_finish_time = datetime.now()

#             diff = (image_finish_time - image_start_time).total_seconds()
#             if(diff < time_between_frame):
#                 time.sleep(time_between_frame - diff)
#         except Exception as e:
#             print(f"exception in capture_images {type(e)}")
        

#     print(f"finished {__name__}.{capture_image.__name__}")

# def run2() -> None:
#     filename = "video_test.csv"
#     duration = 5
#     frame_rate = 30
#     data_queue = mp.Queue()

#     capture_process = mp.Process(target=capture_images, args=(frame_rate, duration, data_queue,))
#     compute_process = mp.Process(target=compute_metrics2, args=(data_queue, filename,))

#     capture_process.start()
#     compute_process.start()

#     capture_process.join()
#     compute_process.join()

# def write_metrics(metric_queue, filename: str, zoom_meeting_on_check: mp.Event):

#     zoom_meeting_on_check.wait()
#     started = False
#     count_images: int = 0
#     num_image_process_print: int = 100

#     with open(filename, mode="w") as csv_file:
#         csv_writer = csv.writer(csv_file)
#         while True:
#             try:
#                 res: "VideoMetrics" = metric_queue.get(timeout=5)
#                 if not started:
#                     csv_writer.writerow(["time"] + [metric_type.value for metric_type in MetricType])
#                     started = True
#                 csv_writer.writerow([res.time] + [res.metrics[metric_type] for metric_type in MetricType])

#                 count_images += 1
#                 if count_images % num_image_process_print == 0:
#                     print(f"processed {count_images} images")
#             except queue.Empty as e:
#                 if not zoom_meeting_on_check.is_set():
#                     break
#             except ValueError as e:
#                 print(f"error in {__name__}.{write_metrics.__name__}: {e}")
#                 break

# def compute_metrics(data_queue, result_queue):
#     """
#     Param: data_queue is mp.Manager.Queue containing the raw numpy array of video frames
#     Param: result_queue is mp.Manager.Queue containing the VideoMetrics record
#     """
#     print(f"started {__name__}.{compute_metrics.__name__}")
#     start_time = datetime.now()
#     count_images: int = 0
#     num_image_process_print: int = 100
#     row = []

#     while True:
#         try:
#             res = data_queue.get(timeout=2) # assume video frames are captured faster than 1 fps
#             # if type(res) == int and res == FINISH:
#             #     break
#             image_capture_time, image_data = res
#             image_data = np.asarray(image_data)
#             # image_data = prepare_for_metric_computation(cg_image)
#             metric_record: "VideoMetrics" = VideoMetrics(
#                 time=image_capture_time,
#                 metrics= {metric_type: get_no_ref_score(image_data, metric_type) for metric_type in MetricType}
#             )
#             result_queue.put(metric_record)
#             count_images += 1
#             if count_images % num_image_process_print == 0:
#                 print(f"processed {count_images} images")
#         except queue.Empty as e:
#             print(f"finished computing metrics for a process {__name__}.{compute_metrics.__name__}: {e}")
#             break
#         except ValueError as e:
#             print(f"error in {__name__}.{compute_metrics.__name__}: {e}")
#             break
#     result_queue.put(FINISH)
#     end_time = datetime.now()
#     print(f"finished {__name__}.{compute_metrics.__name__} in {end_time - start_time}")

# def compute_metrics2(data_queue, filename: str, zoom_meeting_on_check: mp.Event):
#     """
#     Param: data_queue is mp.Manager.Queue containing the raw numpy array of video frames
#     Param: result_queue is mp.Manager.Queue containing the VideoMetrics record
#     """
#     zoom_meeting_on_check.wait()
#     print(f"started {__name__}.{compute_metrics.__name__}")
#     count_images: int = 0
#     num_image_process_print: int = 100
#     started = False

#     with open(filename, mode="w") as csv_file:
#         csv_writer = csv.writer(csv_file)
#         while True:
#             try:
#                 res = data_queue.get(timeout=5) 
                
#                 image_capture_time, image_data = res
#                 image_data = np.asarray(image_data)
#                 metrics= {metric_type: get_no_ref_score(image_data, metric_type) for metric_type in MetricType}
                
#                 if not started:
#                     csv_writer.writerow(["time"] + [metric_type.value for metric_type in MetricType])
#                     started = True
#                 csv_writer.writerow([image_capture_time] + [metrics[metric_type] for metric_type in MetricType])

#                 count_images += 1
#                 if count_images % num_image_process_print == 0:
#                     print(f"processed {count_images} images")
#             except queue.Empty as e:
#                 if not zoom_meeting_on_check.is_set():
#                     break
#             except ValueError as e:
#                 print(f"error in {__name__}.{compute_metrics.__name__}: {e}")
#                 break
#         print(f"finished {__name__}.{compute_metrics.__name__}")

# def compute_metrics3(data_queue, result_queue, zoom_meeting_on_check: mp.Event):
#     """
#     Param: data_queue is mp.Manager.Queue containing the raw numpy array of video frames
#     Param: result_queue is mp.Manager.Queue containing a row of 
#     """
#     zoom_meeting_on_check.wait()
#     print(f"started {__name__}.{compute_metrics.__name__}")

#     result_queue.put(["time"] + [metric_type.value for metric_type in MetricType])
#     while True:
#         try:
#             res = data_queue.get(timeout=5) 
            
#             image_capture_time, image_data = res
#             image_data = np.asarray(image_data)

#             # image_data = prepare_for_metric_computation(cg_image)
#             metric_record: "VideoMetrics" = VideoMetrics(
#                 time=image_capture_time,
#                 metrics= {metric_type: get_no_ref_score(image_data, metric_type) for metric_type in MetricType}
#             )
#             result_queue.put(metric_record)
#         except Exception as e:
#             if not zoom_meeting_on_check.is_set():
#                 break
#             print(f"error in {__name__}.{compute_metrics3.__name__}: {e}")

#     print(f"finished {__name__}.{compute_metrics3.__name__}")

# def graph_metrics(graph_dir: str, result_queue: mp.Queue, num_compute_processes) -> None:
#     # get the time and size
#     times: List[datetime] = []
#     image_scores: Dict[MetricType, List[float]] = defaultdict(list)
    
#     print(f"started {__name__}.{graph_metrics.__name__}")
#     while True:
#         try:
#             metric_record = result_queue.get()
#             if type(metric_record) == int and metric_record == FINISH:
#                 break
#             times.append(metric_record.time)
#             for metric_type in MetricType:
#                 image_scores[metric_type].append(metric_record.metrics[metric_type])
#         except ValueError as e:
#             print(f"error in {__name__}.{graph_metrics.__name__}: {e}")
#             break

#     # start plotting
#     SMALL_SIZE = 250

#     plt.rc("font", size=SMALL_SIZE)  # controls default text sizes
#     plt.rc("axes", titlesize=SMALL_SIZE)  # fontsize of the axes title
#     plt.rc("axes", labelsize=SMALL_SIZE)  # fontsize of the x and y labels
#     plt.rc("xtick", labelsize=SMALL_SIZE)  # fontsize of the tick labels
#     plt.rc("ytick", labelsize=SMALL_SIZE)  # fontsize of the tick labels

#     fig, ax = plt.subplots(len(MetricType), 1, figsize=(200, 100))
#     fig.tight_layout(pad=5.0)

#     for row_idx, metric_type in enumerate(MetricType):
#         ax[row_idx].grid(True, color='r')
#         ax[row_idx].plot_date(times, image_scores[metric_type], ms=30)
#         ax[row_idx].set_title("Timeline of Frame Score")
#         ax[row_idx].set_xlabel("Unix Time")
#         ax[row_idx].set_ylabel(f"{metric_type.value} Score")

#     image_filename = (
#         graph_dir + "/" + "frame_timeline.png"
#     )
#     fig.savefig(image_filename)
#     print("finished " + graph_metrics.__name__)