import { ethers } from "ethers";
import sampleManifest from "../../../packages/shared/example/sample_manifest.json";
import deployments from "./generated/contracts.json";
import {
  DOWNLOAD_MANAGER_ABI,
  FILE_REGISTRY_ABI,
  PROVIDER_REGISTRY_ABI,
} from "../../../packages/shared/src/contracts.js";
import "./style.css";

const DEV_PRIVATE_KEY =
  "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80";
const RPC_URL = "http://127.0.0.1:8545";
const JOB_BUDGET_WEI = ethers.parseEther("0.01");

const app = document.querySelector("#app");

app.innerHTML = `
  <main>
    <section class="hero">
      <span>Local demo for the proposed HySail DApp structure</span>
      <h1>Register, request, reconstruct.</h1>
      <p>
        This small example uses a local Hardhat chain, a mock storage provider, and a reconstructor script.
        The browser uses a development-only wallet wired to the local node.
      </p>
    </section>

    <section class="grid">
      <article class="card">
        <h2>Chain</h2>
        <p>Use the buttons in order after running the local node and deploy script. The reconstructor validates blocks off-chain before settlement.</p>
        <button id="refresh">Refresh counters</button>
        <button id="register-file" class="secondary">Register sample file</button>
        <button id="register-provider" class="secondary">Register provider</button>
        <button id="request-job" class="accent">Request download job</button>
        <div class="kpis">
          <div class="kpi"><span>Files</span><strong id="files">0</strong></div>
          <div class="kpi"><span>Providers</span><strong id="providers">0</strong></div>
          <div class="kpi"><span>Jobs</span><strong id="jobs">0</strong></div>
          <div class="kpi"><span>Signer</span><strong id="signer">-</strong></div>
        </div>
        <small class="code">RPC: http://127.0.0.1:8545</small>
      </article>

      <article class="card">
        <h2>Sample manifest</h2>
        <p>All services use the same sample manifest and sample block stored in the shared package.</p>
        <pre id="manifest"></pre>
      </article>

      <article class="card" style="grid-column: 1 / -1;">
        <h2>Activity log</h2>
        <pre id="log"></pre>
      </article>
    </section>
  </main>
`;

const provider = new ethers.JsonRpcProvider(RPC_URL);
const wallet = new ethers.Wallet(DEV_PRIVATE_KEY, provider);
const fileId = ethers.id(sampleManifest.fileId);
const manifestHash = ethers.id(JSON.stringify(sampleManifest));
const blockRoot = ethers.id(sampleManifest.blockHash);
const fileHash = `0x${sampleManifest.originalFileHash}`;

const zeroAddress = "0x0000000000000000000000000000000000000000";

const log = document.querySelector("#log");
const manifestEl = document.querySelector("#manifest");
manifestEl.textContent = JSON.stringify(sampleManifest, null, 2);

function writeLog(message) {
  log.textContent = `${new Date().toLocaleTimeString()} ${message}\n${log.textContent}`;
}

function getContracts() {
  if (
    deployments.fileRegistry === zeroAddress ||
    deployments.providerRegistry === zeroAddress ||
    deployments.downloadManager === zeroAddress
  ) {
    throw new Error("Contracts are not deployed yet. Run the deploy script first.");
  }

  return {
    fileRegistry: new ethers.Contract(deployments.fileRegistry, FILE_REGISTRY_ABI, wallet),
    providerRegistry: new ethers.Contract(deployments.providerRegistry, PROVIDER_REGISTRY_ABI, wallet),
    downloadManager: new ethers.Contract(deployments.downloadManager, DOWNLOAD_MANAGER_ABI, wallet),
  };
}

async function refreshCounters() {
  const signerNode = document.querySelector("#signer");
  signerNode.textContent = `${wallet.address.slice(0, 6)}...${wallet.address.slice(-4)}`;

  try {
    const { fileRegistry, providerRegistry, downloadManager } = getContracts();
    const [files, providers, jobs] = await Promise.all([
      fileRegistry.fileCount(),
      providerRegistry.providerCount(),
      downloadManager.jobCount(),
    ]);

    document.querySelector("#files").textContent = files.toString();
    document.querySelector("#providers").textContent = providers.toString();
    document.querySelector("#jobs").textContent = jobs.toString();
    writeLog("Counters refreshed.");
  } catch (error) {
    writeLog(`Refresh failed: ${error.message}`);
  }
}

async function sendTransaction(label, action) {
  try {
    const tx = await action();
    writeLog(`${label}: tx submitted ${tx.hash}`);
    await tx.wait();
    writeLog(`${label}: tx confirmed.`);
    await refreshCounters();
  } catch (error) {
    writeLog(`${label}: ${error.shortMessage || error.message}`);
  }
}

async function registerFile() {
  const { fileRegistry } = getContracts();
  await sendTransaction("Register file", () =>
    fileRegistry.registerFile(
      fileId,
      manifestHash,
      blockRoot,
      fileHash,
      sampleManifest.metadataUri
    )
  );
}

async function registerProvider() {
  const { providerRegistry } = getContracts();
  await sendTransaction("Register provider", () =>
    providerRegistry.registerProvider(
      sampleManifest.providerEndpoint,
      BigInt(sampleManifest.samplePriceWei)
    )
  );
}

async function requestJob() {
  const { downloadManager } = getContracts();
  await sendTransaction("Request job", () =>
    downloadManager.requestDownload(fileId, { value: JOB_BUDGET_WEI })
  );

  writeLog("Run the reconstructor service to validate the packet, pay the provider, and finalize or reject the job.");
}

document.querySelector("#refresh").addEventListener("click", refreshCounters);
document.querySelector("#register-file").addEventListener("click", registerFile);
document.querySelector("#register-provider").addEventListener("click", registerProvider);
document.querySelector("#request-job").addEventListener("click", requestJob);

refreshCounters();
