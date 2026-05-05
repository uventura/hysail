const fs = require("fs");
const path = require("path");
const hre = require("hardhat");

async function main() {
  const [deployer] = await hre.ethers.getSigners();

  const fileRegistryFactory = await hre.ethers.getContractFactory("FileRegistry");
  const fileRegistry = await fileRegistryFactory.deploy();
  await fileRegistry.waitForDeployment();

  const providerRegistryFactory = await hre.ethers.getContractFactory("ProviderRegistry");
  const providerRegistry = await providerRegistryFactory.deploy();
  await providerRegistry.waitForDeployment();

  const downloadManagerFactory = await hre.ethers.getContractFactory("DownloadManager");
  const downloadManager = await downloadManagerFactory.deploy(
    await fileRegistry.getAddress(),
    await providerRegistry.getAddress()
  );
  await downloadManager.waitForDeployment();

  const deployments = {
    network: "localhost",
    deployer: deployer.address,
    fileRegistry: await fileRegistry.getAddress(),
    providerRegistry: await providerRegistry.getAddress(),
    downloadManager: await downloadManager.getAddress()
  };

  const outputs = [
    path.resolve(__dirname, "../../apps/web/src/generated/contracts.json"),
    path.resolve(__dirname, "../../packages/shared/deployments/local.json")
  ];

  for (const outputPath of outputs) {
    fs.mkdirSync(path.dirname(outputPath), { recursive: true });
    fs.writeFileSync(outputPath, JSON.stringify(deployments, null, 2));
  }

  console.log(JSON.stringify(deployments, null, 2));
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
