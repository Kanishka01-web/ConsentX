"""
Phase 18/19, updated with confirmed details from Nirali.

CONFIRMED:
  - grantConsent(purposeCode: uint16, policyVersion: uint16, durationSeconds: uint64)
    -> immediately valid, no separate activation step on-chain
  - revokeConsent(consentId: bytes32) -> only the original creator wallet can call it
  - Events: ConsentGranted, ConsentRevoked
  - Read functions: isConsentValid(consentId), getConsent(consentId), userNonce(address)

STILL MISSING - do not invent these:
  - logAccess() does not exist on the contract yet. log_access() stays a
    stub until Nirali adds it (Phase 22 blocker).
  - No Polygon Amoy deployment yet - only a local Hardhat address exists.
    Point POLYGON_AMOY_RPC_URL at http://127.0.0.1:8545 for now.

purposeCode/policyVersion mapping: the contract takes numeric codes, but
Consent stores free-text purpose/data_type. Until the team agrees a mapping
table, grant_consent() below takes the codes as explicit arguments instead
of guessing a text-to-number conversion.
"""
import os
import json
from web3 import Web3

RPC_URL = os.getenv("POLYGON_AMOY_RPC_URL")
CONTRACT_ADDRESS = os.getenv("CONSENTX_CONTRACT_ADDRESS")
RELAYER_PRIVATE_KEY = os.getenv("RELAYER_PRIVATE_KEY")

CONSENT_ABI = json.loads("""
[
  {
    "inputs": [
      {"internalType": "uint16", "name": "purposeCode", "type": "uint16"},
      {"internalType": "uint16", "name": "policyVersion", "type": "uint16"},
      {"internalType": "uint64", "name": "durationSeconds", "type": "uint64"}
    ],
    "name": "grantConsent",
    "outputs": [{"internalType": "bytes32", "name": "", "type": "bytes32"}],
    "stateMutability": "nonpayable",
    "type": "function"
  },
  {
    "inputs": [{"internalType": "bytes32", "name": "consentId", "type": "bytes32"}],
    "name": "revokeConsent",
    "outputs": [],
    "stateMutability": "nonpayable",
    "type": "function"
  },
  {
    "inputs": [{"internalType": "bytes32", "name": "consentId", "type": "bytes32"}],
    "name": "isConsentValid",
    "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
    "stateMutability": "view",
    "type": "function"
  },
  {
    "anonymous": false,
    "inputs": [
      {"indexed": true, "internalType": "bytes32", "name": "consentId", "type": "bytes32"},
      {"indexed": true, "internalType": "address", "name": "user", "type": "address"},
      {"indexed": false, "internalType": "uint16", "name": "purposeCode", "type": "uint16"},
      {"indexed": false, "internalType": "uint16", "name": "policyVersion", "type": "uint16"},
      {"indexed": false, "internalType": "uint64", "name": "grantedAt", "type": "uint64"},
      {"indexed": false, "internalType": "uint64", "name": "expiresAt", "type": "uint64"}
    ],
    "name": "ConsentGranted",
    "type": "event"
  },
  {
    "anonymous": false,
    "inputs": [
      {"indexed": true, "internalType": "bytes32", "name": "consentId", "type": "bytes32"},
      {"indexed": true, "internalType": "address", "name": "user", "type": "address"},
      {"indexed": false, "internalType": "uint64", "name": "revokedAt", "type": "uint64"}
    ],
    "name": "ConsentRevoked",
    "type": "event"
  }
]
""")

_w3 = None
_contract = None
_relayer_account = None


def connect() -> Web3:
    global _w3
    if _w3 is None:
        if not RPC_URL:
            raise RuntimeError("POLYGON_AMOY_RPC_URL is not set in .env (use http://127.0.0.1:8545 for local Hardhat)")
        _w3 = Web3(Web3.HTTPProvider(RPC_URL))
    return _w3


def get_contract():
    global _contract
    if _contract is None:
        if not CONTRACT_ADDRESS:
            raise RuntimeError("CONSENTX_CONTRACT_ADDRESS is not set in .env")
        w3 = connect()
        _contract = w3.eth.contract(address=Web3.to_checksum_address(CONTRACT_ADDRESS), abi=CONSENT_ABI)
    return _contract


def _get_relayer_account():
    global _relayer_account
    if _relayer_account is None:
        if not RELAYER_PRIVATE_KEY:
            raise RuntimeError("RELAYER_PRIVATE_KEY is not set in .env")
        w3 = connect()
        _relayer_account = w3.eth.account.from_key(RELAYER_PRIVATE_KEY)
    return _relayer_account


def grant_consent(purpose_code: int, policy_version: int, duration_seconds: int) -> dict:
    w3 = connect()
    contract = get_contract()
    account = _get_relayer_account()

    tx = contract.functions.grantConsent(purpose_code, policy_version, duration_seconds).build_transaction({
        "from": account.address,
        "nonce": w3.eth.get_transaction_count(account.address),
    })
    signed = account.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

    logs = contract.events.ConsentGranted().process_receipt(receipt)
    on_chain_consent_id = logs[0]["args"]["consentId"].hex() if logs else None

    return {"tx_hash": tx_hash.hex(), "on_chain_consent_id": on_chain_consent_id}


def revoke_consent(on_chain_consent_id: str) -> dict:
    w3 = connect()
    contract = get_contract()
    account = _get_relayer_account()

    consent_id_bytes = bytes.fromhex(on_chain_consent_id.replace("0x", ""))

    tx = contract.functions.revokeConsent(consent_id_bytes).build_transaction({
        "from": account.address,
        "nonce": w3.eth.get_transaction_count(account.address),
    })
    signed = account.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    w3.eth.wait_for_transaction_receipt(tx_hash)

    return {"tx_hash": tx_hash.hex()}


def log_access(consent_id: str, accessor_id: str) -> str:
    raise NotImplementedError(
        "logAccess() does not exist on the current contract. Ask Nirali to add it (Phase 22 blocker)."
    )


def get_transaction(tx_hash: str):
    w3 = connect()
    return w3.eth.get_transaction_receipt(tx_hash)