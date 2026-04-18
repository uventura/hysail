import json

import click
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)

from hysail.hysail_decode import HysailDecode
from hysail.hysail_encode import HysailEncode
from hysail.logger.progress import set_progress


def _create_progress() -> Progress:
    return Progress(
        SpinnerColumn(),
        "[progress.description]{task.description}",
        BarColumn(),
        TextColumn("{task.completed}/{task.total}"),
        TimeElapsedColumn(),
        TimeRemainingColumn(),
    )


@click.group()
def main():
    pass


@main.command("encode")
@click.argument("input_file", type=click.Path(exists=True))
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
def encode_command(input_file, block_size, server_list):
    with open(server_list, "r") as f:
        data = json.load(f)
    servers = data["servers"]

    with _create_progress() as progress:
        set_progress(progress)
        hysail_encode = HysailEncode(input_file, block_size, servers)
        packet_count = hysail_encode.encode()
        set_progress(None)

    click.echo(f"Encoded {packet_count} packets distributed to {len(servers)} servers")


@main.command("decode")
@click.argument("metadata_file", type=click.Path(exists=True))
@click.option(
    "--server-file",
    type=click.Path(exists=True),
    required=True,
    help="JSON file with server information for decoding",
)
@click.option(
    "--output-file",
    type=click.Path(),
    default="./",
    show_default=True,
    help="Path where the decoded file will be written",
)
def decode_command(metadata_file, server_file, output_file):
    with _create_progress() as progress:
        set_progress(progress)
        hysail_decode = HysailDecode(metadata_file, server_file, output_file)
        output_path = hysail_decode.decode()
        set_progress(None)

    click.echo(f"Decoded file written to {output_path}")


if __name__ == "__main__":
    main()
