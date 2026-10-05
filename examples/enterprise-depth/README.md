# Enterprise depth: finished products

[claim.sql](claim.sql) shows two products at the depth this skill produces by
default. It is illustrative, not real data or a certified model.

| Product | Class | Columns | References | What makes it complete |
|---|---|---|---|---|
| `member.member` | Master | 32 | 3 (household, address, language) | Identification, source reconciliation, legal name parts, classification codes, lifecycle with status reason and date, contact with consent, eligibility flags, risk measure, version number, audit |
| `claim.claim` | Transactional | 42 | 8 (member, coverage, billing and rendering provider, facility, network, channel, original claim) | Document numbers, type and frequency classifiers, status with a timestamp per state, service and inpatient dates, prompt-pay due date, DECIMAL amounts with currency, counts and durations, flags, source, audit |

Every column answers a question from claims intake, adjudication, payment,
prompt-pay reporting, or reconciliation; none is a placeholder. Descriptions
state meaning plus rule or use, and product comments state purpose, grain,
lifecycle, consumers, and what is out of bounds.

Compare with the deliberately thin
[remodel](../anti-patterns/claim_remodeled.sql), which has 15 columns on
`claim`, and the [teaching slice](../health-insurance/README.md).

## Run it

```bash
python3 scripts/shape_profile.py advise examples/enterprise-depth/claim.sql --envelope templates/shape-envelope.json
python3 scripts/shape_profile.py check examples/enterprise-depth/claim.sql --envelope templates/shape-envelope.json --scope mvm --ignore-scale --format text
```

Expected results:

- **advise:** both products are inferred correctly, with 0 warnings and 0
  advisories.
- **check:** product score 100 (conformance 1.0, depth fit 1.0).

The model topology score is low only because two products are not a model.

Guidance: [enterprise depth](../../references/enterprise-depth.md).
