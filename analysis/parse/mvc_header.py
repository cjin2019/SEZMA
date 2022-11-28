from dataclasses import dataclass
from typing import Type

@dataclass
class MVCExtension:
    non_idr_flag: int
    priority_id: int
    view_id: int
    temporal_id: int
    anchor_pic_flag: int
    inter_view_flag: int
    reserved_one_bit: int
    
    @classmethod
    def create(cls: Type["MVCExtension"], data: bytes) -> "MVCExtension":
        mvc_values: int = int.from_bytes(data[0: 3], 'big')

        non_idr_flag: int = (mvc_values >> 22) & 1
        priority_id: int = (mvc_values >> 16) & 63
        view_id: int = (mvc_values >> 6) & 1023
        temporal_id: int = (mvc_values >> 3) & 7
        anchor_pic_flag: int = (mvc_values >> 2) & 1
        inter_view_flag: int = (mvc_values >> 1) & 1
        reserved_one_bit: int = mvc_values & 1

        return MVCExtension(non_idr_flag, 
                            priority_id, 
                            view_id, 
                            temporal_id,
                            anchor_pic_flag,
                            inter_view_flag, 
                            reserved_one_bit
                        )
