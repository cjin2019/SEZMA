from dataclasses import dataclass
from typing import Dict, Union

from app.analysis.packet.fua import FU_A


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
            nal_unit_type=nal_unit_type,
        )


class NAL:
    def __init__(self, nal_data: bytes) -> None:
        self.__header = NALHeader.get_header(nal_data)
        self.__payload = nal_data[1:]

    @property
    def header(self) -> "NALHeader":
        return self.__header

    @property
    def payload(self) -> bytes:
        return self.__payload

    def get_next_layer(self) -> "FU_A":
        return FU_A(self.payload)
