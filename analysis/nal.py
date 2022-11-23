from dataclasses import dataclass
from typing import Union

from analysis.avc_3d_header import AVC3dExtension
from analysis.mvc_header import MVCExtension

@dataclass
class NALHeader:
    forbidden_zero_bit: int
    nal_ref_idc: int
    nal_unit_type: int

    @classmethod
    def get_header(cls, nal_data: bytes) -> "NALHeader":
        oct1: int = nal_data[0]

        forbidden_zero_bit: int = oct1 >> 7
        nal_ref_idc: int = (oct1 >> 5) & 3
        nal_unit_type: int = oct1 & 31

        return NALHeader(
                forbidden_zero_bit=forbidden_zero_bit,
                nal_ref_idc=nal_ref_idc,
                nal_unit_type=nal_unit_type
            )

class NAL:
    def __init__(self, nal_data: bytes) -> None:
        self.header = NALHeader.get_header(nal_data)
        self.payload = nal_data[1:]
    
    def get_extension_header(self) -> Union["AVC3dExtension", "MVCExtension"]:
        avc_flag: bool = self.payload[0] >> 7 == 1
        if not avc_flag:
            return MVCExtension.create(self.payload)
        return AVC3dExtension.create(self.payload)


