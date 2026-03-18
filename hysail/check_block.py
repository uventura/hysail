from dataclasses import dataclass


@dataclass
class CheckBlock:
    check_block_indice: int
    message_blocks: list
