from provider_mock import ProviderMockServer


def main() -> None:
    ProviderMockServer().serve_forever()


if __name__ == "__main__":
    main()
