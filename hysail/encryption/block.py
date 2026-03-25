from dataclasses import dataclass

from hysail.server.server import Server

@dataclass
class LocalBlock:
    index: int
    degree: int
    indices: list[int]

class Block:
    def __init__(self, index, degree, indices, data):
        self.index = index
        self.degree = degree
        self.indices = list(indices)
        self.data = data
        self.server = None

    def set_server(self, server):
        self.server = server

        return LocalBlock(self.index, self.degree, self.indices)

    def copy(self):
        return Block(self.degree, self.indices.copy(), self.data)
