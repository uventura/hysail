from pathlib import Path

from hysail.server.packet_saver import PacketSaver
from hysail.encryption.block import Block


def test_when_saving_to_servers_then_packets_distributed(tmp_path):
    packets = [Block(0, 1, [0], b"data1")]
    input_path = Path("test.txt")
    server_list = [{"id": 1, "storage_location": str(tmp_path / "server1")}]

    saver = PacketSaver(packets, input_path, server_list=server_list)
    saver.save()

    server_dir = tmp_path / "server1"
    assert (server_dir / "test_packet_0.pkl").exists()
    assert packets[0].server is not None
    assert packets[0].server._storage_location == str(server_dir)


def test_when_saving_multiple_packets_then_each_block_has_server(tmp_path):
    packets = [
        Block(0, 1, [0], b"data1"),
        Block(1, 1, [1], b"data2"),
    ]
    input_path = Path("test.txt")
    server_list = [
        {"id": 1, "storage_location": str(tmp_path / "server1")},
        {"id": 2, "storage_location": str(tmp_path / "server2")},
    ]

    saver = PacketSaver(packets, input_path, server_list=server_list)
    saver.save()

    assert packets[0].server is not None
    assert packets[1].server is not None
    assert packets[0].server._storage_location in {str(tmp_path / "server1"), str(tmp_path / "server2")}
    assert packets[1].server._storage_location in {str(tmp_path / "server1"), str(tmp_path / "server2")}
