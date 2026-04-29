import json

from hysail.encryption.encoding_metadata import EncodingMetadata


def build_file_manifest(
    metadata: EncodingMetadata,
    metadata_uri: str,
    file_id: str | None = None,
) -> dict:
    resolved_file_id = file_id or _default_file_id(metadata)

    manifest = {
        "fileId": resolved_file_id,
        "metadataUri": metadata_uri,
        "originalFilename": metadata.original_filename,
        "originalFileHash": metadata.original_file_hash,
        "blockRoot": metadata.packet_root_hash,
        "packetCount": len(metadata.packets),
        "servers": sorted({packet.server for packet in metadata.packets}),
    }

    return manifest


def canonical_manifest_json(manifest: dict) -> str:
    return json.dumps(manifest, sort_keys=True, separators=(",", ":"))


def _default_file_id(metadata: EncodingMetadata) -> str:
    stem = metadata.original_filename or "hysail-file"
    digest = metadata.original_file_hash or metadata.packet_root_hash or "pending"
    return f"{stem}-{digest[:12]}"
