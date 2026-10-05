# Model evolution

Modification notice: source versioning/mutation principles are adapted; notebook
version aliases and automatic deploy/promote actions are excluded.

1. Preserve the input snapshot and its hash/version.
2. Classify requested changes: add, rename, relocate, merge, remove, resize, or
   change type/grain/temporal behavior.
3. Record requirement IDs and a new model version. Skill version and contract
   version are independent.
4. Compute dependency and consumer impact: FK endpoints, names, metrics, tags,
   DBML/docs, source mappings, samples if any, and live data migration needs.
5. Propose changes with explicit protected-name/count checks and rollback path.
6. Apply only approved changes to a new artifact set and verify all affected
   representations.

Shrink is a scope decision, not an automatic ratio to source size. Preserve
required process coverage and complete surviving entities. Enlarge retains
existing protected identities unless the user approves a redesign. Do not remove
associations simply to hit a global percentage.

A surrogate PK, natural key, FK, and event snapshot serve different purposes;
changing one can require data migration. `CREATE OR REPLACE TABLE` is not a safe
generic repair. `IF NOT EXISTS` protects against replacement but does not reconcile
schema drift. Existing workspace changes require their own authorization and
physical/data verification.

Deliver an adaptation log and requirement traceability alongside the new model.
Report `blocked` if a cycle policy and a protected relationship conflict, rather
than breaking the relationship to manufacture a pass.
