// SPDX-License-Identifier: MIT
// This tells people that this code uses the MIT open-source license.

pragma solidity ^0.8.28;
// This contract uses Solidity version 0.8.28.


contract Consent {
    // Everything inside this contract controls ConsentX's consent records.


    // ============================================================
    // DATA STRUCTURE
    // ============================================================

    struct ConsentRecord {
        // A struct groups all information about ONE consent together.

        address user;
        // The wallet address that gave this consent.

        uint16 purposeCode;
        // A small number representing the purpose of the consent.
        //
        // Example:
        // 101 = Healthcare
        // 102 = Financial
        // 103 = Marketing
        //
        // The actual mapping of numbers to purposes can be
        // maintained by the backend/frontend.

        uint16 policyVersion;
        // The version of the policy that the user agreed to.
        //
        // Example:
        // 1 = first version of the policy
        // 2 = updated policy

        uint64 grantedAt;
        // The blockchain timestamp when consent was granted.

        uint64 expiresAt;
        // The blockchain timestamp when consent expires.
        //
        // 0 means the consent has no expiry.

        uint64 revokedAt;
        // The blockchain timestamp when consent was revoked.
        //
        // 0 means it has never been revoked.

        bool revoked;
        // false = the user has not revoked it.
        // true = the user has revoked it.
    }


    // ============================================================
    // STORAGE
    // ============================================================

    mapping(address => uint256) public userNonce;
    // Each wallet gets its own counter.
    //
    // Example:
    //
    // Nirali's nonce = 0
    // First consent → use nonce 0
    // Then nonce becomes 1
    //
    // Second consent → use nonce 1
    //
    // This helps create unique consent IDs.


    mapping(bytes32 => ConsentRecord) private consents;
    // Stores all consent records.
    //
    // bytes32 is used as the consent ID.
    //
    // Example:
    //
    // consentId → ConsentRecord
    //
    // We keep this mapping private and provide functions to read it.


    // ============================================================
    // EVENTS
    // ============================================================

    event ConsentGranted(
        bytes32 indexed consentId,
        address indexed user,
        uint16 purposeCode,
        uint16 policyVersion,
        uint64 grantedAt,
        uint64 expiresAt
    );
    // This event is emitted whenever someone grants consent.
    //
    // The frontend/backend can listen for this event.


    event ConsentRevoked(
        bytes32 indexed consentId,
        address indexed user,
        uint64 revokedAt
    );
    // This event is emitted whenever someone revokes consent.


    // ============================================================
    // GRANT CONSENT
    // ============================================================

    function grantConsent(
        uint16 purposeCode,
        uint16 policyVersion,
        uint64 durationSeconds
    ) external returns (bytes32 consentId) {
        // This function creates a new consent.
        //
        // durationSeconds tells us how long the consent should last.
        //
        // Example:
        // 3600 seconds = 1 hour
        //
        // durationSeconds = 0 means no expiry.


        require(
            purposeCode != 0,
            "Invalid purpose"
        );
        // We don't allow purpose code 0.


        require(
            policyVersion != 0,
            "Invalid policy version"
        );
        // Policy version must be greater than 0.


        uint256 nonce = userNonce[msg.sender];
        // Get the current nonce for the wallet calling this function.
        //
        // msg.sender = the wallet that is currently calling the contract.


        consentId = keccak256(
            abi.encodePacked(
                msg.sender,
                nonce
            )
        );
        // Generate the consent ID.
        //
        // We combine:
        //
        //     user's wallet address
        //     user's nonce
        //
        // Then hash them using keccak256.
        //
        // The user does NOT choose the ID.
        //
        // This prevents someone else from simply choosing
        // a predictable consent ID and occupying it first.


        userNonce[msg.sender] = nonce + 1;
        // Increase the user's nonce.
        //
        // This means the next consent will get a different ID.


        uint64 grantedAt = uint64(block.timestamp);
        // Get the current blockchain timestamp.
        //
        // This is saved as the original grant time.
        //
        // We will NEVER overwrite this when consent is revoked.


        uint64 expiresAt = 0;
        // Start with no expiry.


        if (durationSeconds > 0) {
            // If the user gave us an expiry duration...

            expiresAt = grantedAt + durationSeconds;
            // Calculate the exact expiry time.
        }


        consents[consentId] = ConsentRecord({
            user: msg.sender,
            // Save who gave the consent.

            purposeCode: purposeCode,
            // Save the purpose code.

            policyVersion: policyVersion,
            // Save the policy version.

            grantedAt: grantedAt,
            // Save the original grant timestamp.

            expiresAt: expiresAt,
            // Save the expiry timestamp.

            revokedAt: 0,
            // It has not been revoked yet.

            revoked: false
            // It starts as not revoked.
        });


        emit ConsentGranted(
            consentId,
            msg.sender,
            purposeCode,
            policyVersion,
            grantedAt,
            expiresAt
        );
        // Create a blockchain event saying:
        //
        // "This consent was granted."
    }


    // ============================================================
    // REVOKE CONSENT
    // ============================================================

    function revokeConsent(
        bytes32 consentId
    ) external {
        // This function lets a user revoke their consent.


        ConsentRecord storage consent = consents[consentId];
        // Find the consent using its ID.
        //
        // "storage" means we are working directly with
        // the data stored on the blockchain.


        require(
            consent.user != address(0),
            "Consent does not exist"
        );
        // Make sure the consent actually exists.


        require(
            consent.user == msg.sender,
            "Not consent owner"
        );
        // SECURITY CHECK:
        //
        // Only the wallet that originally gave the consent
        // can revoke it.
        //
        // Another user cannot revoke it.


        require(
            !consent.revoked,
            "Consent already revoked"
        );
        // Prevent someone from revoking the same consent twice.


        consent.revoked = true;
        // Mark the consent as revoked.


        consent.revokedAt = uint64(block.timestamp);
        // Save the exact time of revocation.
        //
        // IMPORTANT:
        // We do NOT change grantedAt.
        //
        // This preserves our audit history.


        emit ConsentRevoked(
            consentId,
            msg.sender,
            consent.revokedAt
        );
        // Record the revocation event on the blockchain.
    }


    // ============================================================
    // CHECK CONSENT VALIDITY
    // ============================================================

    function isConsentValid(
        bytes32 consentId
    ) public view returns (bool) {
        // This function checks whether consent is currently valid.
        //
        // "view" means it only reads data.
        // It does not change anything on the blockchain.


        ConsentRecord memory consent = consents[consentId];
        // Load the consent into memory so we can inspect it.


        if (consent.user == address(0)) {
            // If there is no user, the consent doesn't exist.

            return false;
        }


        if (consent.revoked) {
            // If the user revoked the consent...

            return false;
        }


        if (
            consent.expiresAt != 0 &&
            block.timestamp >= consent.expiresAt
        ) {
            // If:
            //
            // 1. The consent has an expiry time
            // AND
            // 2. The expiry time has passed
            //
            // then the consent is expired.

            return false;
        }


        return true;
        // If none of the above conditions are true,
        // the consent is currently valid.
    }


    // ============================================================
    // GET CONSENT
    // ============================================================

    function getConsent(
        bytes32 consentId
    )
        external
        view
        returns (ConsentRecord memory)
    {
        // This function lets the application read a consent record.


        ConsentRecord memory consent = consents[consentId];
        // Find the consent using its ID.


        require(
            consent.user != address(0),
            "Consent does not exist"
        );
        // Make sure the consent exists.


        return consent;
        // Return the complete consent record.
        //
        // To check whether it is currently valid,
        // use:
        //
        // isConsentValid(consentId)
    }
}