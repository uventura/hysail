import pickle
import random
from pathlib import Path

from hysail.logger.progress import advance_progress, create_progress_task, get_progress
from hysail.server.server import Server
from hysail.encryption.encoding_metadata import PacketMetadata


class PacketSaver:
    def __init__(self, packets, input_path, server_list=None):
        self.packets = packets
        self.input_path = input_path
        self.server_list = server_list
        self.progress = get_progress()
        self._packet_metadata = []

    def save(self):
        if not self.server_list:
            raise ValueError("server_list is required")

        self._shuffle_packets()
        self._save_to_servers()

    @property
    def packet_metadata(self):
        return self._packet_metadata

    def _shuffle_packets(self):
        random.shuffle(self.packets)

    def _save_to_servers(self):
        servers = [
            Server(server_dict["storage_location"]) for server_dict in self.server_list
        ]
        task_id = create_progress_task(
            self.progress,
            "Saving packets to server storage",
            total=len(self.packets),
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

        self._packet_metadata.append(
            PacketMetadata(
                server=server._storage_location,
                packet_index=packet.index,
                degree=packet.degree,
                indices=packet.indices,
            )
        )

        advance_progress(self.progress, task_id)
