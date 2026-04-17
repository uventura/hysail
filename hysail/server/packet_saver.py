import pickle
from pathlib import Path

from hysail.server.server import Server


class PacketSaver:
    def __init__(self, packets, input_path, server_list=None):
        self.packets = packets
        self.input_path = input_path
        self.server_list = server_list

    def save(self):
        if not self.server_list:
            raise ValueError("server_list is required")
        self._save_to_servers()

    def _save_to_servers(self):
        servers = [Server(server_dict['storage_location']) for server_dict in self.server_list]
        for packet in self.packets:
            server_index = packet.index % len(servers)
            server = servers[server_index]
            server_storage = Path(server._storage_location)
            server_storage.mkdir(parents=True, exist_ok=True)
            packet_file = server_storage / f"{self.input_path.stem}_packet_{packet.index}.pkl"

            with open(packet_file, "wb") as f:
                pickle.dump(packet, f)
