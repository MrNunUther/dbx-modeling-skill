# dbx-modeling-skill

A standalone, domain-neutral enterprise modeling skill for Databricks. Start with
[SKILL.md](SKILL.md). Version: **0.1.0**.

## Installation and invocation

Copy this entire folder into an agent's supported skill location, keeping the
folder name `dbx-modeling-skill`. For example, a project supporting Agent Skills
can use `.agents/skills/dbx-modeling-skill/` or its documented host-specific
equivalent. Do not copy only the entrypoint: its relative references are required.
Host discovery paths vary; this package does not install itself or modify host
configuration. If auto-discovery is unavailable, explicitly load
[SKILL.md](SKILL.md) and the references it selects.

Example requests:

- "Use dbx-modeling-skill to model procurement from requisition through payment.
  Preserve the named purchasing and finance domains; no workspace execution."
- "Review this model for grain, FK semantics, snapshot preservation, and
  requirement coverage. Provide evidence-bearing findings; do not modify input."
- "Design a two-domain reduced core; keep my product names and do not expand it
  to meet division ratios."

## What's included

- [Task-oriented references](references/modeling-workflow.md), portable
  [instructions](rules/instructions.md), and [canonical rules](rules/modeling-rules.csv).
- [Model contract](templates/model.schema.json), [brief](templates/model-brief.json),
  [conventions](templates/conventions.json), and validation report templates.
- A corrected [health-insurance teaching suite](examples/health-insurance/README.md)
  with matched JSON, SQL, DBML, and traceability.
- Offline checks using maintained JSON Schema validation, standard-library
  tests, and deterministic example rendering. No Databricks credentials required.
- An [authorized-live-validation protocol](references/authorized-live-validation.md),
  not a live executor.
- Default shape guidance from a corpus-derived
  [shape envelope](references/shape-topology.md), covering product forms, an
  anti-pattern catalog, and model topology. It comes with
  `scripts/shape_profile.py`:
  - `advise` reviews any table, model, or bounded DDL and suggests remedies;
  - `check` and `targets` handle models and full MVM/ECM scopes;
  - `profile` and `build-envelope` support regeneration.

  The envelope is validated by leave-one-industry-out. See the
  [anti-pattern remodel](examples/anti-patterns/README.md) example.

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python scripts/validate_skill.py --root .
.venv/bin/python -m unittest discover -s tests -p 'test_*.py'
.venv/bin/python scripts/render_example.py --root . --check
```

The renderer accepts only the bounded example contract and performs no SQL
execution. After approved canonical-example changes, regenerate with
`.venv/bin/python scripts/render_example.py --root . --write`. Refresh the static report
with `.venv/bin/python scripts/validate_skill.py --root . --write-report`. Neither command
is a general-purpose legacy model importer.

## Evidence and limitations

Offline structural checks do not prove business correctness, runtime syntax,
access control, physical parity, or data integrity. The
[static report](examples/health-insurance/validation/static-report.json) explicitly
marks live checks `not_run`. No live validation, deployment, Git operations,
synthetic data generation, or autonomous repair is included.

The six teaching requirements include five statically checked requirements and
one manual semantics review. The denominator retains the manual item; the static
report is not an enterprise-readiness score.

Editorial workflow walkthroughs (not agent-host runtime evaluations):

| Request | Expected skill path |
|---|---|
| Minimal new enterprise core | Brief -> ownership/grain -> explicit keys -> matched artifacts -> evidence-level report |
| Existing-model review | Preserve input -> compare declared/observed facts -> report findings -> bounded change proposal |
| Protected names and tiny scope | Honor names/counts -> surface mapping conflicts -> no quota-driven expansion |

The test suite exercises structural cases and the protected/tiny-scope boundary.
Host-specific discovery and autonomous agent adherence remain future evaluations.

See [source assessment](references/source-assessment.md) for inventory, conflicts,
fingerprints, and rule/instruction dispositions. All derivative material is
reconciled/re-authored, not an unmodified upstream distribution.

## Maturation

After separate scope/authorization: read-only SDK verification, scratch
installation, additional industries/profiles,
legacy importers, workbook/ontology exports, host-runtime evaluations, and CI.
Do not treat this roadmap as implemented capability.

## Licensing

Use is restricted to use within or connection to Databricks Services under the
applicable agreement. This is **not** an Apache/MIT package or an official
Databricks product. Retain [LICENSE](LICENSE), [NOTICE](NOTICE), provenance, and
modification notices on redistribution. Neutral icons do not imply endorsement.
