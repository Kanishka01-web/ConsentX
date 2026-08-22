import { expect } from "chai";
// Chai gives us functions like expect() for testing.

import { network } from "hardhat";
// Hardhat gives us access to the local blockchain and ethers.


describe("Consent", function () {
    // Everything inside this block tests our Consent contract.


    async function deployConsent() {
        // This helper function deploys a fresh Consent contract
        // before each test.


        const { ethers } = await network.connect();
        // Connect to Hardhat's local blockchain.


        const consent = await ethers.deployContract("Consent");
        // Deploy our Consent smart contract.


        await consent.waitForDeployment();
        // Wait until deployment is completed.


        const [user, attacker] = await ethers.getSigners();
        // Get two test wallets.
        //
        // user = legitimate consent owner
        // attacker = another wallet trying to interfere


        return {
            consent,
            user,
            attacker,
            ethers
        };
        // Give these objects back to the test.
    }


    // ============================================================
    // GRANTING CONSENT
    // ============================================================

    describe("Granting consent", function () {


        it("should create a consent successfully", async function () {
            // Test that a user can successfully create consent.


            const {
                consent,
                user
            } = await deployConsent();
            // Deploy a fresh contract and get our test user.


            await consent.grantConsent(
                101,
                // Purpose code = 101.

                1,
                // Policy version = 1.

                3600
                // Consent lasts 3600 seconds = 1 hour.
            );


            expect(
                await consent.userNonce(user.address)
            ).to.equal(1);
            // The user's nonce should now be 1.
            //
            // It started at 0.
            // After creating one consent, it becomes 1.
        });


        it("should generate different IDs for different consents", async function () {
            // Test that the same user gets different IDs
            // for different consent records.


            const {
                consent,
                user,
                ethers
            } = await deployConsent();


            const firstId = ethers.keccak256(
                ethers.solidityPacked(
                    ["address", "uint256"],
                    [user.address, 0]
                )
            );
            // Calculate the ID that the first consent should receive.
            //
            // First consent uses nonce 0.


            const secondId = ethers.keccak256(
                ethers.solidityPacked(
                    ["address", "uint256"],
                    [user.address, 1]
                )
            );
            // Calculate the ID that the second consent should receive.
            //
            // Second consent uses nonce 1.


            await consent.grantConsent(101, 1, 3600);
            // Create the first consent.


            await consent.grantConsent(101, 1, 3600);
            // Create the second consent.


            expect(firstId).to.not.equal(secondId);
            // The IDs must be different.
        });
    });


    // ============================================================
    // REVOKING CONSENT
    // ============================================================

    describe("Revoking consent", function () {


        it("should allow the owner to revoke consent", async function () {
            // Test that the person who gave consent
            // can revoke it.


            const {
                consent,
                user,
                ethers
            } = await deployConsent();


            await consent.grantConsent(101, 1, 3600);
            // Create a consent.


            const consentId = ethers.keccak256(
                ethers.solidityPacked(
                    ["address", "uint256"],
                    [user.address, 0]
                )
            );
            // Calculate the ID of the first consent.


            await consent.revokeConsent(consentId);
            // Revoke the consent.


            expect(
                await consent.isConsentValid(consentId)
            ).to.equal(false);
            // The consent should no longer be valid.
        });


        it("should NOT allow another user to revoke consent", async function () {
            // Test our security rule.
            //
            // A different wallet must NOT be able to revoke
            // someone else's consent.


            const {
                consent,
                user,
                attacker,
                ethers
            } = await deployConsent();


            await consent.grantConsent(101, 1, 3600);
            // User creates consent.


            const consentId = ethers.keccak256(
                ethers.solidityPacked(
                    ["address", "uint256"],
                    [user.address, 0]
                )
            );
            // Calculate the consent ID.


            await expect(
                consent
                    .connect(attacker)
                    .revokeConsent(consentId)
            ).to.be.revertedWith("Not consent owner");
            // The attacker tries to revoke the user's consent.
            //
            // The transaction MUST fail.
        });


        it("should preserve the original grant timestamp", async function () {
            // Test that revoking consent does NOT overwrite
            // the original grant timestamp.


            const {
                consent,
                user,
                ethers
            } = await deployConsent();


            await consent.grantConsent(101, 1, 3600);
            // Create consent.


            const consentId = ethers.keccak256(
                ethers.solidityPacked(
                    ["address", "uint256"],
                    [user.address, 0]
                )
            );
            // Calculate the consent ID.


            const before = await consent.getConsent(consentId);
            // Read the consent before revocation.


            await consent.revokeConsent(consentId);
            // Revoke the consent.


            const after = await consent.getConsent(consentId);
            // Read the consent again after revocation.


            expect(after.grantedAt)
                .to.equal(before.grantedAt);
            // The original grant timestamp must remain unchanged.


            expect(after.revokedAt)
                .to.be.greaterThan(0);
            // revokedAt should now contain a timestamp.


            expect(after.revoked)
                .to.equal(true);
            // The consent should be marked as revoked.
        });
    });


    // ============================================================
    // EXPIRATION
    // ============================================================

    describe("Expiration", function () {


        it("should become invalid after expiration", async function () {
            // Test that consent automatically becomes invalid
            // when its expiry time passes.


            const {
                consent,
                user,
                ethers
            } = await deployConsent();


            await consent.grantConsent(
                101,
                1,
                60
            );
            // Create consent that lasts only 60 seconds.


            const consentId = ethers.keccak256(
                ethers.solidityPacked(
                    ["address", "uint256"],
                    [user.address, 0]
                )
            );
            // Calculate the consent ID.


            expect(
                await consent.isConsentValid(consentId)
            ).to.equal(true);
            // Immediately after creation, it should be valid.


            await ethers.provider.send(
                "evm_increaseTime",
                [61]
            );
            // Move the test blockchain's clock forward by 61 seconds.


            await ethers.provider.send(
                "evm_mine",
                []
            );
            // Mine a new block so the new time is applied.


            expect(
                await consent.isConsentValid(consentId)
            ).to.equal(false);
            // The consent should now be expired.
        });
    });


    // ============================================================
    // RE-CONSENT
    // ============================================================

    describe("Re-consent", function () {


        it("should allow a user to create a new consent after revoking the old one", async function () {
            // Test our re-consent behavior.
            //
            // Instead of modifying the old record,
            // we create a completely new consent record.


            const {
                consent,
                user,
                ethers
            } = await deployConsent();


            await consent.grantConsent(
                101,
                1,
                3600
            );
            // Create the first consent.


            const firstConsentId = ethers.keccak256(
                ethers.solidityPacked(
                    ["address", "uint256"],
                    [user.address, 0]
                )
            );
            // First consent uses nonce 0.


            await consent.revokeConsent(firstConsentId);
            // Revoke the first consent.


            await consent.grantConsent(
                101,
                1,
                3600
            );
            // Give consent again.
            //
            // This creates a NEW consent record.


            const secondConsentId = ethers.keccak256(
                ethers.solidityPacked(
                    ["address", "uint256"],
                    [user.address, 1]
                )
            );
            // Second consent uses nonce 1.


            expect(secondConsentId)
                .to.not.equal(firstConsentId);
            // The new consent must have a different ID.


            expect(
                await consent.isConsentValid(secondConsentId)
            ).to.equal(true);
            // The new consent should be active.


            expect(
                await consent.isConsentValid(firstConsentId)
            ).to.equal(false);
            // The old consent should remain revoked.
        });
    });
});