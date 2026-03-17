from hysail.lt_code import LtCodeEncode, LtCodeDecode, LtPacket


def main():
    data = b"Hello fountain codes!"
    block_size = 8

    encoded = LtCodeEncode(data, block_size, 100)
    for packet in encoded.packets:
        print(packet.indices)
    decoded = LtCodeDecode(encoded.packets, encoded.num_blocks)
    print(decoded.data)


if __name__ == "__main__":
    main()
