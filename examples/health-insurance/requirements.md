# Teaching requirements

Modification notice: original requirements for the curated slice, not claims
that the seed satisfies these requirements.

| ID | Requirement | Verification |
|---|---|---|
| REQ-01 | Preserve member, plan, enrollment, provider, network, claim and ten products | Protected-name/count static check |
| REQ-02 | Valid keys and claim/coverage/participation dependency closure | PK, FK endpoint/type static checks |
| REQ-03 | Full glossary and explicit personal/health-data classification | Metadata/sensitivity presence checks; accuracy manual |
| REQ-04 | One single-source claim financial projection | Source/expression/dependency static checks |
| REQ-05 | Matched canonical JSON, SQL, and DBML | Deterministic file parity |
| REQ-06 | Review business cardinality, event snapshots, and temporal semantics | Manual architect review, not automated |

Out of scope: employer groups, billing, corporate workforce/finance, authorization,
EDI transactions, households/subscriber roles, pharmacy, licensed clinical code
vocabularies, full provider credentials, production reference data, sample rows,
deployment, and jurisdiction-specific legal review.

Assumptions for review: BIGINT identifiers are assigned upstream; the source
member/provider identifiers and declared business uniqueness tuples are reliable;
all claim amounts share the stated currency; coverage intervals use exclusive
ends; source versions are separate submissions, not necessarily unique claims.
No assumption is reported as data-verified.
