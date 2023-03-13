
from datetime import datetime
import Quartz
import time

from PIL import Image

from app2.network.parsing.packet_time import PacketTime
from app2.video.video_run import get_zoom_window_id, capture_image

if __name__ == "__main__":
    # check why microsecond of 0 is not being parsed well

    packet_time = PacketTime(500)
    packet_time.__microseconds = 0
    print(packet_time)

    packet_str = str(packet_time)
    datetime.strptime(packet_str, '%Y-%m-%d %H:%M:%S.%f')

    # check to see what window sharescreen is at
    count = 0
    while True:
        window_num = get_zoom_window_id()
        print(window_num)
        image: Image.Image = capture_image(window_num)
        image.save(f"debug_capture-{count}.png")
        time.sleep(5)
        count += 1