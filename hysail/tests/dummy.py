class DummyEncode:
    captured = None

    def __init__(self, data_arg, block_size_arg):
        self.captured["data"] = data_arg
        self.captured["block_size"] = block_size_arg
        self.packets = []
        self.mac_blocks = {}
        self.polynomials = []


class DummySaver:
    captured = None

    def __init__(self, packets, input_path, server_list):
        self.captured["packets"] = packets
        self.captured["input_path"] = input_path
        self.captured["server_list"] = server_list

    def save(self):
        pass

    @property
    def packet_metadata(self):
        return []


class DummyDecode:
    expected_metadata_file = None
    expected_server_file = None
    decoded_data = b""

    def __init__(self, metadata_file_arg, server_file_arg):
        assert metadata_file_arg == self.expected_metadata_file
        assert server_file_arg == self.expected_server_file

    def decode(self):
        return self.decoded_data


class DummyProgress:
    captured = None

    def add_task(self, description, total):
        self.captured["description"] = description
        self.captured["total"] = total
        return "task-id"

    def advance(self, task_id):
        assert task_id == "task-id"
        self.captured["advances"] += 1


class DummyHysailDecode:
    captured = None
    return_path = None

    def __init__(self, metadata_file_arg, server_file_arg, output_file_arg=None):
        self.captured["metadata_file"] = metadata_file_arg
        self.captured["server_file"] = server_file_arg
        self.captured["output_file"] = output_file_arg

    def decode(self):
        return self.return_path


class DummyHysailEncode:
    captured = None
    return_value = 0

    def __init__(
        self,
        input_file_arg,
        block_size_arg,
        server_list_arg,
        metadata_output_arg,
    ):
        self.captured["input_file"] = input_file_arg
        self.captured["block_size"] = block_size_arg
        self.captured["server_list"] = server_list_arg
        self.captured["metadata_output"] = metadata_output_arg

    def encode(self):
        return self.return_value
