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

from utilities import parser
from analysis.frame.packet_to_frame import parse_frames_from_filenames
from analysis.metrics.image_score import ImageMetrics, MetricType

if __name__ == "__main__":
    config_dir = Path(__file__).parent.parent.parent
    config_file = config_dir / "config.json"

    with config_file.open() as f:
        args = json.load(f)

        args_frames = args["frame_capture_config"]
        parser.check_process_inputs(
            args_frames, {"output_frame_dir": str}
        )

        frame_dir = args_frames["output_frame_dir"]
        # brisque_scorer = BRISQUE()
        count = 0
        every_nth = 1
        # scores: Dict["MetricType", List[float]] = {MetricType.BRISQUE: [], MetricType.NIQE: [], MetricType.PIQE: [], MetricType.LAPLACIAN: []}
        times: List[datetime] = []

        img_metrics = ImageMetrics()

        graph_dir = frame_dir + "_graphs"
        if not os.path.exists(graph_dir):
            os.makedirs(graph_dir)

        # open the file in the write mode
        image_score_data_file = open(graph_dir + "/image_score_data.csv", 'r')

        # create the csv reader
        reader = csv.reader(image_score_data_file)

        # write a row to the csv file
        col_names = next(reader)
        data = {col_name: [] for col_name in col_names}
        metric_type_values = [metric_type.value for metric_type in MetricType]
        for row in reader:
            for row_idx, col_name in enumerate(col_names):
                if col_name == "time":
                    # 2023-01-08 14:12:01.871000
                    if row[row_idx].find(".") == -1:
                        row[row_idx] += "." + "0" * 6
                    data[col_name].append(datetime.strptime(row[row_idx], "%Y-%m-%d %H:%M:%S.%f"))
                elif col_name in metric_type_values:
                    data[col_name].append(float(row[row_idx]))
                else:
                    data[col_name].append(row[row_idx])
        
        image_score_data_file.close()
        SMALL_SIZE = 150
        MEDIUM_SIZE = 200
        BIGGER_SIZE = 300

        plt.rc("font", size=SMALL_SIZE)  # controls default text sizes
        plt.rc("axes", titlesize=SMALL_SIZE)  # fontsize of the axes title
        plt.rc("axes", labelsize=MEDIUM_SIZE)  # fontsize of the x and y labels
        plt.rc("xtick", labelsize=SMALL_SIZE)  # fontsize of the tick labels
        plt.rc("ytick", labelsize=SMALL_SIZE)  # fontsize of the tick labels
        plt.rc("legend", fontsize=SMALL_SIZE)  # legend fontsize
        plt.rc("figure", titlesize=BIGGER_SIZE)  # fontsize of the figure title

        fig, ax = plt.subplots(4, 1, figsize=(200, 100))
        fig.tight_layout(pad=5.0)

        for row_idx, metric_type in enumerate(MetricType):
            ax[row_idx].grid(True, color='r')
            ax[row_idx].plot_date(data["time"], data[metric_type.value], ms=30)
            ax[row_idx].set_xlabel("Time")
            ax[row_idx].set_ylabel(f"{metric_type.value}")

        image_filename = (
            graph_dir + "/" + "frame_timeline.png"
        )
        fig.savefig(image_filename)
        
