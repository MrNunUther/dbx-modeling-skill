# Anti-pattern remodel: flat claim table

This example shows the skill's default shape guidance applied to a poorly
constructed table. It is an illustrative teaching table, not real data.

- [claim_flat.sql](claim_flat.sql) is a typical "one wide table" design. It has:
  - a text key that is not the first column;
  - member and provider details copied into every row;
  - numbered diagnosis and line columns;
  - an attribute/value pair and an opaque `misc` column;
  - money, flags, and dates stored as text or floats.
- [claim_remodeled.sql](claim_remodeled.sql) is the common-form remodel. It has
  `member`, `provider`, and `health_plan` masters, plus a `claim` header with
  `claim_line` and `claim_diagnosis` children. Every product uses a BIGINT
  surrogate key first, clustered FKs, typed columns, and audit columns.

## Run it

```bash
python3 scripts/shape_profile.py advise examples/anti-patterns/claim_flat.sql --envelope templates/shape-envelope.json
python3 scripts/shape_profile.py advise examples/anti-patterns/claim_remodeled.sql --envelope templates/shape-envelope.json --fail-on-warn
```

## Findings to remodel moves

| Finding on `claim_flat` | Move in the remodel |
|---|---|
| SHP-PK-02, SHP-PK-03 (key position and type) | `claim_id BIGINT` first; the source claim number stays as an attribute |
| SHP-COL-04 `member`, `provider` (embedded entities) | Masters `member.member` and `provider.provider`, referenced by `member_id` and `provider_id` |
| SHP-COL-01 `diagnosis_code_N` (repeating group) | `claim.claim_diagnosis`, one row per diagnosis with a sequence |
| SHP-COL-01 `line_N` (repeating group) | `claim.claim_line`, one row per service line |
| SHP-COL-02, SHP-COL-03 (attribute/value pair, `misc`) | Dropped from the business product; known facts become typed attributes |
| SHP-TYPE-01/02/03 (types) | DECIMAL amounts, BOOLEAN `is_emergency`, DATE `service_date` |
| SHP-FK-01 (scattered FK) | FKs clustered after the PK |
| SHP-BAND-fk_out (too few references) | The header now references member, provider, and plan |

## Result

| Table | Warnings | Advisories |
|---|---|---|
| `claim_flat` | 12 | 3 |
| Remodel (6 products) | 0 | band advisories only |

The remaining advisories say the products are narrower than the corpus's
typical depth (25–48 columns). That gap is expected for a teaching slice and is
not closed by padding. In a real remodel, add the attributes the claims process
actually needs: adjudication dates, denial reasons, place of service, and so on.

When remodeling an existing physical table, also deliver an old-to-new column map
and follow the [evolution](../../references/model-evolution.md) rules. Full
guidance is in [shape topology](../../references/shape-topology.md).
