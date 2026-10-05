# Modeling workflow

Modification notice: synthesized/adapted from the sources identified in
[source assessment](source-assessment.md); not the upstream agent's runtime rules.

## Establish the brief

Use [model-brief.json](../templates/model-brief.json). Record industry and
jurisdiction, current capabilities, operational sources if known, business
processes, explicit named objects, exact counts versus approximate targets,
out-of-scope areas, requested artifacts, and permitted actions.

Assign stable requirement IDs before design. An assumption is not a requirement;
record its status and the evidence needed to resolve it. Preserve verbatim user
names in the brief even when a separately approved physical mapping is necessary.
An "exactly N" request is different from "about N": ask about tolerance rather
than silently using the source agent's 20% range.

## Design sequence

1. Identify authoritative owners and current business processes.
2. Declare products and row grains. Distinguish parties, agreements, resources,
   reference data, transactions, events, and associations.
3. Define attributes and explicit keys in the common product form for the
   class. See [shape topology](shape-topology.md): body plan, attribute families,
   and archetypes.
4. Add relationships only after confirming their endpoints and business meaning.
5. Review process coverage and normalization, including temporal snapshots.
   Run `shape_profile.py advise` and resolve anti-pattern warnings by
   remodeling.
6. Add semantic metadata and physical mappings.
7. Produce matched artifacts and evidence-bearing review.

Read the [instructions](../rules/instructions.md) at the start of a modeling
task. Apply only relevant [rules](../rules/modeling-rules.csv). Defaults are in
[conventions.json](../templates/conventions.json); manual/advisory policies are
not automated quality gates.

## Review and changes

For a review, preserve input and report findings before proposing edits.
Shape review is part of every review. When you are given an existing or poorly
constructed table, run `advise` on it. Propose a common-form remodel with an
old-to-new column map instead of reproducing its shape. See the
[anti-pattern example](../examples/anti-patterns/README.md). For
changes, follow [evolution](model-evolution.md). Do not interpret `current_vibes`
or `next_vibes` proposals as actual user-approved requirements. Record requested,
proposed, applied, and verified states separately.

## Completion

Every required artifact must exist and agree with the canonical model. Report
coverage at the achieved evidence level and list blocked/unverified requirements.
Stop on ambiguous ownership/grain or a protected request that cannot satisfy
structural validity. Do not manufacture tables or drop requirements to obtain a
passing score.
