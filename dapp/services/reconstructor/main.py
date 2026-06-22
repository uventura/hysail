import argparse
from pathlib import Path

from hysail.logger.logger import execution_logger

from models import ReconstructorConfig
from reconstructor import Reconstructor


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        dest="output",
        help="Output file path or existing output directory",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    config = ReconstructorConfig(
        output_path=Path(args.output) if args.output else None,
    )
    result = Reconstructor(config).reconstruct()
    execution_logger.info("Reconstruction complete")
    execution_logger.info(f"Output: {result.output_path}")
    execution_logger.info(f"Result hash: {result.payload_hash}")
    execution_logger.info(f"Job finalized: {result.job_id}")
    for tx_hash in result.tx_hashes:
        execution_logger.info(f"Transaction: {tx_hash}")


if __name__ == "__main__":
    main()
