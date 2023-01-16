import argparse
import json
import os
from multiprocessing import Process
from pathlib import Path
from typing import Dict, Tuple

import app.capture.capture_data as capture
import app.analysis.graphs.image_metrics as graph_frame
import app.analysis.graphs.network_metrics as graph_network

def open_config() -> Tuple[Dict,Dict,str]:
    """
    Returns network config dictionary, frame config dictionary, output graph filepath
    """
    config_dir = Path(__file__).parent
    config_file = config_dir / "config.json"

    with config_file.open() as f:
        args = json.load(f)
        args_tcpdump = args["network_capture_config"]
        args_frames = args["frame_capture_config"]

        frame_dir: str = args_frames["output_frame_dir"]
        graph_dir = frame_dir + "_graphs"
        if not os.path.exists(graph_dir):
            os.makedirs(graph_dir)
    
    return args_tcpdump, args_frames, graph_dir

def create_graphs():
    args_tcpdump, args_frames, graph_dir = open_config()
    graph_network.create_graphs(args_tcpdump, graph_dir)
    graph_frame.create_graphs(args_frames, graph_dir)

def run_app():
    parser = argparse.ArgumentParser()
    parser.add_argument('-nc', '--NoCapture', help='default capture else no capture data',required=False)
    parser.add_argument('-ng', '--NoGraph',  help='default create graphs else no graph creation', required=False)
    args = parser.parse_args()

    if args.NoCapture == None:
        print("capturing data")
        capture.run_procceses()
    if args.NoGraph == None:
        print("graph creation")
        create_graphs()

if __name__ == "__main__":
    run_app()