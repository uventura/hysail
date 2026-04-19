def add_padding(data: bytes, block_size: int) -> bytes:
    padding_size = block_size - (len(data) % block_size)
    if padding_size == 0:
        padding_size = block_size
    return data + bytes([padding_size]) * padding_size


def remove_padding(data: bytes) -> bytes:
    if not data:
        return data

    padding_size = data[-1]
    if padding_size == 0 or padding_size > len(data):
        return data

    padding = bytes([padding_size]) * padding_size
    if data[-padding_size:] != padding:
        return data

    return data[:-padding_size]
