# HySail DApp Demo

This folder introduces a runnable local DApp example following the proposed structure:

- contracts: local smart contracts with a minimal file registry, provider registry, and download manager
- apps/web: browser UI for the sample flow
- services/provider_mock: HTTP provider serving one sample block
- services/reconstructor: off-chain reconstruction script
- packages/shared: shared sample manifest, block, contract metadata, and deployment output

Recommended runtime:

1. Node 18 or newer.
2. Warning: The current workspace has Node 16 available, and the sample still compiles and runs locally with a Hardhat warning.
3. Python uses the existing project virtual environment.

## Structure

```text
 dapp/
   contracts/
   apps/web/
   services/provider_mock/
   services/reconstructor/
   packages/shared/
```

## Example flow

1. Start a local Hardhat node.
2. Deploy the sample contracts.
3. Start the mock provider.
4. Start the web app.
5. Register the sample file and provider in the browser.
6. Request a sample download job.
7. Run the reconstructor to challenge the provider, download the block only if it is consistent, and settle the job.
8. If the consistency check fails, the reconstructor rejects the job and refunds the requester instead of paying the provider.

## Commands

### 1. Install contract dependencies

```bash
cd dapp/contracts
npm install
```

### 2. Start the local chain

```bash
cd dapp/contracts
npm run node
```

### 3. Deploy contracts

In another terminal:

```bash
cd dapp/contracts
npm run compile
npm run deploy:local
```

This writes deployed addresses to:

- apps/web/src/generated/contracts.json
- packages/shared/deployments/local.json

### 4. Start the provider mock

```bash
/home/ualtu/dev/git/hysail/hysail_env/bin/python dapp/services/provider_mock/main.py
```

### 5. Install and run the web app

```bash
cd dapp/apps/web
npm install
npm run dev
```

Open the printed local URL, usually http://127.0.0.1:5173.

### 6. Run the reconstructor

After requesting a job in the browser:

```bash
/home/ualtu/dev/git/hysail/hysail_env/bin/python dapp/services/reconstructor/main.py
```

The reconstructor now performs three steps:

1. Challenges the provider using the HySail-style consistency check before downloading the block.
2. Downloads and hashes the block only if the challenge matches the manifest MACs.
3. Accepts and finalizes the job on-chain, or rejects it with a refund if validation fails.

The reconstructed file is written to output/reconstructed_sample.txt.

## Notes

1. Warning: The browser uses a development-only private key that matches the standard local Hardhat mnemonic.
2. This is only for local demonstration.
3. The on-chain example is intentionally small: one file, one provider, one block.
4. The off-chain reconstruction now validates a challenge response before downloading and only settles the chain after the payload hash matches.
