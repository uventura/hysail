import pickle
import random
from pathlib import Path

from hysail.logger.progress import get_progress
from hysail.server.server import Server


class PacketSaver:
    def __init__(self, packets, input_path, server_list=None, metadata=None):
        self.packets = packets
        self.input_path = input_path
        self.server_list = server_list
        self.metadata = metadata
        self.progress = get_progress()

    def save(self):
        if not self.server_list:
            raise ValueError("server_list is required")

        self._shuffle_packets()
        self._save_to_servers()
        if self.metadata:
            self._save_metadata()

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
            self._save_single_packet(packet, servers, task_id)

    def _save_single_packet(self, packet, servers, task_id):
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

        if self.metadata:
            self.metadata.add_packet(server._storage_location, packet.indices)

        if task_id is not None:
            self.progress.advance(task_id)

    def _save_metadata(self):
        metadata_file = self.input_path.parent / f"{self.input_path.stem}_metadata.pkl"
        self.metadata.save(metadata_file)
