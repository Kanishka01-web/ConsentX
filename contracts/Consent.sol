// SPDX-License-Identifier: MIT
// This tells people that this code uses the MIT open-source license.

pragma solidity ^0.8.28;
// This contract uses Solidity version 0.8.28.


contract Consent {
    // ============================================================
    // CONSENT RECORD
    // ============================================================

    struct ConsentRecord {
        // Stores all important information about one consent.

        address user;
        // Wallet address that originally gave the consent.

        uint16 purposeCode;
        // Number representing why the data is being shared.
        //
        // Example:
        // 101 = Healthcare
        // 102 = Financial
        // 103 = Marketing

        uint16 policyVersion;
        // Version of the privacy policy the user agreed to.

        uint64 grantedAt;
        // Timestamp when the consent was originally granted.
        //
        // This value is NEVER changed during revocation.

        uint64 expiresAt;
        // Timestamp when the consent expires.
        //
        // 0 means no expiry was specified.

        uint64 revokedAt;
        // Timestamp when the consent was revoked.
        //
        // 0 means it has not been revoked.

        bool revoked;
        // false = active/not revoked.
        // true = revoked.
    }


    // ============================================================
    // STORAGE
    // ============================================================

    mapping(address => uint256) public userNonce;
    // Every user gets their own counter.
    //
    // This counter is used to create unique consent IDs.
    //
    // First consent:
    // nonce = 0
    //
    // Second consent:
    // nonce = 1
    //
    // Third consent:
    // nonce = 2


    mapping(bytes32 => ConsentRecord) private consents;
    // Stores consent records using their consent ID.
    //
    // consentId -> ConsentRecord


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
    // Emitted whenever a new consent is created.


    event ConsentRevoked(
        bytes32 indexed consentId,
        address indexed user,
        uint64 revokedAt
    );
    // Emitted whenever an existing consent is revoked.


    event DataAccessed(
        bytes32 indexed consentId,
        address indexed accessor,
        bytes32 dataType,
        uint64 accessedAt
    );
    // Emitted whenever an application/service records a data access.
    //
    // consentId = consent that supposedly authorizes the access.
    //
    // accessor = wallet/address that called logAccess().
    //
    // dataType = identifier for the type of data accessed.
    //
    // accessedAt = blockchain timestamp of the access.
    //
    // IMPORTANT:
    // We do NOT put actual private/user data on-chain.
    // Only a small identifier is recorded.


    // ============================================================
    // GRANT CONSENT
    // ============================================================

    function grantConsent(
        uint16 purposeCode,
        uint16 policyVersion,
        uint64 durationSeconds
    )
        external
        returns (bytes32 consentId)
    {
        // Creates a new consent for the caller.


        require(
            purposeCode != 0,
            "Invalid purpose"
        );
        // Purpose code must be valid.


        require(
            policyVersion != 0,
            "Invalid policy version"
        );
        // Policy version must be greater than zero.


        uint256 nonce = userNonce[msg.sender];
        // Get the caller's current nonce.


        consentId = keccak256(
            abi.encodePacked(
                msg.sender,
                nonce
            )
        );
        // Generate the consent ID from:
        //
        // 1. The user's wallet address.
        // 2. The user's nonce.
        //
        // The user cannot choose the ID themselves.
        //
        // This prevents another user from simply submitting
        // a transaction with a chosen predictable ID.


        userNonce[msg.sender] = nonce + 1;
        // Increase the nonce.
        //
        // This guarantees the user's next consent gets
        // a different ID.


        uint64 grantedAt = uint64(block.timestamp);
        // Save the current blockchain timestamp.


        uint64 expiresAt = 0;
        // By default, the consent has no expiry.


        if (durationSeconds > 0) {
            // If the caller provided an expiry duration...

            require(
                durationSeconds <= type(uint64).max - grantedAt,
                "Expiry overflow"
            );
            // Make sure adding the duration cannot overflow uint64.


            expiresAt = grantedAt + durationSeconds;
            // Calculate the expiry timestamp.
        }


        consents[consentId] = ConsentRecord({
            user: msg.sender,
            // Save the user.

            purposeCode: purposeCode,
            // Save the purpose.

            policyVersion: policyVersion,
            // Save the policy version.

            grantedAt: grantedAt,
            // Save the original grant timestamp.

            expiresAt: expiresAt,
            // Save the expiry timestamp.

            revokedAt: 0,
            // Consent has not been revoked yet.

            revoked: false
            // Consent starts as active.
        });


        emit ConsentGranted(
            consentId,
            msg.sender,
            purposeCode,
            policyVersion,
            grantedAt,
            expiresAt
        );
        // Tell the backend/frontend that a consent was created.
    }


    // ============================================================
    // REVOKE CONSENT
    // ============================================================

    function revokeConsent(
        bytes32 consentId
    )
        external
    {
        // Allows the original consent owner to revoke their consent.


        ConsentRecord storage consent = consents[consentId];
        // Load the consent directly from blockchain storage.


        require(
            consent.user != address(0),
            "Consent does not exist"
        );
        // Make sure this consent actually exists.


        require(
            consent.user == msg.sender,
            "Not consent owner"
        );
        // SECURITY:
        // Only the original consent owner can revoke it.


        require(
            !consent.revoked,
            "Consent already revoked"
        );
        // Prevent revoking the same consent twice.


        consent.revoked = true;
        // Mark the consent as revoked.


        consent.revokedAt = uint64(block.timestamp);
        // Save when the revocation happened.
        //
        // IMPORTANT:
        // grantedAt is NOT changed.
        //
        // This preserves the original audit history.


        emit ConsentRevoked(
            consentId,
            msg.sender,
            consent.revokedAt
        );
        // Tell the backend/frontend that the consent was revoked.
    }


    // ============================================================
    // LOG DATA ACCESS
    // ============================================================

    function logAccess(
        bytes32 consentId,
        bytes32 dataType
    )
        external
    {
        // Records that an application/service accessed data
        // under a particular consent.


        require(
            isConsentValid(consentId),
            "Consent is not valid"
        );
        // IMPORTANT:
        //
        // We only allow an access log if the consent is currently valid.
        //
        // This prevents logging an access against:
        //
        // - a nonexistent consent
        // - a revoked consent
        // - an expired consent


        emit DataAccessed(
            consentId,
            msg.sender,
            dataType,
            uint64(block.timestamp)
        );
        // Record the access event.
        //
        // The actual data is NOT stored on-chain.
        // Only the consent ID, accessor, data type and timestamp
        // are recorded.
    }


    // ============================================================
    // CHECK CONSENT VALIDITY
    // ============================================================

    function isConsentValid(
        bytes32 consentId
    )
        public
        view
        returns (bool)
    {
        // Checks whether a consent is currently valid.


        ConsentRecord memory consent = consents[consentId];
        // Load the consent into memory.


        if (consent.user == address(0)) {
            // No user means the consent does not exist.

            return false;
        }


        if (consent.revoked) {
            // A revoked consent is no longer valid.

            return false;
        }


        if (
            consent.expiresAt != 0 &&
            block.timestamp >= consent.expiresAt
        ) {
            // If the consent has an expiry time
            // and that time has passed...

            return false;
        }


        return true;
        // Otherwise the consent is currently valid.
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
        // Allows the backend/frontend to retrieve a consent record.


        ConsentRecord memory consent = consents[consentId];
        // Find the consent using its ID.


        require(
            consent.user != address(0),
            "Consent does not exist"
        );
        // Make sure the consent exists.


        return consent;
        // Return the complete consent record.
    }
}