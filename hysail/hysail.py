from hysail.encryption.encode import Encode
from hysail.encryption.decode import Decode
from hysail.server.server import Server

import random


def shuffle_packets(packets):
    random.shuffle(packets)
    return packets


def random_split_packets(packets, num_servers):
    if num_servers <= 0:
        raise ValueError("num_servers must be > 0")

    split_packets = [[] for _ in range(num_servers)]
    for pkt in packets:
        server_idx = random.randint(0, num_servers - 1)
        split_packets[int(server_idx)].append(pkt)

    return split_packets


def send_packets_to_servers(packets):
    num_servers = 3
    servers = [Server() for _ in range(num_servers)]
    local_blocks = {}

    split_packets = random_split_packets(packets, num_servers)
    for server, pkts in zip(servers, split_packets):
        for pkt in pkts:
            block = pkt.set_server(server)

            if block.degree not in local_blocks:
                local_blocks[int(block.degree)] = [block]
            else:
                local_blocks[int(block.degree)].append(block)
            server.storage_check_block(pkt)

    return servers, local_blocks


def main():
    data = b"Hello fountain codes, this is a weird message that I'm trying to make it work!"
    block_size = 8

    encoded = Encode(data, block_size, 30)
    local_mac_blocks = encoded.mac_blocks
    polynomials = encoded.polynomials

    packets = encoded.packets
    shuffle_packets(packets)
    servers, local_blocks = send_packets_to_servers(packets)

    decoded = Decode(servers, polynomials, local_blocks, local_mac_blocks).decode()
    print(decoded)

    # for pkt in packets:
    #     print(pkt.server)

    # print(packets)
    # for index, packet in enumerate(encoded.packets):
    #     print(index, packet)

    # print(encoded.mac_blocks)


if __name__ == "__main__":
    main()
