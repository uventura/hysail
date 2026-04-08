from dataclasses import dataclass

from hysail.server.server import Server


@dataclass
class LocalBlock:
    index: int
    degree: int
    indices: list[int]
    server: Server


class Block:
    def __init__(self, index, degree, indices, data):
        self.index = index
        self.degree = degree
        self.indices = list(indices)
        self.data = data
        self.server = None

    def __str__(self):
        return f"Block(index={self.index}, degree={self.degree}, indices={self.indices}, data={self.data}, server={self.server})"

    def __repr__(self):
        return f"Block(index={self.index}, degree={self.degree}, indices={self.indices}, data={self.data}, server={self.server})"

    def set_server(self, server):
        self.server = server

        return LocalBlock(self.index, self.degree, self.indices, server)

    def copy(self):
        return Block(self.degree, self.indices.copy(), self.data)
