# Catalog fixture provenance

These are fixed, credential-free, commit-safe synthetic fixtures created for
PipelineForge's public demo path. They are not client data and are not claimed
as observations from a real business.

The three files deliberately represent successive catalog exports:

- CSV: initial rows plus one empty-customer contract violation;
- JSONL: a corrected duplicate, a new row, and one invalid amount;
- Parquet: a late correction plus two new rows.

The expected final warehouse has five unique orders and an amount total of
`1550`; two rows must be quarantined. The binary Parquet fixture is generated
once from the exact rows recorded in `PARQUET_ROWS.json` and committed with its
SHA-256 in `SHA256SUMS`.
