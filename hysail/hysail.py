from hysail.lt_code import LtCodeEncode, LtCodeDecode, LtPacket


def main():
    data = b"Hello fountain codes!"
    block_size = 8

    encode = LtCodeEncode(data, block_size)
    print(encode.packet.indices)


if __name__ == "__main__":
    main()
