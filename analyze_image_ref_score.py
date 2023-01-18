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
from app.analysis.frame.frame import parse_frames_from_filenames
from app.analysis.metrics.image_score import ImageMetrics, MetricType
from app.analysis.metrics.piqe import piqe

if __name__ == "__main__":
    config_dir = Path(__file__).parent
    config_file = config_dir / "config.json"

    with config_file.open() as f:
        args = json.load(f)
        args_tcpdump = args["network_capture_config"]
        parser.check_process_inputs(
            args_tcpdump, {"output_file": str, "duration_seconds": int}
        )

        args_frames = args["frame_capture_config"]
        parser.check_process_inputs(
            args_frames, {"output_frame_dir": str}
        )

        good_image_score_high = "/Users/carolinejin/Documents/meng_project/data/bad_good/2023.01.08.14.18.15.467.jpg"
        bad_image_score_low = "/Users/carolinejin/Documents/meng_project/data/bad_good/2023.01.08.14.18.05.144.jpg"
        bad_image_blurry = "/Users/carolinejin/Documents/meng_project/data/good_bad/2023.01.08.14.12.19.342.jpg"
        good_image_2 = "/Users/carolinejin/Documents/meng_project/data/good_bad/2023.01.08.14.12.15.717.jpg"

        image_metric = ImageMetrics()

        good_res = piqe(cv2.imread(good_image_score_high))
        bad_res = piqe(cv2.imread(bad_image_score_low))
        bad_blurry_res = piqe(cv2.imread(bad_image_blurry))
        good_res2 = piqe(cv2.imread(good_image_2))

        print(good_res[0], image_metric.laplacian_blur(cv2.imread(good_image_score_high)))
        print(bad_res[0], image_metric.laplacian_blur(cv2.imread(bad_image_score_low)))
        print(bad_blurry_res[0], image_metric.laplacian_blur(cv2.imread(bad_image_blurry)))
        print(good_res2[0], image_metric.laplacian_blur(cv2.imread(good_image_2)))

        image_dir = "/Users/carolinejin/Documents/meng_project/data/piqe_not_work"
        if not os.path.exists(image_dir):
            os.makedirs(image_dir)
        
        cv2.imwrite(image_dir + "/good_res_orig.jpg", cv2.imread(good_image_score_high))
        cv2.imwrite(image_dir + "/bad_res_orig.jpg", cv2.imread(bad_image_score_low))
        cv2.imwrite(image_dir + "/bad_blurry_res_orig.jpg", cv2.imread(bad_image_blurry))
        cv2.imwrite(image_dir + "/good_res_2_orig.jpg", cv2.imread(good_image_2))

        cv2.imwrite(image_dir + "/good_res_noticeable_artifact.jpg", (good_res[1] > 0) * 255)
        cv2.imwrite(image_dir + "/bad_res_noticeable_artifact.jpg", (bad_res[1] > 0)*255)
        cv2.imwrite(image_dir + "/bad_blurry_res_noticeable_artifact.jpg", (bad_blurry_res[1] > 0) * 255)
        cv2.imwrite(image_dir + "/good_res_2_noticeable_artifact.jpg", good_res2[1] * 255)

        cv2.imwrite(image_dir + "/good_res_noise_mask.jpg", (good_res[2]>0) * 255)
        cv2.imwrite(image_dir + "/bad_res_noise_mask.jpg", bad_res[2] * 255)
        cv2.imwrite(image_dir + "/bad_blurry_res_noise_mask.jpg", bad_blurry_res[2] * 255)
        cv2.imwrite(image_dir + "/good_res_2_noise_madk.jpg", good_res2[2] * 255)