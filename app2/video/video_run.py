# screen capture -> compute metrics -> save 
import cv2
import datetime
import numpy as np
import Quartz
import Quartz.CoreGraphics as cg
import time

from PIL import Image

def captureImage():
    datetime.time()

    windows = Quartz.CGWindowListCopyWindowInfo(Quartz.kCGWindowListExcludeDesktopElements | Quartz.kCGWindowListOptionOnScreenOnly, Quartz.kCGNullWindowID)

    for win in windows:
        if win[Quartz.kCGWindowOwnerName] == 'zoom.us' and win.get(Quartz.kCGWindowName, '') == 'Zoom Meeting':
            window_num: int = int(win.get(Quartz.kCGWindowNumber, ''))
            cg_image = Quartz.CGWindowListCreateImage(Quartz.CGRectNull, Quartz.kCGWindowListOptionIncludingWindow, window_num, Quartz.kCGWindowImageBoundsIgnoreFraming)

            bpr = cg.CGImageGetBytesPerRow(cg_image)
            width = cg.CGImageGetWidth(cg_image)
            height = cg.CGImageGetHeight(cg_image)

            cg_dataprovider = cg.CGImageGetDataProvider(cg_image)
            cg_data = cg.CGDataProviderCopyData(cg_dataprovider)

            print(cg_data)

            np_raw_data = np.frombuffer(cg_data, dtype=np.uint8)

            np_data = np.lib.stride_tricks.as_strided(np_raw_data,
                                                    shape=(height, width, 3),
                                                    strides=(bpr, 4, 1),
                                                    writeable=False)
            
            cv2.imwrite('color_img.jpg', np_data)
            

    # return ['%s %s %s' % (win[Quartz.kCGWindowOwnerName], win.get(Quartz.kCGWindowName, ''), win.get(Quartz.kCGWindowNumber, '')) for win in windows]

print(captureImage())