class Block:
    def __init__(self, degree, indices, data):
        self.degree = degree
        self.indices = list(indices)
        self.data = data

    def copy(self):
        return Block(self.degree, self.indices.copy(), self.data)
