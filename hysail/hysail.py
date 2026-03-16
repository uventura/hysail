from lt import encode, decode
import io
import itertools


def main():
    data = b"Hello fountain codes!"
    input_file = io.BytesIO(data)
    block_size = 8
    encoder = encode.encoder(input_file, block_size)

    packet = next(encoder)

    degree = packet[0]
    print("degree:", degree)
    print("raw packet:", packet)

    packets = list(itertools.islice(encoder, 10))
    for i, packet in enumerate(packets):
        binary = " ".join(format(b, "08b") for b in packet)
        print(f"Packet {i}: {binary}")

    packet_stream = io.BytesIO(b"".join(packets))
    decoded_file = io.BytesIO()
    decode.decode(packet_stream, decoded_file)

    decoded_file.seek(0)
    print(decoded_file.read())


if __name__ == "__main__":
    main()
