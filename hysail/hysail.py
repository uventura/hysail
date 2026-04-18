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

from hysail.hysail_encode import HysailEncode
from hysail.progress import set_progress


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
        hysail_encode = HysailEncode(input_file, block_size, servers)
        packet_count = hysail_encode.encode()
        set_progress(None)

    click.echo(f"Encoded {packet_count} packets distributed to {len(servers)} servers")


if __name__ == "__main__":
    main()
