from dataclasses import dataclass
from typing import Dict, Type


@dataclass
class AVC3dExtension:
    view_idx: int
    depth_flag: int
    non_idr_flag: int
    temporal_id: int
    anchor_pic_flag: int
    inter_view_flag: int

    def get_important_attributes(self) -> Dict[str, int]:
        return {
            "view_idx": self.view_idx,
            "depth_flag": self.depth_flag,
            "non_idr_flag": self.non_idr_flag,
        }

    @classmethod
    def create(cls: Type["AVC3dExtension"], data: bytes) -> "AVC3dExtension":
        avc_values: int = int.from_bytes(data[0:2], "big")

        view_idx: int = (avc_values >> 7) & 255
        depth_flag: int = (avc_values >> 6) & 1
        non_idr_flag: int = (avc_values >> 5) & 1
        temporal_id: int = (avc_values >> 2) & 7
        anchor_pic_flag: int = (avc_values >> 1) & 1
        inter_view_flag: int = avc_values & 1

        return AVC3dExtension(
            view_idx=view_idx,
            depth_flag=depth_flag,
            non_idr_flag=non_idr_flag,
            temporal_id=temporal_id,
            anchor_pic_flag=anchor_pic_flag,
            inter_view_flag=inter_view_flag,
        )
