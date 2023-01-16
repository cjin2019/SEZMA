import cv2
import numpy as np
import os

from brisque import BRISQUE
from enum import Enum

from app.analysis.frame.frame import Frame
from app.analysis.metrics.niqe import niqe
from app.analysis.metrics.piqe import piqe
from app.utilities import parser

class MetricType(Enum):
    # BRISQUE = "BRISQUE"
    PIQE = "PIQE"
    NIQE = "NIQE"
    LAPLACIAN = "LAPLACIAN"

class ImageMetrics:
    def __init__(self):
        self.BRISQUE = BRISQUE()
    def laplacian_blur(self, img, save_filename: str = None) -> float:
        """
        img: NDArray of shape (W, H) or (W, H, C) where C represents RGB
        """
        gray_img = img
        if len(img.shape) == 3:
            gray_img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        gray_img = gray_img.astype(np.float64)
        
        laplacian = cv2.Laplacian(gray_img, cv2.CV_64F)
        if save_filename != None:
            cv2.imwrite(save_filename, laplacian)

        return np.var(laplacian)

    def get_no_ref_score(self, im, mode: "MetricType") -> float:
        score = -1
        if mode == MetricType.PIQE:
            score, _, _, _ = piqe(im)
        elif mode == MetricType.NIQE:
            score = niqe(im)
        # elif mode == MetricType.BRISQUE:
        #     score = self.BRISQUE.score(im)
        else:
            return self.laplacian_blur(im)
        
        return score
