from hysail.logger.logger import execution_logger

from reconstructor import Reconstructor


def main() -> None:
    result = Reconstructor().reconstruct()
    execution_logger.info("Reconstruction complete")
    execution_logger.info(f"Output: {result.output_path}")
    execution_logger.info(f"Result hash: {result.payload_hash}")
    execution_logger.info(f"Job finalized: {result.job_id}")
    for tx_hash in result.tx_hashes:
        execution_logger.info(f"Transaction: {tx_hash}")


if __name__ == "__main__":
    main()
