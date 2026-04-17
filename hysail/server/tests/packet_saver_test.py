from pathlib import Path

from hysail.server.packet_saver import PacketSaver
from hysail.encryption.block import Block


def test_when_saving_to_servers_then_packets_distributed(tmp_path):
    packets = [Block(0, 1, [0], b"data1")]
    input_path = Path("test.txt")
    server_list = [{"id": 1, "storage_location": str(tmp_path / "server1")}]

    saver = PacketSaver(packets, input_path, server_list=server_list)
    saver.save()

    # Check if server directory has the file
    server_dir = tmp_path / "server1"
    assert (server_dir / "test_packet_0.pkl").exists()
