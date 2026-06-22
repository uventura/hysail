def add_padding(data: bytes, block_size: int) -> bytes:
    if block_size <= 0:
        raise ValueError("block_size must be greater than zero")

    if block_size <= 255:
        padding_size = block_size - (len(data) % block_size)
        if padding_size == 0:
            padding_size = block_size
        return data + bytes([padding_size]) * padding_size

    # For large block sizes, append zero bytes plus a 4-byte trailer
    # containing the total padding size to avoid the single-byte limit.
    trailer_size = 4
    zero_padding_size = (
        block_size - ((len(data) + trailer_size) % block_size)
    ) % block_size
    if zero_padding_size == 0:
        zero_padding_size = block_size

    padding_size = zero_padding_size + trailer_size
    return (
        data
        + (b"\x00" * zero_padding_size)
        + padding_size.to_bytes(
            trailer_size,
            byteorder="big",
        )
    )


def remove_padding(data: bytes) -> bytes:
    if not data:
        return data

    padding_size = data[-1]
    if padding_size == 0 or padding_size > len(data):
        pass
    else:
        padding = bytes([padding_size]) * padding_size
        if data[-padding_size:] == padding:
            return data[:-padding_size]

    if len(data) < 4:
        return data

    trailer_size = 4
    padding_size = int.from_bytes(data[-trailer_size:], byteorder="big")
    if padding_size <= trailer_size or padding_size > len(data):
        return data

    zero_padding_size = padding_size - trailer_size
    if data[-padding_size:-trailer_size] != (b"\x00" * zero_padding_size):
        return data

    return data[:-padding_size]
