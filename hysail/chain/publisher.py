import json

from web3 import Web3

from hysail.chain.manifest import canonical_manifest_json

FILE_REGISTRY_ABI = [
    {
        "inputs": [
            {"internalType": "bytes32", "name": "fileId", "type": "bytes32"},
            {
                "internalType": "bytes32",
                "name": "manifestHash",
                "type": "bytes32",
            },
            {"internalType": "bytes32", "name": "blockRoot", "type": "bytes32"},
            {"internalType": "bytes32", "name": "fileHash", "type": "bytes32"},
            {
                "internalType": "string",
                "name": "metadataUri",
                "type": "string",
            },
        ],
        "name": "registerFile",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    }
]


class HysailChainPublisher:
    def __init__(self, rpc_url: str, contract_address: str, private_key: str):
        self.web3 = Web3(Web3.HTTPProvider(rpc_url))
        self.contract_address = Web3.to_checksum_address(contract_address)
        self.private_key = private_key
        self.account = self.web3.eth.account.from_key(private_key)
        self.contract = self.web3.eth.contract(
            address=self.contract_address,
            abi=FILE_REGISTRY_ABI,
        )

    def publish_manifest(self, manifest: dict) -> dict:
        manifest_json = canonical_manifest_json(manifest)
        file_id = self.web3.keccak(text=manifest["fileId"])
        manifest_hash = self.web3.keccak(text=manifest_json)
        block_root = self._as_bytes32(manifest["blockRoot"])
        file_hash = self._as_bytes32(manifest["originalFileHash"])

        transaction = self.contract.functions.registerFile(
            file_id,
            manifest_hash,
            block_root,
            file_hash,
            manifest["metadataUri"],
        ).build_transaction(
            {
                "from": self.account.address,
                "nonce": self.web3.eth.get_transaction_count(self.account.address),
                "chainId": self.web3.eth.chain_id,
                "gasPrice": self.web3.eth.gas_price,
            }
        )
        estimated_gas = self.web3.eth.estimate_gas(transaction)
        transaction["gas"] = int(estimated_gas * 1.2)

        signed = self.account.sign_transaction(transaction)
        tx_hash = self.web3.eth.send_raw_transaction(signed.raw_transaction)
        receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash)

        return {
            "fileId": manifest["fileId"],
            "manifestHash": manifest_hash.hex(),
            "transactionHash": tx_hash.hex(),
            "blockNumber": receipt.blockNumber,
            "contractAddress": self.contract_address,
        }

    def _as_bytes32(self, value: str) -> bytes:
        normalized = value.lower().removeprefix("0x")
        if len(normalized) != 64:
            raise ValueError(f"Expected 32-byte hex value, got '{value}'")
        return bytes.fromhex(normalized)


def load_file_registry_address(deployment_file: str) -> str:
    with open(deployment_file, "r", encoding="utf-8") as handle:
        deployments = json.load(handle)

    contract_address = deployments.get("fileRegistry")
    if not contract_address:
        raise ValueError("Deployment file does not contain 'fileRegistry'")

    return contract_address
