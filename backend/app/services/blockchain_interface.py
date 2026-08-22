"""
Phase 13: the backend <-> blockchain interface.

This file intentionally contains NO real contract logic. Per the plan,
those details come from Nirali, not invented here:

  1. Contract address
  2. ABI
  3. Network
  4. Consent creation function
  5. Consent activation mechanism
  6. Revoke function
  7. logAccess function
  8. Event names
  9. Event parameters

Once she provides these, replace the bodies below (e.g. with web3.py calls)
without changing their signatures, so routes/consent.py and routes/audit.py
don't need to change.

For now, PATCH /consent/{consent_id}/activate and POST /audit/access accept
a blockchain_tx_hash directly from the caller (simulating what this layer
will eventually produce automatically).
"""


def get_consent_status_onchain(consent_id: str):
    """Placeholder. Will query Nirali's contract for on-chain consent
    status once the contract address/ABI are available."""
    raise NotImplementedError("Waiting on contract details from Nirali (see Phase 13).")


def submit_log_access(consent_id: str, accessor_id: str):
    """Placeholder. Will call Nirali's logAccess() and return the
    resulting transaction hash once the contract is ready."""
    raise NotImplementedError("Waiting on contract details from Nirali (see Phase 13).")
