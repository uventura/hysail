DOWNLOAD_MANAGER_ABI = [
    {
        "inputs": [{"internalType": "bytes32", "name": "fileId", "type": "bytes32"}],
        "name": "requestDownload",
        "outputs": [],
        "stateMutability": "payable",
        "type": "function",
    },
    {
        "inputs": [{"internalType": "uint256", "name": "jobId", "type": "uint256"}],
        "name": "jobs",
        "outputs": [
            {"internalType": "bytes32", "name": "fileId", "type": "bytes32"},
            {"internalType": "address", "name": "requester", "type": "address"},
            {"internalType": "uint256", "name": "budget", "type": "uint256"},
            {"internalType": "uint256", "name": "spent", "type": "uint256"},
            {"internalType": "bytes32", "name": "resultHash", "type": "bytes32"},
            {"internalType": "bool", "name": "finalized", "type": "bool"},
        ],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "jobCount",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [
            {"internalType": "uint256", "name": "jobId", "type": "uint256"},
            {"internalType": "bytes32", "name": "blockId", "type": "bytes32"},
            {"internalType": "address", "name": "provider", "type": "address"},
            {"internalType": "uint256", "name": "priceWei", "type": "uint256"},
        ],
        "name": "acceptBlock",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "inputs": [
            {"internalType": "uint256", "name": "jobId", "type": "uint256"},
            {"internalType": "bytes32", "name": "resultHash", "type": "bytes32"},
        ],
        "name": "finalizeJob",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "inputs": [{"internalType": "uint256", "name": "jobId", "type": "uint256"}],
        "name": "rejectJob",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    },
]
