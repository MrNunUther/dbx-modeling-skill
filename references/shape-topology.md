# Shape topology: common forms for products and models

This is the skill's **default shape guidance**. Apply it whenever you design,
review, extend, or remodel a table or model. It describes the common forms that
well-constructed enterprise products and models take. Use those forms to:

- choose a shape before writing columns;
- recognize anti-patterns in an existing table and steer it toward a common form;
- size and wire a full MVM/ECM when that scope is requested.

The forms are derived from 5,914 products in the Vibe Modelling Agent's published
outputs. These are latest current-lineage exports across 15 industries, triangulated
against documented principles. Shape is a **prior, not a requirement**. Business
intent, protected names, declared grain, and the
[instructions](../rules/instructions.md) win over any band. Shape conformance is
a proxy for good structure, not proof of semantic correctness.

## Two levels, one default

| Level | Applies to | Command | Default use |
|---|---|---|---|
| Product shape | Any table or product, including a single DDL statement | `advise` | Always: design, review, remodel |
| Model envelope | A set of related products | `check` (`--ignore-scale` for bounded scopes) | Whenever more than one product is in scope |
| Scale targets | A full MVM/ECM | `targets`, `check` with scale | Only when that scope is requested |

Scale (domain/product counts, total FKs) is the only part that depends on scope.
Never enlarge a deliberately bounded scope to satisfy it. Everything else in
this page applies to every product and model.

## Common product forms

Classify each product first: declared, or inferred and reported as inferred. Then
compare it with the form for its class. Values are corpus medians with
p10–p90 bands.

| Class | Columns | Outbound FKs | Typical form |
|---|---|---|---|
| Master | 39 [25–46] | 4 [1–9] | Durable identity; heavily referenced; few parents; often a span or versioned |
| Transactional | 41 [26–48] | 7 [3–13] | Event or document with status and event dates; references its parties, products, and context |
| Association | 14 [6–21] | 2 [2–4] | Resolves many-to-many; two or more FKs plus role, span, and a few qualifiers |
| Reference | 36 [26–43] | 2 [1–5] | Governed classification; the agent's are rich, but a small code list is legitimate (do not pad) |

**Body plan (invariant).** In ≈ 100% of products:

- the PK is the first column;
- FKs are clustered right after the PK, in ≈ 97% of products;
- FK names end with the target PK, in ≈ 99% of FKs.

Audit columns (`created_timestamp`, `updated_timestamp`) are present in ≈ 87–90% of
products. Place them last by convention; the corpus order varies.

Keys are BIGINT surrogates: 100% of products. Natural and source keys stay as
attributes. Money is DECIMAL, flags are BOOLEAN, and dates are DATE or TIMESTAMP.

**Attribute families.** Share of columns per product (invariant):

| Family | Share |
|---|---|
| Temporal | ≈ 12% (about half DATE) |
| Identifier | ≈ 9% |
| Flag | ≈ 8% |
| Amount | ≈ 8% |
| Classifier | ≈ 6% |
| Status | ≈ 4% |
| Unclassified | ≈ 17% |

A high unclassified share usually means unconventional naming or mixed grain.

**Archetypes.** Combine as the business requires:

- **Stateful event:** a transaction with a status and dates per state.
- **Span:** effective and termination dates.
- **Versioned:** a version number or a prior/superseded reference.
- **Hierarchy:** a role-named self-reference such as `parent_` or `prior_`.
- **Line:** a child of a header, one row per occurrence.

## Anti-patterns and their common-form remedies

`advise` reports these with a remedy. The prevalence column shows how often each
pattern appears in agent products. A rare pattern is a strong signal; a common
one marked *agent defect* contradicts documented principles and is not imitated.

| Code | Anti-pattern | Remedy toward common form | Corpus |
|---|---|---|---|
| SHP-PK-01/02/03 | Missing PK, PK not first, non-BIGINT PK | Single BIGINT surrogate, first column; keep business keys as attributes | ≤ 0.1% |
| SHP-COL-01 | Repeating group (`code_1`, `code_2`, `line1_*`) | Child product, one row per occurrence | 0.9% |
| SHP-COL-02 | Entity-attribute-value pair | Typed attributes; reference and association for open sets | 0.1% |
| SHP-COL-03 | Generic or opaque columns (`misc`, `value`, `*_json`) | Named, typed attributes; raw payloads stay in a source layer | 0.4% |
| SHP-COL-04 | Embedded entity (`member_name`, `member_phone`, ...) | Extract or reuse a master; reference it by FK | 5.0% |
| SHP-TYPE-01/02/03 | Money, flag, or date stored as text, float, or integer | DECIMAL, BOOLEAN, DATE/TIMESTAMP | ≤ 1% |
| SHP-FK-01 | FKs scattered among business columns | Cluster FKs after the PK | 2.8% |
| SHP-FK-02 (advise) | FK name hides its target | `<role_>target_pk` | 7.9% |
| SHP-FK-03 | Domain-prefixed FK (`member_identity_id`) | Target PK or business role prefix | 19%, agent defect |
| SHP-FK-05 | PII tag on a surrogate FK | Tag the personal attributes, not keys | 49%, agent defect |
| SHP-AUD-01, SPAN-01, EVT-01 (advise) | No audit columns; open span; status-less transaction | Add the missing columns | 2–14% |
| SHP-BAND-* | Columns, FKs, or family mix outside the class band | Direction-specific remedy | n/a |

