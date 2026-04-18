import math
from pathlib import Path

from hysail.constant import DEFAULT_BLOCK_SIZE_PERCENTAGE
from hysail.encryption.encode import Encode
from hysail.server.packet_saver import PacketSaver


def encode(input_file: str, block_size: int | None = None, server_list: list = None) -> int:
    input_path = Path(input_file)
    with open(input_path, "rb") as file:
        data = file.read()

    block_size = _determine_block_size(len(data), block_size)
    encoded = Encode(data, block_size)
    packets = encoded.packets

    saver = PacketSaver(packets, input_path, server_list)
    saver.save()
    return len(packets)


def _determine_block_size(file_size: int, block_size: int | None) -> int:
    if block_size is None:
        return max(1, math.ceil(file_size * DEFAULT_BLOCK_SIZE_PERCENTAGE))

    if block_size <= 0:
        raise ValueError("Block size must be a positive integer")

    return block_size
