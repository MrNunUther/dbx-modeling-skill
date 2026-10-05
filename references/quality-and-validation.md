# Quality and validation

Modification notice: adapts the source's evidence discipline without importing
its agent runtime, repair whitelist, or 90% success shortcut.

## Authority and evidence

Hard gates cannot be overridden by heuristic preferences or free text. Profile
policies may have recorded exceptions; advisory heuristics need architect review.
See the [rule catalog](../rules/modeling-rules.csv): `Check_ID=manual` means no
automated implementation. Automated checks cover the bounded MVP contract only.

| Evidence level | What it proves |
|---|---|
| designed | Artifact/intent exists, not verified |
| static | Explicit local structural/representation checks passed |
| workspace | Authorized syntax/object creation checks passed |
| physical | Authorized catalog metadata parity checks passed |
| data | Authorized row-integrity checks passed |

Each check has expected/observed evidence, object/rule ID, severity, and remediation.
`blocked` is inability to determine, `not_run` is not attempted, and
`not_applicable` needs an applicability reason. Missing visibility must not
masquerade as an empty catalog or successful parity.

## Offline validator boundaries

[validate_skill.py](../scripts/validate_skill.py) checks the explicit canonical
shape, monetary precision, types, keys, references, graph policy, metadata, protected scope, supported
metric-expression dependency declarations, rules/maps, package links, and exact
deterministic example outputs.

It validates shape using the maintained `jsonschema` dependency and rejects
undocumented contract fields and unsupported metric expressions.
This is intentionally not a full SQL/YAML parser, a legacy importer,
or a general business-correctness checker. Explicit attribute sensitivity flags
are checked; deciding whether unmarked fields are actually sensitive is manual.
Snapshot/redundancy semantics, process completeness, and regulatory context are
also manual. Generated output parity is local file parity, not live catalog parity.
The current report validator rejects elevated/live evidence claims; a future
authorized verifier must independently validate workspace evidence before
accepting those report levels.

Use [validation-report.json](../templates/validation-report.json) and its
[schema](../templates/validation-report.schema.json). The shipped report records
actual static checks and the checks not run. Report errors explicitly and exit
nonzero on failed hard/profile checks; never silently recover malformed input.

## Requirement coverage

For each requirement, link object/artifact IDs and applicable automated/manual
checks. Static coverage counts only requirements whose mapped automated checks
pass for the specified objects. Manual semantic reviews are separate and must
remain visible. Use `verified / applicable` for the selected evidence level;
do not exclude blocked requirements to inflate the denominator.

An automated check of glossary presence cannot prove glossary accuracy.
100% structural coverage does not imply 100% business coverage. A 90% aggregate
score never excuses a failed hard gate or omitted required object.

## Repair contract

Provide a bounded proposal with cause, impact, protected intent, and tests.
Preserve inputs and version the result. Stop if the proposal changes business
semantics without approval. Re-run affected checks after approved repair; leave
manual/live checks unresolved until the required evidence exists.
