import math
from pathlib import Path

from hysail.constant import DEFAULT_BLOCK_SIZE_PERCENTAGE
from hysail.encryption.encode import Encode
from hysail.encryption.encoding_metadata import BlockMetadata, EncodingMetadata
from hysail.server.packet_saver import PacketSaver


class HysailEncode:
    def __init__(
        self,
        input_file: str,
        block_size: int | None = None,
        server_list: list = None,
    ):
        self.input_file = input_file
        self.block_size = block_size
        self.server_list = server_list

    def encode(self) -> int:
        input_path = Path(self.input_file)
        with open(input_path, "rb") as file:
            data = file.read()

        block_size = self._determine_block_size(len(data))
        encoded = Encode(data, block_size)
        packets = encoded.packets

        saver = PacketSaver(packets, input_path, self.server_list)
        saver.save()

        self._save_packet_metadata(encoded, saver)
        return len(packets)

    def _collect_metadata(self, encoded):
        blocks = []
        for block_index, mac_list in encoded.mac_blocks.items():
            for local_mac in mac_list:
                blocks.append(
                    BlockMetadata(
                        mac_value=local_mac.mac,
                        block_index=block_index,
                        polynomial_index=local_mac.polynomial_index,
                    )
                )

        return EncodingMetadata(
            polynomials=encoded.polynomials, blocks=blocks, packets=[]
        )

    def _determine_block_size(self, file_size: int) -> int:
        if self.block_size is None:
            return max(1, math.ceil(file_size * DEFAULT_BLOCK_SIZE_PERCENTAGE))

        if self.block_size <= 0:
            raise ValueError("Block size must be a positive integer")

        return self.block_size

    def _save_packet_metadata(self, encoded, saver):
        metadata = self._collect_metadata(encoded)

        for packet in saver.packet_metadata:
            metadata.add_packet(
                server=packet.server,
                packet_index=packet.packet_index,
                degree=packet.degree,
                indices=packet.indices,
            )
