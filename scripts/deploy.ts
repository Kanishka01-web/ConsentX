import { network } from "hardhat";

const { ethers } = await network.create();

const Consent = await ethers.getContractFactory("Consent");
const consent = await Consent.deploy();

await consent.waitForDeployment();

console.log("Consent deployed to:", await consent.getAddress());

