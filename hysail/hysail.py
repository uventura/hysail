import json
import math
from pathlib import Path

import click
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)

from hysail.encryption.encode import Encode
from hysail.progress import set_progress
from hysail.server.packet_saver import PacketSaver
from hysail.constant import DEFAULT_BLOCK_SIZE_PERCENTAGE


def encode(
    input_file: str,
    block_size: int | None = None,
    server_list: list = None,
) -> int:
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


@click.command()
@click.option(
    "--encode", "input_file", type=click.Path(exists=True), help="File to encode"
)
@click.option(
    "--block-size",
    type=int,
    default=None,
    help="Block size for encoding; if omitted, uses 10% of the file size",
)
@click.option(
    "--server-list",
    type=click.Path(exists=True),
    required=True,
    help="JSON file with server list schema: {'servers': [{'id': <number>, 'storage_location': <location>}, ...]}",
)
def main(input_file, block_size, server_list):
    if not input_file:
        click.echo("Use --encode to specify a file to encode.")
        return

    with open(server_list, "r") as f:
        data = json.load(f)
    servers = data["servers"]
    with Progress(
        SpinnerColumn(),
        "[progress.description]{task.description}",
        BarColumn(),
        TextColumn("{task.completed}/{task.total}"),
        TimeElapsedColumn(),
        TimeRemainingColumn(),
    ) as progress:
        set_progress(progress)
        packet_count = encode(input_file, block_size, servers)
        set_progress(None)

    click.echo(f"Encoded {packet_count} packets distributed to {len(servers)} servers")


if __name__ == "__main__":
    main()
