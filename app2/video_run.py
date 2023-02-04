# screen capture -> compute metrics -> save 
import csv
import datetime
import multiprocessing
import numpy as np
import Quartz
import Quartz.CoreGraphics as cg
import time

from PIL import Image

from app2.video.metrics.image_score import MetricType, get_no_ref_score

# close until no more to capture
FINISH = 1

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
    

def capture_images(frame_rate: float, data_queue: multiprocessing.Queue):
    """
    Params:
    frame_rate: frames per second

    Assume that the video call has already started
    """
    window_num: int = get_zoom_window_id()
    time_between_frame: float = 1/frame_rate
    
    capture_start_time = datetime.datetime.now()
    while (datetime.datetime.now() - capture_start_time).total_seconds() <= 5: # for now run for only five seconds
        image_start_time = datetime.datetime.now()
        raw_data: np.ndarray = capture_image(window_num)
        data_queue.put((image_start_time, raw_data), block=True)
        image_finish_time = datetime.datetime.now()

        diff = (image_finish_time - image_start_time).total_seconds()
        if(diff < time_between_frame):
            time.sleep(time_between_frame - diff)
    data_queue.put(FINISH, block=True)
    data_queue.close()
    print("finished capture")

def compute_metrics(data_queue: multiprocessing.Queue):
    with open('test.csv', 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Time'] + [metric.value for metric in MetricType])

        while True:
            try:
                res = data_queue.get(block=True)
                if type(res) == int and res == FINISH:
                    break
                image_capture_time, image_data = res
                writer.writerow([image_capture_time] + [get_no_ref_score(image_data, metric) for metric in MetricType])
            except ValueError:
                print("error occurred")
                break
    print("finished analysis")

def run_processes():
    data_queue = multiprocessing.Queue()

    process_capture = multiprocessing.Process(target=capture_images, args=(30, data_queue,))
    process_capture.start()

    process_analysis = multiprocessing.Process(target=compute_metrics, args=(data_queue,))
    process_analysis.start()

    process_capture.join()
    process_analysis.join()



if __name__ == "__main__":
    run_processes()