# Authorized live validation: future execution contract

This release supplies a protocol and read-only SQL, **not** a workspace runner.
No previous modeling request implies workspace access or deployment approval.

## Authorization record

Before any future runner: capture explicit consent, workspace/profile, catalog
allowlist, schema/object scope, warehouse ID, evidence destination, allowed
operations, maximum statements/rows/time/cost, expiry, and cancellation behavior.
Do not store credentials in artifacts.

Read-only verification is the default. Creation, data writes, metadata changes,
grants, masks/filters, and cleanup need separate permission. Silence is not consent.

## Preflight

- Verify actual workspace/profile, UC availability, compute capability, metric
  feature support, and required SELECT/USE/metadata visibility.
- Check supported SQL/SDK operations rather than guessing experimental CLI flags.
- Resolve reviewed placeholders and bound object scope.
- Reject any request outside the allowlist.
- Handle asynchronous statement completion, failure, timeout, cancellation, and
  unavailable/incomplete metadata explicitly.

## Verification sequence

1. Compare table/schema/column identities, order, types, and nullability.
2. Compare declared PK/FK tuples and referenced constraints.
3. Compare comments, requested tags, and metric-view definitions.
4. Check row uniqueness/non-nullness, FK orphan rows, business uniqueness,
   category values, monetary/temporal constraints, and hierarchy cycles.
5. Capture actual evidence with environment, timestamp, statement/result IDs,
   expected/observed values, visibility limitations, and remediation.

Start from the example's
[catalog-parity.sql](../examples/health-insurance/validation/catalog-parity.sql)
and [data-integrity.sql](../examples/health-insurance/validation/data-integrity.sql).
They cover expected example objects; comments/metric definitions, governance
enforcement, temporal completeness, and regulatory correctness still require
appropriate evidence and review.

Zero rows in a violation query is not proof that expected objects exist or that
the caller can see all required metadata. Mark permission errors `blocked`.
Never enrich a live snapshot with model declarations and call those declarations
independently observed facts.

## Installation and cleanup

A future authorized scratch install must use an explicit fresh namespace.
Namespace creation and cleanup must be separately approved, narrowly scoped,
and ownership-verified. No broad catalog/job/run deletion or inferred cleanup.
Existing namespace migrations need an impact/rollback plan, not rerunning
example DDL.

## Future runner acceptance

Test allowlist rejection, capability failures, asynchronous completion, timeouts,
visibility gaps, missing artifacts, tag/key/metric drift, row-integrity failures,
and honest report levels. A runner cannot mark `physical` or `data` checks passed
without actual workspace evidence conforming to the report contract.
