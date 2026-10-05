# Enterprise objects and canonical contract

Modification notice: original synthesis informed by the source inventory.

## Hierarchy and semantics

Business/model -> division classification -> domain -> subdomain -> product ->
attribute/key. Relationships connect products; analytical projections sit outside
the normalized core. Division and subdomain are semantic labels, not necessarily
catalog/schema boundaries.

Domain ownership is based on business responsibility and stewardship, not a
universal department blacklist. A valid lookup may have only a few columns.
Do not pad attributes, merge unrelated grains, or create corporate domains merely
to fill a quota. Full/reduced scope is explicit; legacy ECM/MVM names are ambiguous.

Each product declares purpose, grain, classification, role, steward, a PK column
tuple, and business uniqueness tuples. An association owns a real relationship,
not an analytical correlation. A transaction line and its header have distinct
identities and lifecycles.

## Contract 1.0.0

[model.schema.json](../templates/model.schema.json) documents the complete
bounded MVP shape. The offline validator uses `jsonschema` for shape validation
and explicit checks for model semantics. Additional undocumented fields are
rejected rather than accepted as silently ignored instructions.

| Field | Meaning |
|---|---|
| `contract_version` | Shape version, independent of skill/model/source versions |
| `model_version` | Immutable model snapshot version |
| `business` | Name, industry, jurisdiction, process list |
| `profile`, `scope`, `conventions` | Applied design policy and configuration |
| `provenance` | Source references, adaptation method, no secrets |
| `domains` | Name, physical schema, division, owner, descriptions/subdomains/products |
| `products` | Physical/logical identity, classification, role, grain, keys, attributes |
| `attributes` | Type/nullability, monetary/snapshot semantics, glossary, description, classification, references, constraints, tags |
| `relationships` | Endpoint tuples, cardinality, role, optionality, phase, justification |
| `metric_views` | Single-source MVP projections with declared column dependencies |
| `requirements` | Stable IDs, artifact/object targets, check IDs, manual review status |
| `protected` | Requested domains/products/counts, checked without auto-repair |

The MVP supports ordered composite PK/FK tuples for structural checks and DDL
rendering. Types must match by position; do not flatten a composite key into one
column. Actual runtime support must be verified separately.

## Defaults and ordering

Use BIGINT surrogate keys unless there is a reason to use a different supported
key type. Declare business uniqueness separately; a surrogate does not prevent
duplicate business records. Never infer PK declarations from name suffixes.

Order columns PK, FKs, business fields, housekeeping, then history. This is a
readability convention, not a Databricks requirement. All PK columns are
non-nullable. Declared `monetary` values must use explicit DECIMAL precision/scale.
The configured `key_type` is a synthesis default, not a ban on a justified
composite business-key type. Do not assume
identity generation is appropriate for distributed/concurrent ingestion.

Use semantic names and preserve units. Contextualize generic names such as
`status`; avoid needless prefixes on already-specific terms. Separate allowed
values from STRING format patterns. Type inference from names is only a proposal
until reviewed; BOOLEAN flags do not carry regexes.

## Unknowns

Missing stewardship, jurisdiction-specific standards, temporal grain, or source
identity guarantees are explicit design decisions. Record unknowns in the brief
and block claims that depend on them. A glossary or classification string is not
a guarantee of legal compliance.
