import pickle
import random
from pathlib import Path

from hysail.progress import get_progress
from hysail.server.server import Server


class PacketSaver:
    def __init__(self, packets, input_path, server_list=None):
        self.packets = packets
        self.input_path = input_path
        self.server_list = server_list
        self.progress = get_progress()

    def save(self):
        if not self.server_list:
            raise ValueError("server_list is required")

        self._shuffle_packets()
        self._save_to_servers()

    def _shuffle_packets(self):
        random.shuffle(self.packets)

    def _save_to_servers(self):
        servers = [
            Server(server_dict["storage_location"]) for server_dict in self.server_list
        ]
        task_id = None
        if self.progress is not None:
            task_id = self.progress.add_task(
                "Saving packets to server storage", total=len(self.packets)
            )

        for packet in self.packets:
            server_index = packet.index % len(servers)
            server = servers[server_index]
            packet.set_server(server)
            server_storage = Path(server._storage_location)
            server_storage.mkdir(parents=True, exist_ok=True)
            packet_file = (
                server_storage / f"{self.input_path.stem}_packet_{packet.index}.pkl"
            )

            with open(packet_file, "wb") as f:
                pickle.dump(packet, f)

            if task_id is not None:
                self.progress.advance(task_id)
