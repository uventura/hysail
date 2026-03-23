class Server:
    def __init__(self):
        self._check_blocks = []

    def storage_check_block(self, check_block):
        self._check_blocks.append(check_block)
