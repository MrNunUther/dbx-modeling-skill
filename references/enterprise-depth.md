# Enterprise depth: what "complete" looks like

Modification notice: original synthesis. The targets are aggregate shapes
measured from published Vibe Modelling Agent outputs (see
[shape topology](shape-topology.md)) and reconciled with the
[instructions](../rules/instructions.md).

Enterprise depth is the **default** for every designed product and model. A
product is not finished when it has a key, a name, and a status. It is finished
when it records what the business processes in scope need to:

- identify the thing;
- classify it;
- track its lifecycle;
- date its events;
- measure it;
- relate it to its context;
- reconcile it with its sources.

## Bounded is not thin

| Request | Limits | Does not limit |
|---|---|---|
| "Bound to four domains" | Which domains exist | Products per domain, columns per product, relationships, metadata |
| "Minimum viable model (MVM)" | Breadth: the core domains first | Depth: an MVM product has the same depth as its ECM counterpart |
| "Teaching, conceptual, or logical-only slice" | Depth, deliberately | Nothing else; state the thinness in the brief |

Produce a thin model only when the user asks for one. The
[health-insurance teaching slice](../examples/health-insurance/README.md) is
deliberately thin (about 7 columns per product). It is a contract and pattern
reference, **not a depth reference**. For depth, use the
[enterprise-depth example](../examples/enterprise-depth/README.md).

## Depth is not padding

Every column must answer a question that a process, report, control, or
integration in scope actually asks. Fill each product by walking the coverage
checklist for its class below, keeping only the sections that apply. That yields
real columns; a placeholder never qualifies.

- Never add `custom_field_1`, `misc`, `extra_data`, or columns duplicated with a
  different suffix.
- Never copy another product's attributes. Reference that product instead.
- If the brief cannot support a section, record it as an open question.
- Never bolt the same block onto every product. In the corpus, at most two
  non-key columns appear on 80% or more of a model's products: the created and
  updated timestamps. Data-quality scores, stewardship dates, retention codes,
  lineage batch ids, and similar governance columns belong on the products that
  manage them, or in platform metadata. They do not belong on every row.
- Never reuse a stock sentence across descriptions ("This supports audit,
  routing, and reporting."). Write each description for its own column.

`check` enforces this. Before scoring, it discounts ubiquitous non-key columns
beyond the two audit stamps (and the edges they carry), plus sentences repeated
across many descriptions. Boilerplate therefore cannot raise depth, density, or
description scores. The corpus loses nothing to this discount.

A small reference list (code, name, description, sort order, active flag) is
legitimately narrow. Do not inflate it.

## Coverage checklists

The counts below are typical ranges, not quotas. Totals land around the corpus
bands:

| Class | Typical columns (p10–p90) | Typical outbound FKs |
|---|---|---|
| Master | 25–46 | 1–9 |
| Transactional | 26–48 | 3–13 |
| Association | 6–21 (rare: 1–4% of products) | 2–4 |
| Reference | 26–43 when richly governed (a small list may be narrow) | 1–5 |

### Master (party, resource, agreement, location)

| Section | Typical columns | Examples of the kind of column |
|---|---|---|
| Key and context references | 1 + 1–9 | Owning organization, parent (hierarchy), primary location, classification reference |
| Identification | 3–5 | Official number, source/external identifiers, legal name, display name |
| Classification | 3–5 | Type, category, subtype, segment, standard industry/zoning/product codes |
| Lifecycle | 3–5 | Status, status reason, status date, effective and termination dates, version number |
| Characteristics | 8–15 | The physical, legal, or commercial facts the domain manages |
| Measures and amounts | 2–5 | Capacity, area, limits, valuations with currency code |
| Flags | 2–4 | `is_active`, `is_exempt`, `has_restriction` |
| Source and audit | 2–4 | Created and updated timestamps on every product. Add source system code and source record id only where the product reconciles more than one source |

### Transactional (event, document, request, case, order)

| Section | Typical columns | Examples of the kind of column |
|---|---|---|
| Key and references | 1 + 3–13 | Requesting party, responsible party, assignee, subject resource, location, channel, parent or related transaction |
| Identification | 2–4 | Document/case number, external reference, channel reference |
| Classification | 3–5 | Type, category, priority, reason code, channel |
| Lifecycle and events | 5–9 | Status, status reason, and a timestamp per state (submitted, accepted, approved, completed, cancelled) |
| Business dates | 2–5 | Due, target, service, and period start/end dates (DATE) |
| Amounts | 3–6 | Fee, tax, discount, adjustment, total, and currency code (DECIMAL) |
| Measures | 1–4 | Duration, quantity, SLA hours, score |
| Flags | 2–4 | `is_expedited`, `is_disputed`, `is_billable` |
| Outcome | 1–3 | Resolution code, outcome summary |
| Source and audit | 2–4 | As for masters |

### Association (participation, assignment, membership)

Associations are rare in the corpus (about 1–4% of products, typically 0–1 per
domain). Most links are FKs on the transaction or master, with a role-named
column (`requesting_party_id`, `inspector_party_id`). Create an association only
when the relationship itself owns facts or history, as below:
Two or more references, a role, effective and end dates, primary/default flag,
share or percentage, status, source, and audit columns. The relationship owns
these facts; neither endpoint can.

### Reference (governed classification)

Code (with a pattern), name, description, category or group, sort order,
effective and end dates, active flag, and standard or authority source. Add
parent code, regulatory citation, and mapping codes when governed externally.

## Model breadth inside the scope

- **Products per domain:** about 8–11, across 2–3 two-word subdomains. A domain
  with three products is usually missing its events, its associations, or its
  governed classifications.
- **Cross-domain references:** about two-thirds of FKs cross a domain boundary.
  Transactions reference the parties, resources, and locations owned elsewhere
  instead of restating them. Shared hubs (party, location, asset) are heavily
  referenced.
- **Archetypes:**
  - versioned products: about 20%, using a version number or a supersedes
    reference;
  - hierarchies: about 15%, as a role-named `parent_` self-reference;
  - span-dated masters and associations: about 30%;
  - header/line pairs where a document has occurrences.
- **Metric views:** about 0.8 per product. Every major transaction gets a
  governed projection.

## Metadata depth

| Item | Typical depth |
|---|---|
| Product description | 400–600 characters: purpose, grain, lifecycle, main consumers, and what is out of bounds. `description_width` does not apply |
| Attribute description | 90–170 characters: meaning, unit or format, and business rule or source. Stay within the 256-character `description_width` editorial convention |
| Patterns | About 15% of columns carry a format pattern: coded identifiers, official numbers, codes |
| Types | Business dates as DATE (about half of temporal columns); moments as TIMESTAMP; flags as BOOLEAN (about 8% of columns); money as DECIMAL (about 12%) |
| Sensitivity | Tag personal and confidential attributes (about 8% of columns), never surrogate keys |

## Checking depth

When the tool is available, run it after drafting and again after repairs, in
bounded passes:

```bash
python3 scripts/shape_profile.py advise MODEL --envelope templates/shape-envelope.json
python3 scripts/shape_profile.py check MODEL --envelope templates/shape-envelope.json --scope mvm --ignore-scale --format text
```

Without the tool, compare each product with its checklist and the metadata table
above. Report any section deliberately left out and the reason.
