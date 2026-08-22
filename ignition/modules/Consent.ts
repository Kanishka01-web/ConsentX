import { buildModule } from "@nomicfoundation/hardhat-ignition/modules";
// This imports Hardhat Ignition's function for creating deployment modules.


const ConsentModule = buildModule("ConsentModule", (m) => {
    // Create a deployment module called "ConsentModule".
    //
    // Think of this file as instructions for Hardhat:
    // "Deploy my Consent contract."


    const consent = m.contract("Consent");
    // Tell Hardhat to deploy the Consent contract.
    //
    // Hardhat automatically finds:
    // contracts/Consent.sol


    return {
        consent,
    };
    // Return the deployed contract so Hardhat knows about it.
});


export default ConsentModule;
// Export the deployment instructions.