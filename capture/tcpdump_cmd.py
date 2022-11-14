import subprocess
import os
import json
import time

from datetime import timedelta
from pathlib import Path

from utilities.parser import *

ZOOM_COUNT = 3 # number of times zoom appears on ps -A output when a meeting is going on
CHECK_COUNT = 3 # number of times to make sure there exists a zoom meeting and is in the foreground of screen
FULL_SCREEN_SIZE_ERROR = 1 # max error difference between the actual size dimensions

def run_tcp(path_name: str, timeout_sec = -1) -> subprocess.Popen:
    """
    Run tcp command with timeout given by timeout_sec
    Default timeout_sec = -1 meaning there is timeout. Otherwise, users
    must input timeout_sec > 0 (int). 

    Runs tcpdump with sudo privileges. User must input sudo password in terminal

    sudo tcpdump -n udp -G 5 -W 1 -w sample.pcap
    https://stackoverflow.com/a/40330559
    5 = number of seconds you want to rotate
    """
    return subprocess.Popen(['sudo', 'tcpdump', '-n', 'udp', '-G', str(timeout_sec), '-W', '1', '-w', path_name]) #, stdin=subprocess.PIPE, stdout=subprocess.PIPE) #.communicate(bytes(getpass.getpass('Password:\n'), 'utf-8'))


def capture_screen(device_index: int, timeout_sec: int, dir_frames: str) -> subprocess.Popen:
    """
    Runs ffmpeg command and screen captures the frames.
    Saves the timestamp as part of the filename
    """
    duration = str(timedelta(seconds=timeout_sec))
    if not os.path.exists(dir_frames):
        os.makedirs(dir_frames)
    else:
        if os.path.isfile(dir_frames):
            raise OSError(f"{dir_frames} is a file not a directory")
        # cleans up previous runs of screen capture
        for f in os.listdir(dir_frames):
            os.remove(os.path.join(dir_frames, f))

    filename = dir_frames+"/output%t.jpg"
    return subprocess.Popen(['ffmpeg', '-r', '30', '-f', 'avfoundation', '-i', str(device_index), '-t', duration, "-f", "image2", filename])

def is_zoom_meeting_active() -> bool:
    """
    Return whether a zoom meeting is going on
    """

    ps_out = subprocess.check_output(["ps", "-A"]).splitlines()
    curr_zoom_count = 0

    for line in ps_out:
        if b"zoom" in line:
            curr_zoom_count += 1
    
    return curr_zoom_count == ZOOM_COUNT

def is_zoom_fullscreen() -> bool:
    """
    Return whether zoom application is in the fullscreen and in the foreground of application
    """
    swift_file_path: str = os.path.join(os.path.dirname(__file__), 'is_zoom_ready.swift')
    swift_out = subprocess.check_output(["swift", swift_file_path]).splitlines()

    # check the output in is_zoom_ready to see what the output format is
    # false -> "false"
    # true
    if(len(swift_out) <= 1):
        return False
    
    screen_width: float = float(parse_swift_output(swift_out[0]))
    screen_height: float = float(parse_swift_output(swift_out[1]))
    x: float = float(parse_swift_output(swift_out[2]))
    y: float = float(parse_swift_output(swift_out[3]))

    width: float = float(parse_swift_output(swift_out[4]))
    height: float = float(parse_swift_output(swift_out[5]))

    return abs(x + width - screen_width) <= FULL_SCREEN_SIZE_ERROR and abs(y + height - screen_height) <= FULL_SCREEN_SIZE_ERROR

def can_collect_data() -> None:
    """
    Returns whether we can start collecting data
    """
    curr_count = 0
    while curr_count < CHECK_COUNT:
        if(is_zoom_meeting_active() and is_zoom_fullscreen()):
            curr_count += 1
            time.sleep(2)

def run_procceses():
    """
    Runs the processes with the given config.json file
    """
    # check to make sure a zoom meeting is active and in front of the screen
    can_collect_data()

    # start capturing data
    config_dir = Path(__file__).parent.parent
    config_file = config_dir / "config.json"
    with config_file.open() as f:
        args = json.load(f)

        # tcpdump
        args_tcpdump = args["network_capture_config"]
        check_process_inputs(args_tcpdump, {"output_file": str, "duration_seconds": int})

        # screen capture
        args_ffmpeg = args["frame_capture_config"]
        check_process_inputs(args_ffmpeg, {"device_index": int, "duration_seconds": int, "output_frame_dir": str})

        procs = [run_tcp(args_tcpdump["output_file"], args_tcpdump["duration_seconds"]), 
                capture_screen(args_ffmpeg["device_index"], args_ffmpeg["duration_seconds"], args_ffmpeg["output_frame_dir"])]
        for p in procs:
            p.wait()

if __name__ == "__main__":
    run_procceses()
    
    
