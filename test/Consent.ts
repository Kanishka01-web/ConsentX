// ============================================================
// CONSENT CONTRACT TESTS
// ============================================================
//
// These tests cover:
//
// 1. Granting consent
// 2. Revoking consent
// 3. Consent expiration
// 4. Re-consent
// 5. Access / audit logging
// 6. Input validation
//
// This file is written for Hardhat 3.
// ============================================================

import { expect } from "chai";
import { network } from "hardhat";

// Hardhat 3 provides ethers through a network connection.
const { ethers } = await network.connect();


// ============================================================
// HELPER: ASSERT TRANSACTION REVERTS
// ============================================================
//
// We intentionally use a small helper instead of:
//
//     .to.be.reverted
//
// because Hardhat 3 deprecates the legacy `reverted` matcher.
//
// This helper works by expecting the transaction to throw.
// ============================================================

async function expectRevert(
    transaction: Promise<unknown>,
    expectedMessage: string
): Promise<void> {

    let reverted = false;

    try {
        await transaction;
    } catch (error: any) {

        reverted = true;

        const message =
            error?.shortMessage ??
            error?.reason ??
            error?.message ??
            "";

        expect(message).to.include(expectedMessage);
    }

    expect(reverted).to.equal(true);
}


// ============================================================
// TEST SUITE
// ============================================================

