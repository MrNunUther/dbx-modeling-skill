# Source inventory and adaptation assessment

Modification notice: this package re-authors and reconciles source material.
Nothing here authorizes the source agent's operational commands.

## Sources

Upstream repositories: `databricks-agent-skills` and
`lakehouse-industry-data-models`. Local source paths were supplied by the user;
no source files were modified, uploaded, or made runtime dependencies.

| Source | Inventory | Use |
|---|---|---|
| `skills/databricks-dbsql` | Entry point, metadata, 2 icons, 5 references | Progressive disclosure and practical pattern form |
| `skills/databricks-unity-catalog` | Entry point, metadata, 2 icons, 7 references | Governance boundaries and UC mapping |
| `model-agent/rules/vibe-data-modelling-rules.csv` | 264 records, 263 distinct IDs, 22 groups | Canonical rule synthesis and occurrence mapping |
| `model-agent/rules/instructions.txt` | 452 lines, 434 nonblank lines, 18 themes | Portable workflow; original runtime instructions excluded |
| `data-models/health_insurance/v2/ecm/` | 52 files, 39,099,783 bytes | Selected business concepts, not wholesale exports |

The nonblank ledger accounting includes 3 introductory lines and 18 headings:
413 remaining instruction lines are individually dispositioned. Some portable
ideas were independently re-synthesized even when their original runtime wording
was excluded. `excluded` means that original line is not an active instruction;
it does not imply its underlying topic has no value.

Review included complete source rule enumeration, ledger themes, bounded relevant
skill references, full JSON structural enumeration, artifact counts, representative
SQL/DBML/Turtle excerpts, spreadsheet packaging/sheet dimensions, and export
comparisons. It was not an exhaustive SQL statement/cell-level or live-platform audit.

## Traceability

- [Source rule map](../rules/source-rule-map.csv): all 264 occurrences, using the
  parsed CSV record's ending physical line number to distinguish duplicate IDs.
- [Instruction map](../rules/source-instruction-map.csv): every nonblank line,
  original text/theme, disposition, portable target where applicable, and rationale.
- [Canonical catalog](../rules/modeling-rules.csv): 35 consolidated requirements.
  Source references use `source_ID@physical_line`; `MVP synthesis` denotes an
  independently introduced package/safety/contract rule.
- [Example adaptation log](../examples/health-insurance/adaptation-log.csv):
  retained concepts, new scope/grain, omitted dependencies, and corrections.

Dispositions are adopted, adapted, merged, deferred, excluded, or incomplete.
The current mapping predominantly uses `adapted`: it points to a reconciled
requirement, not a promise to enforce every original heuristic literally.
Future samples are deferred; incomplete source requirements remain incomplete.

## Observed inconsistencies

| Measure | Published summary | Enumerated JSON | Other evidence |
|---|---:|---:|---|
| Domains | 19 | 19 | 19 domain DDL files |
| Subdomains | 80 | 83 | Not reconciled |
| Products | 410 | 411 | 411 SQL table creations |
| Attributes | 13,044 | 13,069 | CSV has 13,044 attribute records |
| Declared product PKs | 411 | 411 | Not row uniqueness evidence |
| FK attributes | 1,528 | 1,534 | Export parity not established |
| Metric views | 225 | 287 | 225 SQL metric-view creations |

- Folder is `v2/ecm`; artifacts identify `v3_ecm`; SQL targets a `v1` catalog.
  Agent version is `4.3.3`, release version `0.8.0`: different version concepts.
- `model.domains` is the actual JSON shape, not the ledger's `model.model.domains`.
- 486 attribute logical/physical name pairs differ.
- Mixed product classifications/casing and structural PK tags require mapping.
- Corporate domains are 5/19 (26.3%), exceeding a source heuristic. This is not
  proof that the business model is invalid.
- DBML and text diagram are byte-identical. RDF-named and TTL-named exports are
  byte-identical Turtle, not independent serializations.
- Subscriber key types disagree between the DBML excerpt and JSON/SQL.
- Claim status metadata uses lowercase values; a metric compares uppercase
  `DENIED`. No such mismatch is propagated.
- Advertised sample directory is absent.
- Release notes admit warnings; next-vibe proposals and self-reported quality
  scores are not verified repairs.

Limited JSON checks found no missing product PK columns, unresolved declared FK
targets, type mismatches, or self-PK FKs. This does not establish graph policy,
business meaning, runtime compatibility, physical parity, or data integrity.

## Reconciliation decisions

| Conflict | Active policy |
|---|---|
| Duplicate `QGATE-RUL-011` | Distinct source occurrences map to editorial policy and bounded repair policy |
| Truncated ATT-RUL-069/070 | Mark incomplete; use corroborating 085/086, never invent missing text |
| Primitive versus complex types | Primitive enterprise-core MVP; alternate profiles deferred |
| Prefix prohibition versus contextual generic names | Semantic naming review; explicit physical names and collisions are hard checks |
| Lowercase versus case conversion | Only snake_case physical contract in MVP; alternate mappings deferred |
| Single-word/exactly-two-word names versus qualification | Word counts advisory; scoped uniqueness/ownership authoritative |
| Exactly one PK attribute versus at-least-one | One declared ordered PK tuple, including supported composite tuples |
| Name-suffix PK/FK inference | Explicit declaration; suffixes nominate review candidates only |
| DAG versus hierarchy exceptions | Declared graph policy; self-PK invalid; row hierarchy validation remains separate |
| Silos versus legitimate standalone/reference slices | Connectivity or explicit scope justification, never fabricated joins |
| Chronological FK prohibition versus pre-parent children | Nullable later FK with explicit enrichment path |
| Exactly three divisions versus industry taxonomies | Configurable taxonomy; ratios advisory |
| Automatic trimming/merging versus protected requirements | Dependency-aware proposals; never silent destructive fixes |
| Universal field completeness versus speculation/caps | Required current capabilities and grain; no padding |
| Empty tags versus glossary/ownership coverage | Separate classification and discovery metadata |
| Sensitivity tags as universal compliance law | Explicit policy/jurisdiction; tags never certify compliance |
| 90% glossary/adherence versus mandatory requirements | Full applicable delivered metadata; hard failures cannot hide in aggregate scores |
| Random FK ranges versus actual parent identity | Samples deferred; actual parent pools and deterministic integrity required later |
| ECM/MVM inconsistent meanings | Explicit `full_core`/`reduced_core`; source aliases preserved only in provenance |
| In-place mutation versus version barrier | Immutable input and new model snapshot |
| Single-source/no-joins claimed as platform rule | Single-source MVP boundary; Databricks metric views can support joins |
| 256-character width as platform limit | Advisory editorial width, not a UC engine limit |
| Runtime repair whitelist/log aliases | Bounded repair proposal and structured evidence, no original agent runtime |

## Fingerprints

Rechecked unchanged before implementation:

```text
instructions.txt
37a01b51a0c00d1ab8131617160743472867814d81cecec50489841224493b7f

vibe-data-modelling-rules.csv
fc7fca89c151a23d0e4d03327667c45b38fb82b9a90853366de23d5f9c5c5867

health_insurance/v2/ecm/model.json
d7e9c480227f5ca9da8b3ed5548abfc03ad9980c0e85c0d627762d10c1b8b21e
```

The original notebooks, helpers, jobs/profiles, deployment loops, cleaning
recipes, single-digit version rituals, implied approval, Git promotion, and
telemetry mechanisms are not imported. See [LICENSE](../LICENSE) and
[NOTICE](../NOTICE) before redistribution.
