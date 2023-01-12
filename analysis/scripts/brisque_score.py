import json
import PIL.Image
import os
from brisque import BRISQUE
from matplotlib import image as plt_img
from pathlib import Path

from utilities import parser

if __name__ == "__main__":
    config_dir = Path(__file__).parent.parent.parent
    config_file = config_dir / "config.json"

    extension_header_vals = set()

    with config_file.open() as f:
        args = json.load(f)
        args_frames = args["frame_capture_config"]
        parser.check_process_inputs(
            args_frames, {"output_frame_dir": str}
        )

        num_files = 10
        counter = 0
        frame_dir = args_frames["output_frame_dir"]
        brisque_scorer = BRISQUE()

        min_val, max_val, sum_val, count_val = float('inf'), -1, 0, 0

        min_filename, max_filename = "", ""
        for file in os.listdir(args_frames["output_frame_dir"]):
            img = plt_img.imread(frame_dir + "/" + file)

            curr_score = brisque_scorer.score(img)
            min_val = min(curr_score, min_val)
            max_val = max(curr_score, max_val)
            sum_val += curr_score
            count_val += 1
        
            mean_val = sum_val / count_val

            if curr_score == max_val:
                max_filename = frame_dir + "/" + file
            if curr_score == min_val:
                min_filename = frame_dir + "/" + file
            
            filename = frame_dir + "/" + file
            print(f"filename = {filename} curr score = {curr_score}")
            # if count_val % 100 == 0:
            #     print(f"Count = {count_val}")
            #     print(f"file {max_filename} bad score = {max_val}, file {min_filename} good score = {min_val}")
        
        print("FINAL----")
        print(f"file {max_filename} bad score = {max_val}, file {min_filename} good score = {min_val}")
            # print(f"min = {min_val}, max = {max_val}, mean = {mean_val}")
        
