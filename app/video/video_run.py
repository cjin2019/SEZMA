import csv
import multiprocessing as mp
import numpy as np
import os
import queue
import time
import traceback
import Quartz
import Quartz.CoreGraphics as cg

from collections import defaultdict
from datetime import datetime
from matplotlib import pyplot as plt
from typing import Dict, List
from PIL import Image

from app.common.constants import SpecialQueueValues, TIME_FORMAT
from app.video.metrics.image_score import MetricType, get_no_ref_score
from app.video.video_metrics import VideoMetrics

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
    if cg_image == None: # is fullscreen
        cg_image = Quartz.CGWindowListCreateImage(Quartz.CGRectNull, Quartz.kCGWindowListOptionIncludingWindow | Quartz.kCGWindowListOptionOnScreenAboveWindow, window_num, Quartz.kCGWindowImageBoundsIgnoreFraming)
        
    bpr = cg.CGImageGetBytesPerRow(cg_image)
    width = cg.CGImageGetWidth(cg_image)
    height = cg.CGImageGetHeight(cg_image)

    cg_dataprovider = cg.CGImageGetDataProvider(cg_image)
    cg_data = cg.CGDataProviderCopyData(cg_dataprovider)

    return Image.frombuffer("RGBA", (width, height), cg_data, "raw", "BGRA", bpr, 1)

def pipeline_run(filename: str, frame_rate: float, log_queue, zoom_meeting_on_check: mp.Event(), metric_list = [metric_type for metric_type in MetricType]) -> None:
    """
    Param: filename is the name of the file to write the video metrics into
    Param: frame_rate is the rate at which we capture the frames
    Param: log_queue is mp.Queue that contains a string with log information
    Param: zoom_meeting_on_check determines whether Zoom Meeting is still in progress on the user's laptop
    """
    zoom_meeting_on_check.wait()
    log_queue.put(f"started {__name__}.{pipeline_run.__name__}")
    window_num: int = get_zoom_window_id()
    
    time_between_frame: float = 1/frame_rate

    count_images: int = 0
    num_image_process_print: int = 100
    # do binary search if really necessary
    
    prev_array_data = np.array([0])
    with open(filename, mode="w") as csv_file:
        csv_writer = csv.writer(csv_file)
        csv_writer.writerow(["time"] + [metric_type.value for metric_type in metric_list] + ["is_stalled"])
        while zoom_meeting_on_check.is_set(): 
            try:
                image_start_time = datetime.now()
                # get image data ready to process
                raw_data: Image.Image = capture_image(window_num)
                image_data = np.asarray(raw_data)

                # compute metrics
                metrics= {metric_type: get_no_ref_score(image_data, metric_type) for metric_type in metric_list}

                # record metrics
                csv_writer.writerow([image_start_time.strftime(TIME_FORMAT)] + [metrics[metric_type] for metric_type in metric_list] + [1 if np.array_equal(prev_array_data, image_data) else 0])

                prev_array_data = image_data

                count_images += 1
                if count_images % num_image_process_print == 0:
                    log_queue.put(f"processed {count_images} images")
                image_finish_time = datetime.now()

                diff = (image_finish_time - image_start_time).total_seconds()
                if(diff < time_between_frame):
                    time.sleep(time_between_frame - diff)

            except Exception as e:
                if get_zoom_window_id() == -1:
                    # faster than checking if zoom_meeting_on_check is updated
                    log_queue.put(f"in {__name__}.{pipeline_run.__name__}, zoom window does not exist")
                    break
                log_queue.put(f"exception in {__name__}.{pipeline_run.__name__}: {type(e)}, {e}, {traceback.format_exc()}")
        
    log_queue.put(f"finished {__name__}.{pipeline_run.__name__}")