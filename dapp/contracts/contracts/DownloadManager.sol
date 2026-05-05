// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

interface IFileRegistry {
    function fileExists(bytes32 fileId) external view returns (bool);
}

interface IProviderRegistry {
    function isProviderActive(address provider) external view returns (bool);
}

contract DownloadManager {
    struct Job {
        bytes32 fileId;
        address requester;
        uint256 budget;
        uint256 spent;
        bytes32 resultHash;
        bool finalized;
    }

    IFileRegistry public immutable fileRegistry;
    IProviderRegistry public immutable providerRegistry;
    uint256 public jobCount;

    mapping(uint256 => Job) public jobs;
    mapping(uint256 => mapping(bytes32 => bool)) public claimedBlocks;

    event DownloadRequested(uint256 indexed jobId, bytes32 indexed fileId, address indexed requester, uint256 budget);
    event BlockAccepted(uint256 indexed jobId, bytes32 indexed blockId, address indexed provider, uint256 priceWei);
    event JobFinalized(uint256 indexed jobId, bytes32 resultHash, uint256 refundWei);
    event JobRejected(uint256 indexed jobId, uint256 refundWei);

    constructor(address fileRegistryAddress, address providerRegistryAddress) {
        fileRegistry = IFileRegistry(fileRegistryAddress);
        providerRegistry = IProviderRegistry(providerRegistryAddress);
    }

    function requestDownload(bytes32 fileId) external payable {
        require(msg.value > 0, "budget required");
        require(fileRegistry.fileExists(fileId), "unknown file");

        jobCount += 1;
        jobs[jobCount] = Job({
            fileId: fileId,
            requester: msg.sender,
            budget: msg.value,
            spent: 0,
            resultHash: bytes32(0),
            finalized: false
        });

        emit DownloadRequested(jobCount, fileId, msg.sender, msg.value);
    }

    function acceptBlock(uint256 jobId, bytes32 blockId, address provider, uint256 priceWei) external {
        Job storage job = jobs[jobId];

        require(job.requester != address(0), "unknown job");
        require(!job.finalized, "job finalized");
        require(msg.sender == job.requester, "only requester");
        require(providerRegistry.isProviderActive(provider), "inactive provider");
        require(!claimedBlocks[jobId][blockId], "block already claimed");
        require(job.spent + priceWei <= job.budget, "insufficient budget");

        claimedBlocks[jobId][blockId] = true;
        job.spent += priceWei;

        (bool paid, ) = payable(provider).call{value: priceWei}("");
        require(paid, "provider payment failed");

        emit BlockAccepted(jobId, blockId, provider, priceWei);
    }

    function finalizeJob(uint256 jobId, bytes32 resultHash) external {
        Job storage job = jobs[jobId];

        require(job.requester != address(0), "unknown job");
        require(!job.finalized, "job finalized");
        require(msg.sender == job.requester, "only requester");

        job.finalized = true;
        job.resultHash = resultHash;

        uint256 refund = _refundRemainingBudget(job);

        emit JobFinalized(jobId, resultHash, refund);
    }

    function rejectJob(uint256 jobId) external {
        Job storage job = jobs[jobId];

        require(job.requester != address(0), "unknown job");
        require(!job.finalized, "job finalized");
        require(msg.sender == job.requester, "only requester");

        job.finalized = true;

        uint256 refund = _refundRemainingBudget(job);

        emit JobRejected(jobId, refund);
    }

    function _refundRemainingBudget(Job storage job) private returns (uint256 refund) {
        refund = job.budget - job.spent;
        if (refund > 0) {
            (bool paid, ) = payable(job.requester).call{value: refund}("");
            require(paid, "refund failed");
        }
    }
}
