
from typing import Dict

class AVC3dExtension:
    def __init__(self, view_idx: int, depth_flag: int, non_idr_flag: int, temporal_id: int, anchor_pic_flag: int, inter_view_flag: int):
        self.view_idx: int = view_idx
        self.depth_flag: int = depth_flag
        self.non_idr_flag: int = non_idr_flag
        self.temporal_id: int = temporal_id
        self.anchor_pic_flag: int = anchor_pic_flag
        self.inter_view_flag: int = inter_view_flag
    
    def __str__(self) -> str:
        return str(vars(self))
    
    def get_important_attributes(self) -> Dict[str, int]:
        return {"view_idx": self.view_idx, "depth_flag": self.depth_flag, "non_idr_flag": self.non_idr_flag}