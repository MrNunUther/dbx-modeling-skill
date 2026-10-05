# Relationships and normalization

Modification notice: reconciled adaptation of source relationship/normalization
rules; arbitrary deletion and confidence-based auto-repair are not preserved.

## Keys and cardinality

An FK must use existing source columns and reference the declared target PK tuple,
with exactly matching types in order. Put a many-to-one FK on the many side.
One-to-one requires declared source-tuple uniqueness plus separate data evidence.
For many-to-many, model a
business-named association with real reciprocity and relationship-owned facts.
Events can also have multiple participants: do not assume event/master always
proves one-to-many.

Every relationship carries a meaningful role, justification, optionality,
population phase, and source provenance. Two relationships to the same target
need distinct role labels (for example billing provider and rendering provider).
FK-shaped names are candidates only; source-system IDs may intentionally have
no local FK. Do not fabricate a person entity for an unknown operator identifier.

The contract expresses optionality by source-column nullability. A relationship
with a nullable source tuple is optional; a mandatory tuple is fully non-null.
Partial nullable composite tuples require a later MATCH/null-semantics design;
the MVP rejects mixed tuple nullability.

## Temporal behavior

A legitimate child may exist before its target is available. Use an optional FK,
`population_phase: later`, and an explicit enrichment path. Do not reverse
correct cardinality merely to satisfy chronological heuristics. Required
completion-time completeness is a separate data check.

Declare effective intervals, event time, processing time, and version identity
where applicable. Do not conflate date precision with timestamp precision.
Retain execution-time prices, contractual terms, identities, and overrides when
required for auditability. Databricks Time Travel is not a substitute for business
effective-date modeling.

## Graph policy

The default `acyclic_with_hierarchy` policy checks dependencies after excluding
explicit hierarchical self-edges with a distinct source column, role, and
justification. A PK-to-itself FK is always invalid. A syntactically permitted
self-edge does not prove acyclic row-level hierarchy.

`allow_cycles` is an explicit alternate design policy, not a structural waiver.
FK validity still applies. Databricks does not require a relational schema to be
a DAG. Under the default policy, report cycles and propose a reviewed resolution;
do not delete parent-child/user-required edges automatically.

Incoming-only lookups are connected. Standalone products need a declared scope
justification; false joins are worse than an explained standalone table.

## Normalization and deduplication

For the normalized core, document determinants and remove partial/transitive
dependencies through approved design changes. A prefix alone does not prove
redundancy. Preserve:

- Event-time snapshots, audit actor details, and historical overrides.
- Method versus channel; ID versus label; target versus actual.
- Different lifecycle timestamps and date/timestamp precision.
- Measurements and coordinates owned by the entity.

Two similar names do not prove an SSOT violation. Compare grain, lifecycle,
ownership, authoritative source, key identity, and attribute semantics. Propose
merges with dependency/consumer impact. An overlap percentage or self-reported
confidence is only a review signal. Do not merge operational and analytical
grains or discard a natural key required for source reconciliation.
