export const FILE_REGISTRY_ABI = [
  "function registerFile(bytes32 fileId, bytes32 manifestHash, bytes32 blockRoot, bytes32 fileHash, string metadataUri)",
  "function fileCount() view returns (uint256)"
];

export const PROVIDER_REGISTRY_ABI = [
  "function registerProvider(string endpointUri, uint256 pricePerBlock)",
  "function providerCount() view returns (uint256)"
];

export const DOWNLOAD_MANAGER_ABI = [
  "function requestDownload(bytes32 fileId) payable",
  "function acceptBlock(uint256 jobId, bytes32 blockId, uint256 priceWei)",
  "function finalizeJob(uint256 jobId, bytes32 resultHash)",
  "function jobCount() view returns (uint256)"
];
