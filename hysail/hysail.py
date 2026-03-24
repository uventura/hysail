from hysail.encryption.encode import Encode
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
        split_packets[server_idx].append(pkt)

    return split_packets


def send_packets_to_servers(packets):
    num_servers = 3
    servers = [Server() for _ in range(num_servers)]
    split_packets = random_split_packets(packets, num_servers)
    for server, pkts in zip(servers, split_packets):
        for pkt in pkts:
            pkt.set_server(server)
            server.storage_check_block(pkt)

    return servers


def main():
    data = b"Hello fountain codes!"
    block_size = 8

    encoded = Encode(data, block_size, 30)
    packets = encoded.packets
    shuffle_packets(packets)
    servers = send_packets_to_servers(packets)

    for pkt in packets:
        print(pkt.server)

    # print(packets)
    # for index, packet in enumerate(encoded.packets):
    #     print(index, packet)

    # print(encoded.mac_blocks)


if __name__ == "__main__":
    main()
