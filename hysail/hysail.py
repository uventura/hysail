from hysail.encryption.encode import Encode
import click
import os
import pickle
from pathlib import Path


def encode(input_file: str, output: str, block_size: int = 8) -> int:
    input_path = Path(input_file)
    with open(input_path, "rb") as file:
        data = file.read()

    encoded = Encode(data, block_size)
    packets = encoded.packets

    os.makedirs(output, exist_ok=True)
    for i, packet in enumerate(packets):
        output_file = os.path.join(output, f"{input_path.name}_packet_{i}.pkl")
        with open(output_file, "wb") as f:
            pickle.dump(packet, f)

    return len(packets)


@click.command()
@click.option(
    "--encode", "input_file", type=click.Path(exists=True), help="File to encode"
)
@click.option("--block-size", default=8, help="Block size for encoding")
@click.option(
    "--output",
    type=click.Path(file_okay=False, dir_okay=True),
    required=True,
    help="Directory where generated packets will be placed",
)
def main(input_file, block_size, output):
    if input_file:
        packet_count = encode(input_file, output, block_size)
        click.echo(f"Encoded {packet_count} packets saved to {output}")
    else:
        click.echo("Use --encode to specify a file to encode.")


if __name__ == "__main__":
    main()