describe("Consent", function () {

    // Contract instance.
    let consent: any;

    // Test wallets.
    let user: any;
    let anotherUser: any;


    // ============================================================
    // BEFORE EACH TEST
    // ============================================================

    beforeEach(async function () {

        // Get two local Hardhat accounts.
        //
        // user:
        //     person who gives consent.
        //
        // anotherUser:
        //     another application/service/wallet attempting
        //     to interact with the consent.

        [user, anotherUser] = await ethers.getSigners();


        // Get the Consent contract factory.

        const Consent = await ethers.getContractFactory("Consent");


        // Deploy a fresh contract for every test.

        consent = await Consent.deploy();


        // Wait for deployment to finish.

        await consent.waitForDeployment();
    });


    // ============================================================
    // HELPER: CREATE CONSENT AND RETURN ITS ID
    // ============================================================

    async function createConsent(
        purposeCode = 101,
        policyVersion = 1,
        duration = 3600
    ): Promise<string> {

        const tx = await consent
            .connect(user)
            .grantConsent(
                purposeCode,
                policyVersion,
                duration
            );

        const receipt = await tx.wait();


        // Find the ConsentGranted event.

        const event = receipt.logs.find(
            (log: any) =>
                log.fragment &&
                log.fragment.name === "ConsentGranted"
        );


        expect(event).to.not.equal(undefined);


        // First event parameter is consentId.

        return event.args[0];
    }


    // ============================================================
    // GRANTING CONSENT
    // ============================================================

    describe("Granting consent", function () {

        it("should create a consent successfully", async function () {

            const purposeCode = 101;
            const policyVersion = 1;
            const duration = 3600;


            // Grant consent.

            const tx = await consent
                .connect(user)
                .grantConsent(
                    purposeCode,
                    policyVersion,
                    duration
                );


            // Transaction must succeed.

            const receipt = await tx.wait();

            expect(receipt).to.not.equal(null);


            // User nonce should increase.

            expect(
                await consent.userNonce(user.address)
            ).to.equal(1);


            // Find ConsentGranted event.

            const event = receipt.logs.find(
                (log: any) =>
                    log.fragment &&
                    log.fragment.name === "ConsentGranted"
            );


            expect(event).to.not.equal(undefined);


            // Verify event data.

            expect(event.args[1]).to.equal(user.address);
            expect(event.args[2]).to.equal(purposeCode);
            expect(event.args[3]).to.equal(policyVersion);
        });


        it("should generate different IDs for different consents", async function () {

            // First consent.

            const tx1 = await consent
                .connect(user)
                .grantConsent(
                    101,
                    1,
                    3600
                );

            const receipt1 = await tx1.wait();


            // Second consent.

            const tx2 = await consent
                .connect(user)
                .grantConsent(
                    101,
                    1,
                    3600
                );

            const receipt2 = await tx2.wait();


            // Find both events.

            const event1 = receipt1.logs.find(
                (log: any) =>
                    log.fragment &&
                    log.fragment.name === "ConsentGranted"
            );

            const event2 = receipt2.logs.find(
                (log: any) =>
                    log.fragment &&
                    log.fragment.name === "ConsentGranted"
            );


            expect(event1).to.not.equal(undefined);
            expect(event2).to.not.equal(undefined);


            // IDs must be different.

            expect(event1.args[0]).to.not.equal(
                event2.args[0]
            );
        });


        it("should store the correct purpose and policy version", async function () {

            const tx = await consent
                .connect(user)
                .grantConsent(
                    101,
                    3,
                    3600
                );

            const receipt = await tx.wait();


            const event = receipt.logs.find(
                (log: any) =>
                    log.fragment &&
                    log.fragment.name === "ConsentGranted"
            );


            expect(event).to.not.equal(undefined);


            expect(event.args[2]).to.equal(101);
            expect(event.args[3]).to.equal(3);
        });


        it("should store the correct owner", async function () {

            const consentId = await createConsent();


            const record = await consent.getConsent(
                consentId
            );


            expect(record.user).to.equal(
                user.address
            );
        });


        it("should store the correct expiration time", async function () {

            const duration = 3600;

            const consentId = await createConsent(
                101,
                1,
                duration
            );


            const record = await consent.getConsent(
                consentId
            );


            expect(record.expiresAt).to.be.greaterThan(
                record.grantedAt
            );


            expect(
                Number(record.expiresAt) -
                Number(record.grantedAt)
            ).to.equal(duration);
        });
    });


    // ============================================================
    // REVOKING CONSENT
    // ============================================================

    describe("Revoking consent", function () {

        it("should allow the owner to revoke consent", async function () {

            // Create consent.

            const consentId = await createConsent();


            // The OWNER revokes the consent.

            const tx = await consent
                .connect(user)
                .revokeConsent(consentId);


            // Transaction must succeed.

            await tx.wait();


            // Read the updated consent.

            const record = await consent.getConsent(
                consentId
            );


            // It should be marked revoked.

            expect(record.revoked).to.equal(true);


            // revokedAt should contain a timestamp.

            expect(record.revokedAt).to.be.greaterThan(0);


            // Consent should no longer be valid.

            expect(
                await consent.isConsentValid(consentId)
            ).to.equal(false);
        });


        it("should NOT allow another user to revoke consent", async function () {

            // Create consent owned by user.

            const consentId = await createConsent();


            // anotherUser attempts to revoke it.
            //
            // This must fail.

            await expectRevert(
                consent
                    .connect(anotherUser)
                    .revokeConsent(consentId),
                "Not consent owner"
            );


            // Consent should still be valid.

            expect(
                await consent.isConsentValid(consentId)
            ).to.equal(true);
        });


        it("should preserve the original grant timestamp", async function () {

            // Create consent.

            const consentId = await createConsent();


            // Read before revocation.

            const before = await consent.getConsent(
                consentId
            );


            const originalGrantTime =
                before.grantedAt;


            // Revoke.

            await consent
                .connect(user)
                .revokeConsent(consentId);


            // Read after revocation.

            const after = await consent.getConsent(
                consentId
            );


            // Grant timestamp must remain unchanged.

            expect(after.grantedAt).to.equal(
                originalGrantTime
            );


            // Revocation timestamp must exist.

            expect(after.revokedAt).to.be.greaterThan(0);


            // Revoked flag must be true.

            expect(after.revoked).to.equal(true);
        });


        it("should NOT allow a consent to be revoked twice", async function () {

            const consentId = await createConsent();


            // First revocation succeeds.

            await consent
                .connect(user)
                .revokeConsent(consentId);


            // Second revocation must fail.

            await expectRevert(
                consent
                    .connect(user)
                    .revokeConsent(consentId),
                "Consent already revoked"
            );
        });


        it("should reject revoking a nonexistent consent", async function () {

            const fakeConsentId = ethers.id(
                "NONEXISTENT_CONSENT"
            );


            await expectRevert(
                consent
                    .connect(user)
                    .revokeConsent(fakeConsentId),
                "Consent does not exist"
            );
        });
    });


    // ============================================================
    // EXPIRATION
    // ============================================================

    describe("Expiration", function () {

        it("should become invalid after expiration", async function () {

            // Create a consent that lasts 60 seconds.

            const consentId = await createConsent(
                101,
                1,
                60
            );


            // It should initially be valid.

            expect(
                await consent.isConsentValid(consentId)
            ).to.equal(true);


            // Move blockchain time forward by 61 seconds.

            await ethers.provider.send(
                "evm_increaseTime",
                [61]
            );


            // Mine a new block.

            await ethers.provider.send(
                "evm_mine",
                []
            );


            // It should now be expired.

            expect(
                await consent.isConsentValid(consentId)
            ).to.equal(false);
        });


        it("should allow a consent with no expiry", async function () {

            // duration = 0 means no expiration.

            const consentId = await createConsent(
                101,
                1,
                0
            );


            const record = await consent.getConsent(
                consentId
            );


            // No expiration.

            expect(record.expiresAt).to.equal(0);


            // Still valid.

            expect(
                await consent.isConsentValid(consentId)
            ).to.equal(true);
        });
    });


    // ============================================================
    // RE-CONSENT
    // ============================================================

    describe("Re-consent", function () {

        it("should allow a user to create a new consent after revoking the old one", async function () {

            // First consent.

            const firstConsentId =
                await createConsent(
                    101,
                    1,
                    3600
                );


            // Revoke first consent.

            await consent
                .connect(user)
                .revokeConsent(
                    firstConsentId
                );


            // Create a second consent.

            const secondConsentId =
                await createConsent(
                    101,
                    2,
                    3600
                );


            // IDs must be different.

            expect(secondConsentId).to.not.equal(
                firstConsentId
            );


            // New consent must be valid.

            expect(
                await consent.isConsentValid(
                    secondConsentId
                )
            ).to.equal(true);


            // Old consent must remain invalid.

            expect(
                await consent.isConsentValid(
                    firstConsentId
                )
            ).to.equal(false);
        });


        it("should increment the user nonce for each consent", async function () {

            expect(
                await consent.userNonce(
                    user.address
                )
            ).to.equal(0);


            await createConsent();


            expect(
                await consent.userNonce(
                    user.address
                )
            ).to.equal(1);


            await createConsent();


            expect(
                await consent.userNonce(
                    user.address
                )
            ).to.equal(2);
        });
    });


    // ============================================================
    // ACCESS / AUDIT LOGGING
    // ============================================================

    describe("Access logging", function () {

        it("should log a data access when consent is valid", async function () {

            // Create valid consent.

            const consentId =
                await createConsent();


            // Never put actual health data on-chain.
            //
            // We only store a hash/identifier describing
            // the category of data accessed.

            const dataType =
                ethers.id("HEALTH_RECORD");


            // anotherUser accesses data under the consent.
            //
            // If logAccess succeeds, the test continues.
            //
            // IMPORTANT:
            // We do NOT use `.to.not.be.reverted`.
            // That matcher is deprecated in Hardhat 3.

            const tx = await consent
                .connect(anotherUser)
                .logAccess(
                    consentId,
                    dataType
                );


            // Successful transaction.

            await tx.wait();
        });


        it("should emit DataAccessed when data is accessed", async function () {

            const consentId =
                await createConsent();


            const dataType =
                ethers.id("HEALTH_RECORD");


            const tx = await consent
                .connect(anotherUser)
                .logAccess(
                    consentId,
                    dataType
                );


            const receipt = await tx.wait();


            // Find DataAccessed event.

            const event = receipt.logs.find(
                (log: any) =>
                    log.fragment &&
                    log.fragment.name === "DataAccessed"
            );


            expect(event).to.not.equal(undefined);


            // Event arguments:
            //
            // 0 = consentId
            // 1 = accessor
            // 2 = dataType
            // 3 = accessedAt

            expect(event.args[0]).to.equal(
                consentId
            );

            expect(event.args[1]).to.equal(
                anotherUser.address
            );

            expect(event.args[2]).to.equal(
                dataType
            );

            expect(event.args[3]).to.be.greaterThan(0);
        });


        it("should NOT allow data access after consent is revoked", async function () {

            // Create consent.

            const consentId =
                await createConsent();


            // Revoke it.

            await consent
                .connect(user)
                .revokeConsent(
                    consentId
                );


            const dataType =
                ethers.id("HEALTH_RECORD");


            // Access should now fail.

            await expectRevert(
                consent
                    .connect(anotherUser)
                    .logAccess(
                        consentId,
                        dataType
                    ),
                "Consent is not valid"
            );
        });


        it("should NOT allow data access after consent expires", async function () {

            // Create a 60-second consent.

            const consentId =
                await createConsent(
                    101,
                    1,
                    60
                );


            // Move time past expiration.

            await ethers.provider.send(
                "evm_increaseTime",
                [61]
            );

            await ethers.provider.send(
                "evm_mine",
                []
            );


            const dataType =
                ethers.id("HEALTH_RECORD");


            // Access should fail.

            await expectRevert(
                consent
                    .connect(anotherUser)
                    .logAccess(
                        consentId,
                        dataType
                    ),
                "Consent is not valid"
            );
        });


        it("should reject access to a nonexistent consent", async function () {

            const fakeConsentId =
                ethers.id("NONEXISTENT_CONSENT");


            const dataType =
                ethers.id("HEALTH_RECORD");


            await expectRevert(
                consent
                    .connect(anotherUser)
                    .logAccess(
                        fakeConsentId,
                        dataType
                    ),
                "Consent is not valid"
            );
        });
    });


    // ============================================================
    // INPUT VALIDATION
    // ============================================================

    describe("Input validation", function () {

        it("should reject purpose code 0", async function () {

            await expectRevert(
                consent
                    .connect(user)
                    .grantConsent(
                        0,
                        1,
                        3600
                    ),
                "Invalid purpose"
            );
        });


        it("should reject policy version 0", async function () {

            await expectRevert(
                consent
                    .connect(user)
                    .grantConsent(
                        101,
                        0,
                        3600
                    ),
                "Invalid policy version"
            );
        });
    });
});