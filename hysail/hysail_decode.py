from pathlib import Path

from hysail.encryption.decode import Decode
from hysail.logger.progress import get_progress


class HysailDecode:
    def __init__(
        self,
        metadata_file: str,
        server_file: str,
        output_file: str | None = None,
    ):
        self.metadata_file = metadata_file
        self.server_file = server_file
        self.output_file = output_file

    def decode(self) -> Path:
        metadata_path = Path(self.metadata_file)
        output_path = self._determine_output_path(metadata_path)

        progress = get_progress()
        task_id = None
        if progress is not None:
            task_id = progress.add_task("Decoding file", total=3)

        decoder = Decode(self.metadata_file, self.server_file)
        if task_id is not None:
            progress.advance(task_id)

        decoded_data = decoder.decode()
        if task_id is not None:
            progress.advance(task_id)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "wb") as file:
            file.write(decoded_data)

        if task_id is not None:
            progress.advance(task_id)

        return output_path

    def _determine_output_path(self, metadata_path: Path) -> Path:
        output_stem = metadata_path.stem
        if output_stem.endswith("_metadata"):
            output_stem = output_stem[: -len("_metadata")]

        output_name = f"{output_stem}_decoded.bin"
        if self.output_file is None:
            return metadata_path.with_name(output_name)

        output_path = Path(self.output_file)
        if output_path in {Path("."), Path("./")}:
            return output_path / output_name

        if output_path.exists() and output_path.is_dir():
            return output_path / output_name

        return output_path
