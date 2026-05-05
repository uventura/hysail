const assert = require("node:assert/strict");

const FILE_ID = ethers.id("sample-file");
const BLOCK_ID = ethers.id("sample-block-1");
const MANIFEST_HASH = ethers.id("sample-manifest");
const BLOCK_ROOT = ethers.id("sample-block-root");
const FILE_HASH = `0x${"11".repeat(32)}`;
const PRICE_WEI = ethers.parseEther("0.001");
const BUDGET_WEI = ethers.parseEther("0.01");

async function deployFixture() {
  const [requester, provider, outsider] = await ethers.getSigners();

  const fileRegistryFactory = await ethers.getContractFactory("FileRegistry");
  const fileRegistry = await fileRegistryFactory.deploy();
  await fileRegistry.waitForDeployment();

  const providerRegistryFactory = await ethers.getContractFactory("ProviderRegistry");
  const providerRegistry = await providerRegistryFactory.deploy();
  await providerRegistry.waitForDeployment();

  const downloadManagerFactory = await ethers.getContractFactory("DownloadManager");
  const downloadManager = await downloadManagerFactory.deploy(
    await fileRegistry.getAddress(),
    await providerRegistry.getAddress()
  );
  await downloadManager.waitForDeployment();

  await fileRegistry.connect(requester).registerFile(
    FILE_ID,
    MANIFEST_HASH,
    BLOCK_ROOT,
    FILE_HASH,
    "http://127.0.0.1:8000/manifest"
  );
  await providerRegistry.connect(provider).registerProvider(
    "http://127.0.0.1:8000",
    PRICE_WEI
  );
  await downloadManager.connect(requester).requestDownload(FILE_ID, { value: BUDGET_WEI });

  return { downloadManager, requester, provider, outsider };
}

describe("DownloadManager", function () {
  it("test_accept_block_requires_requester_authorization", async function () {
    const { downloadManager, provider, requester } = await deployFixture();

    let reverted = false;
    try {
      await downloadManager.connect(provider).acceptBlock(
        1,
        BLOCK_ID,
        provider.address,
        PRICE_WEI
      );
    } catch (error) {
      reverted = error.message.includes("only requester");
    }

    assert.equal(reverted, true);

    const providerBalanceBefore = await ethers.provider.getBalance(provider.address);
    await downloadManager.connect(requester).acceptBlock(
      1,
      BLOCK_ID,
      provider.address,
      PRICE_WEI
    );
    const providerBalanceAfter = await ethers.provider.getBalance(provider.address);

    assert.equal(providerBalanceAfter - providerBalanceBefore, PRICE_WEI);
  });

  it("test_reject_job_refunds_without_paying_provider", async function () {
    const { downloadManager, requester, provider } = await deployFixture();

    const providerBalanceBefore = await ethers.provider.getBalance(provider.address);
    await downloadManager.connect(requester).rejectJob(1);
    const providerBalanceAfter = await ethers.provider.getBalance(provider.address);

    const job = await downloadManager.jobs(1);
    const contractBalance = await ethers.provider.getBalance(await downloadManager.getAddress());

    assert.equal(job.finalized, true);
    assert.equal(job.spent, 0n);
    assert.equal(contractBalance, 0n);
    assert.equal(providerBalanceAfter, providerBalanceBefore);
  });
});
