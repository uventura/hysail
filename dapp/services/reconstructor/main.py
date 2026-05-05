from reconstructor import Reconstructor


def main() -> None:
    result = Reconstructor().reconstruct()
    print("Reconstruction complete")
    print(f"Output: {result.output_path}")
    print(f"Result hash: {result.payload_hash}")
    print(f"Job finalized: {result.job_id}")
    for tx_hash in result.tx_hashes:
        print(f"Transaction: {tx_hash}")


if __name__ == "__main__":
    main()