A table more than 1.4× wider than its class p90 is a warning, matching the
documented hard-reject buffer. Narrow tables get advice only: enrich them with
real process attributes, never pad.

## Remodeling a poorly constructed table

1. **Preserve the input.** Run `advise` on it. Accept a JSON model or bounded
   `CREATE TABLE` DDL:

   ```bash
   python3 scripts/shape_profile.py advise TABLE.sql --envelope templates/shape-envelope.json
   ```

2. **Declare the grain.** Read the class and archetypes the input suggests.
   Confirm the true grain with the user when it is ambiguous; inference is a
   hint, not a decision.
3. **Fix warnings in order:**
   1. key and body plan;
   2. embedded entities and repeating groups (these create new products);
   3. EAV and generic columns;
   4. types;
   5. FK naming.

   Each extracted product gets its own grain sentence and PK, and is checked
   with `advise` in turn.
4. **Weigh advisories against intent.** Band gaps on a bounded slice are
   expected. Report them; do not fabricate columns or relationships to close them.
5. **Deliver the result.** Include a rename and move map from old to new columns,
   the new products, and the before/after `advise` output. Follow the
   [evolution](model-evolution.md) rules for existing physical tables.

See the [anti-pattern example](../examples/anti-patterns/README.md): one flat
claim table with 12 warnings becomes six products with zero warnings.

## Model-level topology

These shapes apply to any multi-product model. Values are MVM medians with
p10–p90 bands.

| Shape | Common form | Stability |
|---|---|---|
| Graph | DAG; no siloed or unresolved products; self-references ≈ 2% of FKs (ECM 5%), role-named | invariant |
| Cross-domain FKs | 0.71 [0.64–0.79] (ECM 0.63) | invariant |
| Hub concentration | Top 10% of products hold 0.47 of inbound FKs (ECM 0.75) | invariant |
| Polarity | Master products ≈ 11 in / 5 out; transactional ≈ 10 out. About 1/4 of domains are producers and 1/3 are consumers | stable |
| Class mix | Master 0.50, transactional 0.44, association ≈ 0.02 (ECM 0.12) | invariant |
| Metric views | ≈ 0.8 per product (ECM 0.65) | invariant |

Domain polarity is `(in − out) / (in + out)`, computed on cross-domain FKs.
Producer domains own master hubs; consumer domains own transactions.

For a bounded model, run:

```bash
python3 scripts/shape_profile.py check MODEL --envelope templates/shape-envelope.json --scope mvm --ignore-scale --format text
```

Treat invariant `out` rows as design questions, not as quotas.

### Full-scope sizing

The full-scope bands are:

- **MVM:** 12 [9–13] domains, 10 [8–11] products per domain, about 114 products.
- **ECM:** 18 [14–20] domains, about 20 products per domain, about 405 products.

An MVM is a subset of its ECM at the same attribute depth, not a thinner version.
The documentation suggests 6–10 MVM domains, while current outputs have 9–13. Let
the user's tier or scope decide.

When a full scope is requested, plan skeleton-first:

1. Run `targets --scope mvm|ecm` (add `--domains N` to honor a tier).
2. Assign domain roles and place hubs in producer domains.
3. Allocate class and archetype quotas.
4. Wire FKs to the fan-out and cross-domain targets, keeping the graph acyclic.
5. Fill each product with the body plan and family mix.
6. Score with `check` and repair invariant `out` rows within a bounded number of passes.

## Signal versus defect: triangulation

| Documented | Observed in corpus | Treatment |
|---|---|---|
| yes | yes | Common form: match the band |
| no | yes | Style: match unless intent differs |
| yes | no | Follow the documentation |
| contradicts | yes | **Agent defect: never imitate** |

Where the documentation states an ideal (PK first, zero cycles, zero silos), the
band extends to that ideal. Exceeding the corpus in that direction is never penalized.

## Evidence

Measured without running the agent:

- **Leave-one-industry-out.** Each industry is scored against bands built from
  the other 14 industries. The median score is 84 for both scopes, so a score of
  about 80 or above reads as agent-like.
- **Closed loop.** Skeletons built only from `targets` score about 92 (MVM) and
  about 84 (ECM) ([tests](../tests/test_shape_profile.py)).
- **Agent output.** The agent's own health_insurance MVM triggers only its two
  known defects (FK-03, FK-05) and two genuine repeating groups.
- **Remodel example.** The flat example table has 12 warnings; its remodel has 0.
  The bounded [teaching slice](../examples/health-insurance/README.md) has
  0 warnings and advisories only.

## Provenance and regeneration

[`shape-envelope.json`](../templates/shape-envelope.json) holds aggregate
statistics only:

- model bands per scope;
- product bands per class;
- anti-pattern prevalence;
- leave-one-out scores;
- source export paths.

These are derived from Vibe Modelling Agent exports in the Databricks
`lakehouse-industry-data-models` repository. No model content is copied. Earlier
0.7.x agent outputs are excluded by default.

Regenerate after new releases:

```bash
python3 scripts/shape_profile.py build-envelope --corpus PATH/TO/data-models --out templates/shape-envelope.json
```

Then review the leave-one-out scores and anti-pattern prevalence. See
[NOTICE](../NOTICE) before redistribution.
