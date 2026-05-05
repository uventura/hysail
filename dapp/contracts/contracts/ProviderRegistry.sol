// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract ProviderRegistry {
    struct Provider {
        address payoutAddress;
        string endpointUri;
        uint256 pricePerBlock;
        bool active;
    }

    mapping(address => Provider) public providers;
    uint256 public providerCount;

    event ProviderRegistered(address indexed provider, address indexed payoutAddress, string endpointUri, uint256 pricePerBlock);

    function registerProvider(
        string calldata endpointUri,
        uint256 pricePerBlock
    ) external {
        require(!providers[msg.sender].active, "provider already registered");

        providers[msg.sender] = Provider({
            payoutAddress: msg.sender,
            endpointUri: endpointUri,
            pricePerBlock: pricePerBlock,
            active: true
        });
        providerCount += 1;

        emit ProviderRegistered(msg.sender, msg.sender, endpointUri, pricePerBlock);
    }

    function isProviderActive(address provider) external view returns (bool) {
        return providers[provider].active;
    }
}
