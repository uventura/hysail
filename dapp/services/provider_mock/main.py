import argparse

from provider_mock import ProviderMockConfig, ProviderMockServer


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-n",
        "--servers",
        type=int,
        default=None,
        help="Number of provider mock servers to start",
    )
    args = parser.parse_args()

    config = ProviderMockConfig(server_count=args.servers)
    ProviderMockServer(config=config).serve_forever()


if __name__ == "__main__":
    main()
