import { network } from "hardhat";

const { ethers } = await network.create();

const address = "0x8E09DD5af25C6752dB41DabfE36c8fFf3B4Ca9a9";

const consent = await ethers.getContractAt("Consent", address);

const [signer] = await ethers.getSigners();

console.log("Wallet:", await signer.getAddress());
console.log("Contract:", address);

const tx = await consent.grantConsent(
  1,
  1,
  3600
);

console.log("Transaction:", tx.hash);

await tx.wait();

console.log("Consent granted!");
