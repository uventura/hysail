from __future__ import annotations

import json
import os
from urllib.error import HTTPError, URLError

from web3 import Web3

from abi import DOWNLOAD_MANAGER_ABI
from constants import JOB_ID_ENV_VAR
from models import ChainContext, JobContext, RetrievedPacket, ReconstructorConfig


class DownloadSettlementService:
    def __init__(self, config: ReconstructorConfig):
        self.config = config

    def reject_latest_job(self) -> int | None:
        try:
            chain_context = self._create_chain_context()
            job_context = self._load_job_context(chain_context)
            self._reject_job(job_context)
            return job_context.job_id
        except (RuntimeError, HTTPError, URLError, ValueError):
            return None

    def settle_job(
        self, manifest: dict, accepted_packets: list[RetrievedPacket], result_hash: str
    ) -> tuple[int, list[str]]:
        chain_context = self._create_chain_context()
        job_context = self._load_job_context(chain_context)
        self._validate_job_ownership(job_context)
        self._ensure_job_not_finalized(job_context)

        tx_hashes = [
            self._accept_block(job_context, manifest["providerAddress"], packet)
            for packet in accepted_packets
        ]
        tx_hashes.append(self._finalize_job(job_context, result_hash))
        return job_context.job_id, tx_hashes

    def _get_download_manager(self, web3: Web3):
        deployments = json.loads(self.config.deployments_path.read_text())
        return web3.eth.contract(
            address=Web3.to_checksum_address(deployments["downloadManager"]),
            abi=DOWNLOAD_MANAGER_ABI,
        )

    def _get_job_id(self, download_manager) -> int:
        explicit_job_id = os.environ.get(JOB_ID_ENV_VAR)
        if explicit_job_id is not None:
            return int(explicit_job_id)

        job_id = download_manager.functions.jobCount().call()
        if job_id == 0:
            raise RuntimeError("No download job available")
        return int(job_id)

    def _build_transaction_params(self, chain_context: ChainContext) -> dict:
        return {
            "from": chain_context.account.address,
            "nonce": chain_context.web3.eth.get_transaction_count(
                chain_context.account.address
            ),
            "chainId": chain_context.web3.eth.chain_id,
            "gas": 300000,
            "gasPrice": chain_context.web3.eth.gas_price,
        }

    def _create_chain_context(self) -> ChainContext:
        web3 = Web3(Web3.HTTPProvider(self.config.rpc_url))
        account = web3.eth.account.from_key(self.config.private_key)
        return ChainContext(
            web3=web3,
            account=account,
            download_manager=self._get_download_manager(web3),
        )

    def _load_job_context(self, chain_context: ChainContext) -> JobContext:
        job_id = self._get_job_id(chain_context.download_manager)
        job = chain_context.download_manager.functions.jobs(job_id).call()
        return JobContext(chain_context=chain_context, job_id=job_id, job=job)

    def _validate_job_ownership(self, job_context: JobContext) -> None:
        if Web3.to_checksum_address(job_context.job[1]) == Web3.to_checksum_address(
            job_context.chain_context.account.address
        ):
            return

        raise RuntimeError(
            "Latest download job does not belong to the configured requester"
        )

    def _ensure_job_not_finalized(self, job_context: JobContext) -> None:
        if not job_context.job[-1]:
            return

        raise RuntimeError(f"Download job {job_context.job_id} is already finalized")

    def _accept_block(
        self,
        job_context: JobContext,
        provider_address: str,
        packet: RetrievedPacket,
    ) -> str:
        return self._send_transaction(
            job_context.chain_context,
            job_context.chain_context.download_manager.functions.acceptBlock(
                job_context.job_id,
                Web3.keccak(text=packet.block_id),
                Web3.to_checksum_address(provider_address),
                packet.price_wei,
            ),
        )

    def _finalize_job(self, job_context: JobContext, result_hash: str) -> str:
        return self._send_transaction(
            job_context.chain_context,
            job_context.chain_context.download_manager.functions.finalizeJob(
                job_context.job_id, bytes.fromhex(result_hash)
            ),
        )

    def _send_transaction(self, chain_context: ChainContext, function_call) -> str:
        transaction = function_call.build_transaction(
            self._build_transaction_params(chain_context)
        )
        signed = chain_context.account.sign_transaction(transaction)
        tx_hash = chain_context.web3.eth.send_raw_transaction(signed.raw_transaction)
        chain_context.web3.eth.wait_for_transaction_receipt(tx_hash)
        return tx_hash.hex()

    def _reject_job(self, job_context: JobContext) -> None:
        if job_context.job[-1]:
            return
        self._send_transaction(
            job_context.chain_context,
            job_context.chain_context.download_manager.functions.rejectJob(
                job_context.job_id
            ),
        )
