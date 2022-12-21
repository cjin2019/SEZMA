from dataclasses import dataclass
from typing import Dict, Optional, Tuple, Type, Union

from analysis.packet.exceptions import PacketException
from analysis.packet.packet_constants import ExceptionCodes, RTPWrapper, contains_value
from analysis.packet.nal import NAL


@dataclass
class RTPHeader:
    version: int
    has_padding: int
    has_extension: int
    csrc_count: int
    marker: int
    payload_type: "RTPWrapper"
    seq_num: int
    timestamp: bytes
    ssrc: bytes
    extension_header: "RTPExtensionHeader"
    csrcs: Union[Tuple[bytes], Tuple[()]] = ()
    profile_specific_id: Optional[bytes] = None
    extension_header_len: Optional[int] = None

    @classmethod
    def get_header(cls: Type["RTPHeader"], rtp_data: bytes) -> Tuple["RTPHeader", int]:
        """
        Raises an exception is version is invalid

        Returns RTPHeader and the starting index of the payload
        """
        oct1: int = rtp_data[0]

        version: int = oct1 >> 6
        if version != 2:
            raise PacketException(ExceptionCodes.INVALID_RTP_VERSION)
        has_padding: int = (oct1 >> 5) & 1
        has_extension: int = (oct1 >> 4) & 1
        csrc_count: int = oct1 & 15

        oct2: int = rtp_data[1]
        marker: int = oct2 >> 7
        payload_type_val: int = oct2 & 127
        if not contains_value(RTPWrapper, payload_type_val):
            raise PacketException(ExceptionCodes.UNSUPPORTED_RTP_TYPE)
        payload_type: "RTPWrapper" = RTPWrapper(payload_type_val)

        seq_num: int = int.from_bytes(rtp_data[2:4], "big")
        timestamp: bytes = rtp_data[4:8]
        ssrc: bytes = rtp_data[8:12]

        csrcs = []
        for csrc_idx in range(12, 12 + 4 * csrc_count, 4):
            csrcs.append(rtp_data[csrc_idx : csrc_idx + 4])
        csrcs = tuple(csrcs)

        payload_idx: int = 12 + 4 * csrc_count
        profile_specific_id: Optional[bytes] = None
        extension_header_len: Optional[int] = None
        extension_header: Optional[bytes] = None

        if has_extension == 1:
            extension_idx = 12 + 4 * csrc_count
            profile_specific_id = rtp_data[extension_idx : extension_idx + 2]
            extension_header_len = 4 * int.from_bytes(
                rtp_data[extension_idx + 2 : extension_idx + 4], "big"
            )
            extension_header = rtp_data[
                extension_idx + 4 : extension_idx + 4 + extension_header_len
            ]
            payload_idx = extension_idx + 4 + extension_header_len

        extension_header_input = RTPExtensionHeader({})
        if extension_header is not None:
            extension_header_input = RTPExtensionHeader.create(extension_header)

        return (
            RTPHeader(
                version=version,
                has_padding=has_padding,
                has_extension=has_extension,
                csrc_count=csrc_count,
                marker=marker,
                payload_type=payload_type,
                seq_num=seq_num,
                timestamp=timestamp,
                ssrc=ssrc,
                csrcs=csrcs,
                profile_specific_id=profile_specific_id,
                extension_header_len=extension_header_len,
                extension_header=extension_header_input,
            ),
            payload_idx,
        )


class RTPExtensionHeader:
    """
    Following one byte

    https://www.rfc-editor.org/rfc/rfc8285.html#section-4.2
    """

    def __init__(self, data: Dict[int, bytes]) -> None:
        self.__data = data

    def __str__(self) -> str:
        return str(self.__data)

    def __getitem__(self, id: int) -> Optional[bytes]:
        return self.__data[id] if id in self.__data else None

    @classmethod
    def create(cls, data: bytes) -> "RTPExtensionHeader":
        idx = 0
        inp = {}
        while idx < len(data):
            header: int = data[idx]
            id: int = header >> 4

            if id == 0:
                break

            length: int = (header & 15) + 1

            idx += 1
            extension_data: bytes = data[idx : idx + length]
            inp[id] = extension_data

            idx += length

        return RTPExtensionHeader(inp)


class RTP:
    """
    Check https://en.wikipedia.org/wiki/Real-time_Transport_Protocol
    """

    def __init__(self, data: bytes) -> None:
        header, payload_idx = RTPHeader.get_header(data)
        self.__header: "RTPHeader" = header
        self.__payload: bytes = data[payload_idx:]

    @property
    def header(self) -> "RTPHeader":
        return self.__header

    @property
    def payload(self) -> bytes:
        return self.__payload

    def get_next_layer(self) -> "NAL":
        return NAL(self.__payload)
