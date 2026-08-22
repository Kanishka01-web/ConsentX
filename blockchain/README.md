# blockchain/

Not built yet — this is Nirali's folder.

Per Step 5 and Step 8 of the plan, before finalizing `backend/app/models.py`,
ask Nirali for:
- Final consent contract functions and events
- Exactly which fields her contract exposes (e.g. transaction hash,
  on-chain consent identifier)

Once confirmed, `blockchain_tx_hash` in `Consent` (backend/app/models.py)
gets populated from her contract's output, and any additional on-chain
fields she specifies should be added there too.

Reminder from the plan: don't store unnecessary personal/sensitive data
on-chain.
