from hysail.encryption.encode import Encode
import click
import json
from pathlib import Path
from hysail.server.packet_saver import PacketSaver


def encode(input_file: str, block_size: int = 8, server_list: list = None) -> int:
    input_path = Path(input_file)
    with open(input_path, "rb") as file:
        data = file.read()

    encoded = Encode(data, block_size)
    packets = encoded.packets

    saver = PacketSaver(packets, input_path, server_list)
    saver.save()
    return len(packets)


@click.command()
@click.option(
    "--encode", "input_file", type=click.Path(exists=True), help="File to encode"
)
@click.option("--block-size", default=8, help="Block size for encoding")
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

    with open(server_list, 'r') as f:
        data = json.load(f)
    servers = data['servers']
    packet_count = encode(input_file, block_size, servers)
    click.echo(f"Encoded {packet_count} packets distributed to {len(servers)} servers")


if __name__ == "__main__":
    main()
