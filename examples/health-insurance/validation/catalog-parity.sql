-- Re-authored teaching artifact; see adaptation-log.csv and NOTICE.
-- NOT EXECUTED. Substitute reviewed __CATALOG__ offline before authorized use.
-- Expected table/column comparisons; remaining metadata queries require explicit review.
WITH expected(schema_name, table_name) AS (VALUES
  ('member', 'identity'),
  ('plan', 'health_plan'),
  ('enrollment', 'coverage'),
  ('provider', 'provider'),
  ('network', 'provider_network'),
  ('network', 'participation'),
  ('claim', 'claim_status'),
  ('claim', 'header'),
  ('claim', 'line'),
  ('claim', 'adjudication'))
SELECT e.*, CASE WHEN t.table_name IS NULL THEN 'missing_or_invisible' ELSE 'present' END AS observed
FROM expected e LEFT JOIN `__CATALOG__`.information_schema.tables t
ON t.table_schema = e.schema_name AND t.table_name = e.table_name;

WITH expected(schema_name, table_name, column_name, ordinal_position, full_type, nullable) AS (VALUES
  ('member', 'identity', 'identity_id', 1, 'BIGINT', 'NO'),
  ('member', 'identity', 'source_member_number', 2, 'STRING', 'NO'),
  ('member', 'identity', 'given_name', 3, 'STRING', 'NO'),
  ('member', 'identity', 'family_name', 4, 'STRING', 'NO'),
  ('member', 'identity', 'date_of_birth', 5, 'DATE', 'NO'),
  ('member', 'identity', 'identity_status', 6, 'STRING', 'NO'),
  ('member', 'identity', 'created_at', 7, 'TIMESTAMP', 'NO'),
  ('plan', 'health_plan', 'health_plan_id', 1, 'BIGINT', 'NO'),
  ('plan', 'health_plan', 'plan_code', 2, 'STRING', 'NO'),
  ('plan', 'health_plan', 'design_version', 3, 'INT', 'NO'),
  ('plan', 'health_plan', 'plan_name', 4, 'STRING', 'NO'),
  ('plan', 'health_plan', 'effective_from', 5, 'DATE', 'NO'),
  ('plan', 'health_plan', 'effective_to', 6, 'DATE', 'YES'),
  ('plan', 'health_plan', 'currency_code', 7, 'STRING', 'NO'),
  ('plan', 'health_plan', 'deductible_amount', 8, 'DECIMAL(18,2)', 'NO'),
  ('enrollment', 'coverage', 'coverage_id', 1, 'BIGINT', 'NO'),
  ('enrollment', 'coverage', 'identity_id', 2, 'BIGINT', 'NO'),
  ('enrollment', 'coverage', 'health_plan_id', 3, 'BIGINT', 'NO'),
  ('enrollment', 'coverage', 'coverage_from', 4, 'DATE', 'NO'),
  ('enrollment', 'coverage', 'coverage_to', 5, 'DATE', 'YES'),
  ('enrollment', 'coverage', 'coverage_status', 6, 'STRING', 'NO'),
  ('enrollment', 'coverage', 'elected_at', 7, 'TIMESTAMP', 'NO'),
  ('provider', 'provider', 'provider_id', 1, 'BIGINT', 'NO'),
  ('provider', 'provider', 'provider_number', 2, 'STRING', 'NO'),
  ('provider', 'provider', 'provider_name', 3, 'STRING', 'NO'),
  ('provider', 'provider', 'provider_kind', 4, 'STRING', 'NO'),
  ('provider', 'provider', 'provider_status', 5, 'STRING', 'NO'),
  ('provider', 'provider', 'created_at', 6, 'TIMESTAMP', 'NO'),
  ('network', 'provider_network', 'provider_network_id', 1, 'BIGINT', 'NO'),
  ('network', 'provider_network', 'network_code', 2, 'STRING', 'NO'),
  ('network', 'provider_network', 'network_name', 3, 'STRING', 'NO'),
  ('network', 'provider_network', 'network_status', 4, 'STRING', 'NO'),
  ('network', 'participation', 'participation_id', 1, 'BIGINT', 'NO'),
  ('network', 'participation', 'provider_id', 2, 'BIGINT', 'NO'),
  ('network', 'participation', 'provider_network_id', 3, 'BIGINT', 'NO'),
  ('network', 'participation', 'participation_from', 4, 'DATE', 'NO'),
  ('network', 'participation', 'participation_to', 5, 'DATE', 'YES'),
  ('network', 'participation', 'participation_status', 6, 'STRING', 'NO'),
  ('network', 'participation', 'created_at', 7, 'TIMESTAMP', 'NO'),
  ('claim', 'claim_status', 'claim_status_id', 1, 'BIGINT', 'NO'),
  ('claim', 'claim_status', 'status_code', 2, 'STRING', 'NO'),
  ('claim', 'claim_status', 'status_label', 3, 'STRING', 'NO'),
  ('claim', 'claim_status', 'is_terminal', 4, 'BOOLEAN', 'NO'),
  ('claim', 'header', 'header_id', 1, 'BIGINT', 'NO'),
  ('claim', 'header', 'coverage_id', 2, 'BIGINT', 'NO'),
  ('claim', 'header', 'billing_provider_id', 3, 'BIGINT', 'NO'),
  ('claim', 'header', 'rendering_provider_id', 4, 'BIGINT', 'YES'),
  ('claim', 'header', 'claim_status_id', 5, 'BIGINT', 'NO'),
  ('claim', 'header', 'claim_number', 6, 'STRING', 'NO'),
  ('claim', 'header', 'submission_version', 7, 'INT', 'NO'),
  ('claim', 'header', 'received_at', 8, 'TIMESTAMP', 'NO'),
  ('claim', 'header', 'service_date', 9, 'DATE', 'NO'),
  ('claim', 'header', 'currency_code', 10, 'STRING', 'NO'),
  ('claim', 'header', 'billed_amount', 11, 'DECIMAL(18,2)', 'NO'),
  ('claim', 'header', 'allowed_amount', 12, 'DECIMAL(18,2)', 'YES'),
  ('claim', 'header', 'paid_amount', 13, 'DECIMAL(18,2)', 'YES'),
  ('claim', 'line', 'line_id', 1, 'BIGINT', 'NO'),
  ('claim', 'line', 'header_id', 2, 'BIGINT', 'NO'),
  ('claim', 'line', 'line_number', 3, 'INT', 'NO'),
  ('claim', 'line', 'service_code', 4, 'STRING', 'NO'),
  ('claim', 'line', 'service_date', 5, 'DATE', 'NO'),
  ('claim', 'line', 'service_quantity', 6, 'DECIMAL(12,3)', 'NO'),
  ('claim', 'line', 'unit_price_at_service', 7, 'DECIMAL(18,2)', 'NO'),
  ('claim', 'adjudication', 'adjudication_id', 1, 'BIGINT', 'NO'),
  ('claim', 'adjudication', 'header_id', 2, 'BIGINT', 'NO'),
  ('claim', 'adjudication', 'decided_at', 3, 'TIMESTAMP', 'NO'),
  ('claim', 'adjudication', 'decision_outcome', 4, 'STRING', 'NO'),
  ('claim', 'adjudication', 'decision_reason', 5, 'STRING', 'NO'),
  ('claim', 'adjudication', 'allowed_amount_at_decision', 6, 'DECIMAL(18,2)', 'YES'))
SELECT e.*, c.full_data_type AS observed_type, c.is_nullable AS observed_nullable
FROM expected e LEFT JOIN `__CATALOG__`.information_schema.columns c
ON c.table_schema = e.schema_name AND c.table_name = e.table_name AND c.column_name = e.column_name
WHERE c.column_name IS NULL OR UPPER(REPLACE(c.full_data_type, ' ', '')) <> e.full_type
OR c.is_nullable <> e.nullable OR c.ordinal_position <> e.ordinal_position;

-- Inspect all tuple positions and referenced declarations; absence can be a visibility gap.
SELECT * FROM `__CATALOG__`.information_schema.table_constraints;
SELECT * FROM `__CATALOG__`.information_schema.key_column_usage;
SELECT * FROM `__CATALOG__`.information_schema.referential_constraints;
SELECT * FROM `__CATALOG__`.information_schema.column_tags;
SELECT * FROM `__CATALOG__`.information_schema.table_tags;
-- Verify metric-view definitions with SHOW CREATE TABLE for each declared metric object.
SHOW CREATE TABLE `__CATALOG__`.`metrics`.`claim_financials`;
