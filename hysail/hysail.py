from hysail.encryption.encode import Encode


def main():
    data = b"Hello fountain codes!"
    block_size = 8

    encoded = Encode(data, block_size, 30)
    for index, packet in enumerate(encoded.packets):
        print(index, packet.indices)


if __name__ == "__main__":
    main()
