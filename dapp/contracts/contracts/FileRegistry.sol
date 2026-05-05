// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract FileRegistry {
    struct FileRecord {
        address owner;
        bytes32 manifestHash;
        bytes32 blockRoot;
        bytes32 fileHash;
        string metadataUri;
        bool exists;
    }

    mapping(bytes32 => FileRecord) public files;
    uint256 public fileCount;

    event FileRegistered(bytes32 indexed fileId, address indexed owner, string metadataUri);

    function registerFile(
        bytes32 fileId,
        bytes32 manifestHash,
        bytes32 blockRoot,
        bytes32 fileHash,
        string calldata metadataUri
    ) external {
        require(!files[fileId].exists, "file already registered");

        files[fileId] = FileRecord({
            owner: msg.sender,
            manifestHash: manifestHash,
            blockRoot: blockRoot,
            fileHash: fileHash,
            metadataUri: metadataUri,
            exists: true
        });
        fileCount += 1;

        emit FileRegistered(fileId, msg.sender, metadataUri);
    }

    function fileExists(bytes32 fileId) external view returns (bool) {
        return files[fileId].exists;
    }
}
