# PhoenixCore Evidence Ledger

## Purpose

The evidence ledger is a host-side append-only JSONL ledger for PhoenixCore validation events.

It is intended for retained evidence such as:

- physical-drive identity receipts
- exclusive read-handle observations
- bounded sacrificial-drive write receipts
- read-back verification receipts
- ARCWYRE boot-attempt classifications
- installer lifecycle observations

## Schema

Each record uses:

```text
bws.evidence-ledger/v1
```

Each record includes:

- `schema_version`
- `sequence`
- `timestamp`
- `event_type`
- `payload`
- `previous_hash`
- `record_hash`

`record_hash` is computed over the canonical record body without the `record_hash` field.

The first record uses:

```text
previous_hash = 0000000000000000000000000000000000000000000000000000000000000000
```

Every later record points at the previous record's hash.

## Security boundary

The ledger detects:

- record deletion
- record reordering
- payload tampering
- sequence gaps
- previous-hash mismatch
- malformed JSONL records
- non-canonical payload values such as NaN

The ledger does **not** claim:

- cryptographic signing
- hardware-backed trust
- remote transparency logging
- timestamp-authority proof
- write protection against filesystem rollback
- release eligibility

This is a tamper-evident host ledger, not a magical courtroom. Software does not become legally binding because it has hashes and a serious filename.

## Usage

Append an event:

```bash
python scripts/evidence/evidence_ledger.py append \
  --ledger evidence/session.jsonl \
  --event-type DRIVE.IDENTITY \
  --payload-json '{"target":"disk/by-id/example","bytes_written":0}'
```

Verify a ledger:

```bash
python scripts/evidence/evidence_ledger.py verify \
  --ledger evidence/session.jsonl \
  --summary evidence/session-summary.json
```

## Ownership

This belongs in PhoenixCore because PhoenixCore orchestrates host-side diagnosis, USB writing, installer lifecycle evidence, and machine evidence collection.

bluephoenix-native consumes selected receipts and defines native contracts. It does not own the host evidence ledger.
