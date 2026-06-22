from __future__ import annotations

from pathlib import Path

from errors import ValidationError
from models import ReconstructionResult, ReconstructorConfig
from retrieval import BlockRetrievalService
from settlement import DownloadSettlementService


class Reconstructor:
    def __init__(self, config: ReconstructorConfig | None = None):
        self.config = config or ReconstructorConfig()
        self.block_retrieval = BlockRetrievalService()
        self.settlement = DownloadSettlementService(self.config)

    def reconstruct(self) -> ReconstructionResult:
        manifest = self.block_retrieval.load_manifest(self.config.manifest_path)
        try:
            decoder = self.block_retrieval.build_decoder(manifest)
            payload = decoder.decode()
            payload_hash = self.block_retrieval.sha256_hex(payload)
            self.block_retrieval.validate_payload_hash(manifest, payload_hash)
            output_path = self._write_output_file(manifest, payload)
            accepted_blocks = self.block_retrieval.build_accepted_blocks(decoder)
            job_id, tx_hashes = self.settlement.settle_job(
                manifest, accepted_blocks, payload_hash
            )
            return ReconstructionResult(
                output_path=output_path,
                payload_hash=payload_hash,
                job_id=job_id,
                tx_hashes=tx_hashes,
            )
        except ValidationError as error:
            job_id = self.reject_latest_job()
            if job_id is not None:
                raise SystemExit(
                    f"{error}. Download job {job_id} rejected with refund."
                ) from error
            raise SystemExit(str(error)) from error

    def reject_latest_job(self) -> int | None:
        return self.settlement.reject_latest_job()

    def _write_output_file(self, manifest: dict, payload: bytes):
        output_path = self._resolve_output_path(manifest)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(payload)
        return output_path

    def _resolve_output_path(self, manifest: dict) -> Path:
        if self.config.output_path is None:
            return self.config.output_dir / manifest["outputFileName"]

        configured_path = self.config.output_path
        if configured_path in {Path("."), Path("./")}:
            return configured_path / manifest["outputFileName"]

        if configured_path.exists() and configured_path.is_dir():
            return configured_path / manifest["outputFileName"]

        return configured_path
