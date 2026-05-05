from __future__ import annotations

from errors import ValidationError
from models import ReconstructionResult, ReconstructorConfig
from retrieval import PacketRetrievalService
from settlement import DownloadSettlementService


class Reconstructor:
    def __init__(self, config: ReconstructorConfig | None = None):
        self.config = config or ReconstructorConfig()
        self.packet_retrieval = PacketRetrievalService()
        self.settlement = DownloadSettlementService(self.config)

    def reconstruct(self) -> ReconstructionResult:
        manifest = self.packet_retrieval.load_manifest(self.config.manifest_path)
        try:
            retrieved_data, accepted_packets = self.packet_retrieval.retrieve_blocks(
                manifest
            )
            payload = self.packet_retrieval.build_payload(retrieved_data)
            payload_hash = self.packet_retrieval.sha256_hex(payload)
            self.packet_retrieval.validate_payload_hash(manifest, payload_hash)
            output_path = self._write_output_file(manifest, payload)
            job_id, tx_hashes = self.settlement.settle_job(
                manifest, accepted_packets, payload_hash
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
        self.config.output_dir.mkdir(parents=True, exist_ok=True)
        output_path = self.config.output_dir / manifest["outputFileName"]
        output_path.write_bytes(payload)
        return output_path
