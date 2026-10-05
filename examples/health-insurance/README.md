# Health-insurance teaching slice

Modification notice: selected ECM concepts are re-authored and simplified.
See [adaptation log](adaptation-log.csv) and
[source assessment](../../references/source-assessment.md).

**Scope:** 6 domains, 10 products, 69 attributes, 10 relationships, and 1 metric
view. This is a bounded reduced core, not a complete health insurer system.
It has no sample rows, compliance certification, deployment, or live evidence.

## Reading paths

| Pattern | Products | Lesson |
|---|---|---|
| Identity and coverage | member.identity, plan.health_plan, enrollment.coverage | Ownership, versioned design, effective intervals |
| Submission and detail | claim.header, claim.line | Header/line grain, business uniqueness, financial snapshots |
| Decisions | claim.adjudication | Multiple decision events, not overwriting event history |
| Provider participation | provider.provider, network.provider_network, network.participation | Genuine many-to-many through relationship-owned intervals |
| Processing vocabulary | claim.claim_status | Reference promotion for a category above six values |
| Financial projection | metrics.claim_financials | Single source, currency grouping, DECIMAL sums, zero-safe ratios |

An identity is one insured person, not a subscriber/household-role model.
Coverage is a person-plan interval; matching claims to actual coverage/service
dates needs data/business checks. Provider-network membership does not imply a
plan-network contract: that relationship is deliberately outside this slice.

The status lookup can represent `submitted`, `pending`, `adjudicated`, `paid`,
`denied`, `suspended`, and `withdrawn` (seven values). These illustrative values
are documented vocabulary, not a distributed production reference code set.
No INSERT statements or sample engine are shipped. Before future use, load a
reviewed vocabulary and validate every referenced state.

Rendering provider is optional and populated later; the documented enrichment
path must be completed where business rules require it. Billing/rendering are
distinct roles. Financial amounts remain DECIMAL and are grouped by currency.
The metric counts **submission versions**, not unique business claims; adding
latest-version reporting requires a separate reviewed source/grain.

Personal/health-linked fields are explicitly classified under the teaching policy.
Provider names can denote individuals and are conservatively personal. Classification
accuracy and de-identification require manual context review, not name heuristics.

## Artifacts and order

1. [Requirements](requirements.md) and [traceability](traceability.csv).
2. [Canonical model](model.json), authoritative for this suite.
3. [Catalog/schemas](schemas/01-catalog-and-schemas.sql).
4. [Tables and PKs](schemas/02-tables.sql).
5. [FK declarations](schemas/03-foreign-keys.sql).
6. [Comments/tags](schemas/04-comments-and-tags.sql).
7. [Optional metric view](metrics/claim-financials.sql).
8. [DBML](diagram/model.dbml), [static report](validation/static-report.json),
   [catalog checks](validation/catalog-parity.sql), and
   [data checks](validation/data-integrity.sql).

All SQL is **unexecuted**. `__CATALOG__` is a literal reviewed-substitution token,
not automatic binding. The DDL is for a fresh, separately authorized namespace;
`IF NOT EXISTS` does not migrate existing tables and FK additions are not
rerun-idempotent. PK/FK declarations do not enforce row integrity.

Run the [renderer](../../scripts/render_example.py) with `--check` to compare all
supported derivative files against canonical JSON. `--write` regenerates the
files only after model validation; it does not connect to Databricks.

## Validation boundaries

The static report proves only applicable offline checks. The manual requirement
for cardinality/snapshot/temporal semantics remains unverified by automation.
Live syntax, physical parity, data uniqueness, orphan rows, completeness,
reference vocabulary, legal obligations, ownership/access enforcement, and
hierarchy-row checks have not been run.

Read-only SQL supplies PK/business uniqueness, FK orphan, enum/pattern, period
order, and coverage-overlap checks. It is not a general compliance/data-quality
framework and must not be run without [authorization](../../references/authorized-live-validation.md).
