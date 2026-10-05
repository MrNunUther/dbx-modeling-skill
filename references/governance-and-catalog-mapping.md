# Governance and Unity Catalog mapping

Modification notice: synthesized modeling guidance; UC administration stays a
separately authorized operation.

## Mapping and create order

Default one environment/model namespace -> catalog; domain -> schema; product ->
managed Delta table. Division/subdomain stay semantic metadata. Use explicit
physical identifiers and collision checks rather than copying a source catalog.

Example SQL contains the literal `__CATALOG__` token. It is not a Databricks
parameter binding: substitute a reviewed identifier offline in an authorized
copy before execution. Do not execute the distributed SQL unchanged.

1. Catalog and schemas.
2. Tables, explicit nullability, and PK declarations.
3. FKs after all endpoints exist.
4. Comments and object/column tags.
5. Optional analytical/metric-view projections.

`IF NOT EXISTS` is not a migration tool: existing objects may have incompatible
definitions. Compare the actual schema and plan changes before using the files
against an existing namespace. FK `ADD CONSTRAINT` is not rerun-idempotent.
No file uses DROP/CASCADE or grants itself privileges.

## Governance metadata

Use structured tags for glossary, classification, division/subdomain,
stewardship, and requested discovery metadata. Keys/FKs live in declarations,
not classification tags. No comma-separated string is the authoritative format.

Person/health/payment data are `restricted` under the example policy, with a
specific sensitivity marker. Nonpersonal business contacts can be confidential
under an approved policy. Classify by context, not just attribute-name regex.
Regular data still receives applicable glossary/discovery tags.

Tags alone do not enforce access. Do not infer HIPAA/GDPR/PCI compliance from a
boolean, tag, or standards reference. Owners should be appropriate groups;
assigning UC ownership, grants, row filters, masks, or governed tags needs
appropriate privileges and separate authorization.

## Platform semantics and sources

- PK/FK constraints are informational, not enforced row integrity. PK columns
  must be non-null. Composite key ordering matters.
- Do not add optimizer `RELY` absent established integrity and an explicit
  decision. Data checks and catalog metadata checks are distinct.
- The example metric view has one source and no joins for simplicity. Metric
  views support more sophisticated joins; single-source is an MVP boundary,
  not a platform prohibition.
- No identity/clustering strategy is selected without ingestion/workload needs.
- Metric views (`WITH METRICS LANGUAGE YAML`) are not materialized views.

Official documentation consulted for this release on 2026-10-05:

- [Table constraints](https://docs.databricks.com/aws/en/sql/language-manual/sql-ref-syntax-ddl-create-table-constraint)
- [Metric-view creation and prerequisites](https://docs.databricks.com/aws/en/uc-semantics/metric-views/create)

The metric-view example uses YAML version 1.1. Verify its supported features and
compute capability in the target workspace; runtime compatibility remains
`not_run`. Optional sibling skills are conveniences, not proof of compatibility.
