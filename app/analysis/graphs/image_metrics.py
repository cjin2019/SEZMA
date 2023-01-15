import csv
import cv2
import json
import PIL.Image
import os
import time

from datetime import datetime
from matplotlib import image as plt_img, pyplot as plt
from pathlib import Path
from typing import Dict, List

from app.utilities import parser
from app.analysis.frame.packet_to_frame import parse_frames_from_filenames
from app.analysis.metrics.image_score import ImageMetrics, MetricType

def create_graphs(args_frames: Dict, graph_dir) -> None:
    frame_dir = args_frames["output_frame_dir"]
    # brisque_scorer = BRISQUE()
    count = 0
    every_nth = 1
    scores: Dict["MetricType", List[float]] = {metric_type: [] for metric_type in MetricType}
    times: List[datetime] = []

    img_metrics = ImageMetrics()

    # open the file in the write mode
    image_score_data_file = open(graph_dir + "/image_score_data.csv", 'w')

    # create the csv writer
    writer = csv.writer(image_score_data_file)

    # write a row to the csv file
    writer.writerow(["filename", "time"] + [metric_type.value for metric_type in MetricType])

    start_time = time.time()
    for frame in parse_frames_from_filenames(frame_dir):
        if count % every_nth == 0:

            img_filename = frame_dir + "/" + frame.filename
            img = cv2.imread(img_filename)

            for metric_type in MetricType:
                scores[metric_type].append(img_metrics.get_no_ref_score(img, metric_type))
            times.append(frame.time.get_datetime())

            writer.writerow([img_filename, frame.time.get_datetime()] + [scores[metric_type][-1] for metric_type in MetricType])

            
        count += 1
        # print(f"{img_filename} pique {scores[MetricType.PIQE][-1]} laplacian {scores[MetricType.LAPLACIAN][-1]} brisque {scores[MetricType.BRISQUE][-1]} niqe {scores[MetricType.NIQE][-1]}")
        if count % 100 == 0:
            print(f"processed {count} images")
    
    end_time = time.time()
    print(f"Time Run: {end_time - start_time}")
    
    image_score_data_file.close()
    SMALL_SIZE = 100
    MEDIUM_SIZE = 200
    BIGGER_SIZE = 300

    plt.rc("font", size=SMALL_SIZE)  # controls default text sizes
    plt.rc("axes", titlesize=SMALL_SIZE)  # fontsize of the axes title
    plt.rc("axes", labelsize=MEDIUM_SIZE)  # fontsize of the x and y labels
    plt.rc("xtick", labelsize=SMALL_SIZE)  # fontsize of the tick labels
    plt.rc("ytick", labelsize=SMALL_SIZE)  # fontsize of the tick labels
    plt.rc("legend", fontsize=SMALL_SIZE)  # legend fontsize
    plt.rc("figure", titlesize=BIGGER_SIZE)  # fontsize of the figure title

    fig, ax = plt.subplots(len(MetricType), 1, figsize=(200, 100))
    fig.tight_layout(pad=5.0)

    for row_idx, metric_type in enumerate(MetricType):
        ax[row_idx].grid(True, color='r')
        ax[row_idx].plot_date(times, scores[metric_type], ms=30)
        ax[row_idx].set_title("Timeline of Frame Score")
        ax[row_idx].set_xlabel("Unix Time")
        ax[row_idx].set_ylabel(f"{metric_type.value} Score")

    image_filename = (
        graph_dir + "/" + "frame_timeline.png"
    )
    fig.savefig(image_filename)

# if __name__ == "__main__":
#     config_dir = Path(__file__).parent.parent.parent
#     config_file = config_dir / "config.json"

#     with config_file.open() as f:
#         args = json.load(f)
#         args_tcpdump = args["network_capture_config"]
#         parser.check_process_inputs(
#             args_tcpdump, {"output_file": str, "duration_seconds": int}
#         )

#         args_frames = args["frame_capture_config"]
#         parser.check_process_inputs(
#             args_frames, {"output_frame_dir": str}
#         )

#         frame_dir = args_frames["output_frame_dir"]
#         # brisque_scorer = BRISQUE()
#         count = 0
#         every_nth = 1
#         scores: Dict["MetricType", List[float]] = {metric_type: [] for metric_type in MetricType}
#         times: List[datetime] = []

#         img_metrics = ImageMetrics()

#         graph_dir = frame_dir + "_graphs"
#         if not os.path.exists(graph_dir):
#             os.makedirs(graph_dir)

#         # open the file in the write mode
#         image_score_data_file = open(graph_dir + "/image_score_data.csv", 'w')

#         # create the csv writer
#         writer = csv.writer(image_score_data_file)

#         # write a row to the csv file
#         writer.writerow(["filename", "time"] + [metric_type.value for metric_type in MetricType])

#         start_time = time.time()
#         for frame in parse_frames_from_filenames(frame_dir):
#             if count % every_nth == 0:

#                 img_filename = frame_dir + "/" + frame.filename
#                 img = cv2.imread(img_filename)

#                 for metric_type in MetricType:
#                     scores[metric_type].append(img_metrics.get_no_ref_score(img, metric_type))
#                 times.append(frame.time.get_datetime())

#                 writer.writerow([img_filename, frame.time.get_datetime()] + [scores[metric_type][-1] for metric_type in MetricType])

                
#             count += 1
#             print(f"{img_filename} pique {scores[MetricType.PIQE][-1]} laplacian {scores[MetricType.LAPLACIAN][-1]} brisque {scores[MetricType.BRISQUE][-1]} niqe {scores[MetricType.NIQE][-1]}")
#             # if count % 100 == 0:
#             #     print(count)
        
#         end_time = time.time()
#         print(end_time - start_time)
        
#         image_score_data_file.close()
#         SMALL_SIZE = 100
#         MEDIUM_SIZE = 200
#         BIGGER_SIZE = 300

#         plt.rc("font", size=SMALL_SIZE)  # controls default text sizes
#         plt.rc("axes", titlesize=SMALL_SIZE)  # fontsize of the axes title
#         plt.rc("axes", labelsize=MEDIUM_SIZE)  # fontsize of the x and y labels
#         plt.rc("xtick", labelsize=SMALL_SIZE)  # fontsize of the tick labels
#         plt.rc("ytick", labelsize=SMALL_SIZE)  # fontsize of the tick labels
#         plt.rc("legend", fontsize=SMALL_SIZE)  # legend fontsize
#         plt.rc("figure", titlesize=BIGGER_SIZE)  # fontsize of the figure title

#         fig, ax = plt.subplots(len(MetricType), 1, figsize=(200, 100))
#         fig.tight_layout(pad=5.0)

#         for row_idx, metric_type in enumerate(MetricType):
#             ax[row_idx].grid(True, color='r')
#             ax[row_idx].plot_date(times, scores[metric_type], ms=30)
#             ax[row_idx].set_title("Timeline of Frame Score")
#             ax[row_idx].set_xlabel("Unix Time")
#             ax[row_idx].set_ylabel(f"{metric_type.value} Score")

#         image_filename = (
#             graph_dir + "/" + "frame_timeline_2.png"
#         )
#         fig.savefig(image_filename)
        
