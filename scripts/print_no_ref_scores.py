# import cv2
# import json
# import PIL.Image
# import numpy as np
# import os

# from brisque import BRISQUE
# from matplotlib import image as plt_img, pyplot as plt
# from pathlib import Path
# from sewar.no_ref import d_lambda, d_s
# from skimage.color import rgb2gray
# from skimage.measure import blur_effect
# from typing import List

# from utilities import parser
# from analysis.frame.packet_to_frame import parse_frames_from_filenames, Frame

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

#         frame_dir: str = args_frames["output_frame_dir"]
#         brisque_scorer = BRISQUE()
#         count = 0
#         every_nth = 1
#         frames: List[Frame] = parse_frames_from_filenames(frame_dir)
#         imgs = [cv2.imread(frame_dir + "/" + frame.filename) for frame in frames]
#         # for frame in parse_frames_from_filenames(frame_dir):
#         #     if count % every_nth == 0:
#         #         img = plt_img.imread(frame_dir + "/" + frame.filename)
#         #         curr_score = brisque_scorer.score(img)
#         #         scores.append(curr_score)
#         #         times.append(frame.time.unix_time)
#         #         blurr_score = blur_effect(img)
#         #         print(f"filename {frame.filename}, brisque {curr_score} blurr_score {blurr_score} ")
#         #     count += 1
#         #     if count % 100 == 0:
#         #         print(count)
#         times = [frame.time.get_unix_time() for frame in frames]
#         num_frames = len(times)
#         for i in range(num_frames):
#             filename: str = frame_dir + "/" + frames[i].filename
#             print(f"filename {filename} blurr_score {cv2.Laplacian(imgs[i], cv2.CV_64F).var()}")


            
#         # SMALL_SIZE = 100
#         # MEDIUM_SIZE = 200
#         # BIGGER_SIZE = 300

#         # plt.rc("font", size=SMALL_SIZE)  # controls default text sizes
#         # plt.rc("axes", titlesize=SMALL_SIZE)  # fontsize of the axes title
#         # plt.rc("axes", labelsize=MEDIUM_SIZE)  # fontsize of the x and y labels
#         # plt.rc("xtick", labelsize=SMALL_SIZE)  # fontsize of the tick labels
#         # plt.rc("ytick", labelsize=SMALL_SIZE)  # fontsize of the tick labels
#         # plt.rc("legend", fontsize=SMALL_SIZE)  # legend fontsize
#         # plt.rc("figure", titlesize=BIGGER_SIZE)  # fontsize of the figure title

#         # fig, ax = plt.subplots(4, 1 figsize=(100, 80))

#         # ax.scatter(times, scores, s=800)
#         # ax.set_title("Timeline of Frame Score")
#         # ax.set_xlabel("Unix Time")
#         # ax.set_ylabel("BRISQUE Score")

#         # graph_dir = frame_dir + "_graphs"
#         # if not os.path.exists(graph_dir):
#         #     os.makedirs(graph_dir)

#         # image_filename = (
#         #     graph_dir + "/" + "frame_timeline.png"
#         # )
#         # fig.savefig(image_filename)
        
