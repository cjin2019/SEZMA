from dataclasses import dataclass
from datetime import datetime
from typing import Dict

from app.video.metrics.image_score import MetricType

@dataclass
class VideoMetrics:
    time: datetime
    metrics: Dict[MetricType, float]
