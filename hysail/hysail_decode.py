from pathlib import Path

from hysail.encryption.decode import Decode
from hysail.encryption.encoding_metadata import EncodingMetadata
from hysail.logger.progress import advance_progress, create_progress_task, get_progress


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
        task_id = create_progress_task(progress, "Decoding file", total=3)

        decoder = Decode(self.metadata_file, self.server_file)
        advance_progress(progress, task_id)

        decoded_data = decoder.decode()
        advance_progress(progress, task_id)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "wb") as file:
            file.write(decoded_data)

        advance_progress(progress, task_id)

        return output_path

    def _determine_output_path(self, metadata_path: Path) -> Path:
        output_name = self._determine_output_name(metadata_path)
        if self.output_file is None:
            return metadata_path.with_name(output_name)

        output_path = Path(self.output_file)
        if output_path in {Path("."), Path("./")}:
            return output_path / output_name

        if output_path.exists() and output_path.is_dir():
            return output_path / output_name

        return output_path

    def _determine_output_name(self, metadata_path: Path) -> str:
        metadata = EncodingMetadata.load(metadata_path)
        original_filename = getattr(metadata, "original_filename", "")
        if original_filename:
            return Path(original_filename).name

        output_stem = metadata_path.stem
        if output_stem.endswith("_metadata"):
            output_stem = output_stem[: -len("_metadata")]

        return f"{output_stem}_decoded.bin"
