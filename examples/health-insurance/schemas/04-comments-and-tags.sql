-- Re-authored teaching artifact; see adaptation-log.csv and NOTICE.
-- NOT EXECUTED. Substitute reviewed __CATALOG__ offline before authorized use.


ALTER SCHEMA `__CATALOG__`.`member` SET TAGS ('dbx_division' = 'business');

ALTER TABLE `__CATALOG__`.`member`.`identity` SET TAGS ('dbx_data_type' = 'master_data', 'dbx_steward' = 'example_data_stewards', 'dbx_subdomain' = 'person_identity');

ALTER TABLE `__CATALOG__`.`member`.`identity` ALTER COLUMN `identity_id` SET TAGS ('dbx_business_glossary_term' = 'Identity Identifier', 'dbx_classification' = 'restricted', 'sensitivity' = 'personal');

ALTER TABLE `__CATALOG__`.`member`.`identity` ALTER COLUMN `source_member_number` SET TAGS ('dbx_business_glossary_term' = 'Source Member Number', 'dbx_classification' = 'restricted', 'sensitivity' = 'personal');

ALTER TABLE `__CATALOG__`.`member`.`identity` ALTER COLUMN `given_name` SET TAGS ('dbx_business_glossary_term' = 'Given Name', 'dbx_classification' = 'restricted', 'sensitivity' = 'personal');

ALTER TABLE `__CATALOG__`.`member`.`identity` ALTER COLUMN `family_name` SET TAGS ('dbx_business_glossary_term' = 'Family Name', 'dbx_classification' = 'restricted', 'sensitivity' = 'personal');

ALTER TABLE `__CATALOG__`.`member`.`identity` ALTER COLUMN `date_of_birth` SET TAGS ('dbx_business_glossary_term' = 'Date Of Birth', 'dbx_classification' = 'restricted', 'sensitivity' = 'personal');

ALTER TABLE `__CATALOG__`.`member`.`identity` ALTER COLUMN `identity_status` SET TAGS ('dbx_business_glossary_term' = 'Identity Status', 'dbx_classification' = 'restricted', 'sensitivity' = 'personal');

ALTER TABLE `__CATALOG__`.`member`.`identity` ALTER COLUMN `created_at` SET TAGS ('dbx_business_glossary_term' = 'Created At', 'dbx_classification' = 'restricted', 'sensitivity' = 'personal');

ALTER SCHEMA `__CATALOG__`.`plan` SET TAGS ('dbx_division' = 'business');

ALTER TABLE `__CATALOG__`.`plan`.`health_plan` SET TAGS ('dbx_data_type' = 'master_data', 'dbx_steward' = 'example_data_stewards', 'dbx_subdomain' = 'plan_design');

ALTER TABLE `__CATALOG__`.`plan`.`health_plan` ALTER COLUMN `health_plan_id` SET TAGS ('dbx_business_glossary_term' = 'Health Plan Identifier', 'dbx_classification' = 'internal');

ALTER TABLE `__CATALOG__`.`plan`.`health_plan` ALTER COLUMN `plan_code` SET TAGS ('dbx_business_glossary_term' = 'Plan Code', 'dbx_classification' = 'internal');

ALTER TABLE `__CATALOG__`.`plan`.`health_plan` ALTER COLUMN `design_version` SET TAGS ('dbx_business_glossary_term' = 'Design Version', 'dbx_classification' = 'internal');

ALTER TABLE `__CATALOG__`.`plan`.`health_plan` ALTER COLUMN `plan_name` SET TAGS ('dbx_business_glossary_term' = 'Plan Name', 'dbx_classification' = 'internal');

ALTER TABLE `__CATALOG__`.`plan`.`health_plan` ALTER COLUMN `effective_from` SET TAGS ('dbx_business_glossary_term' = 'Effective From', 'dbx_classification' = 'internal');

ALTER TABLE `__CATALOG__`.`plan`.`health_plan` ALTER COLUMN `effective_to` SET TAGS ('dbx_business_glossary_term' = 'Effective To', 'dbx_classification' = 'internal');

ALTER TABLE `__CATALOG__`.`plan`.`health_plan` ALTER COLUMN `currency_code` SET TAGS ('dbx_business_glossary_term' = 'Currency Code', 'dbx_classification' = 'internal', 'dbx_standard_references' = 'ISO 4217 currency codes');

ALTER TABLE `__CATALOG__`.`plan`.`health_plan` ALTER COLUMN `deductible_amount` SET TAGS ('dbx_business_glossary_term' = 'Deductible Amount', 'dbx_classification' = 'internal');

ALTER SCHEMA `__CATALOG__`.`enrollment` SET TAGS ('dbx_division' = 'operations');

ALTER TABLE `__CATALOG__`.`enrollment`.`coverage` SET TAGS ('dbx_data_type' = 'transactional_data', 'dbx_steward' = 'example_data_stewards', 'dbx_subdomain' = 'coverage_management');

ALTER TABLE `__CATALOG__`.`enrollment`.`coverage` ALTER COLUMN `coverage_id` SET TAGS ('dbx_business_glossary_term' = 'Coverage Identifier', 'dbx_classification' = 'restricted', 'sensitivity' = 'health');

ALTER TABLE `__CATALOG__`.`enrollment`.`coverage` ALTER COLUMN `identity_id` SET TAGS ('dbx_business_glossary_term' = 'Identity Identifier', 'dbx_classification' = 'restricted', 'sensitivity' = 'health');

ALTER TABLE `__CATALOG__`.`enrollment`.`coverage` ALTER COLUMN `health_plan_id` SET TAGS ('dbx_business_glossary_term' = 'Health Plan Identifier', 'dbx_classification' = 'restricted', 'sensitivity' = 'health');

ALTER TABLE `__CATALOG__`.`enrollment`.`coverage` ALTER COLUMN `coverage_from` SET TAGS ('dbx_business_glossary_term' = 'Coverage From', 'dbx_classification' = 'restricted', 'sensitivity' = 'health');

ALTER TABLE `__CATALOG__`.`enrollment`.`coverage` ALTER COLUMN `coverage_to` SET TAGS ('dbx_business_glossary_term' = 'Coverage To', 'dbx_classification' = 'restricted', 'sensitivity' = 'health');

ALTER TABLE `__CATALOG__`.`enrollment`.`coverage` ALTER COLUMN `coverage_status` SET TAGS ('dbx_business_glossary_term' = 'Coverage Status', 'dbx_classification' = 'restricted', 'sensitivity' = 'health');

ALTER TABLE `__CATALOG__`.`enrollment`.`coverage` ALTER COLUMN `elected_at` SET TAGS ('dbx_business_glossary_term' = 'Elected At', 'dbx_classification' = 'restricted', 'sensitivity' = 'health');

ALTER SCHEMA `__CATALOG__`.`provider` SET TAGS ('dbx_division' = 'operations');

ALTER TABLE `__CATALOG__`.`provider`.`provider` SET TAGS ('dbx_data_type' = 'master_data', 'dbx_steward' = 'example_data_stewards', 'dbx_subdomain' = 'provider_identity');

ALTER TABLE `__CATALOG__`.`provider`.`provider` ALTER COLUMN `provider_id` SET TAGS ('dbx_business_glossary_term' = 'Provider Identifier', 'dbx_classification' = 'internal');

ALTER TABLE `__CATALOG__`.`provider`.`provider` ALTER COLUMN `provider_number` SET TAGS ('dbx_business_glossary_term' = 'Provider Number', 'dbx_classification' = 'internal');

ALTER TABLE `__CATALOG__`.`provider`.`provider` ALTER COLUMN `provider_name` SET TAGS ('dbx_business_glossary_term' = 'Provider Name', 'dbx_classification' = 'restricted', 'sensitivity' = 'personal');

ALTER TABLE `__CATALOG__`.`provider`.`provider` ALTER COLUMN `provider_kind` SET TAGS ('dbx_business_glossary_term' = 'Provider Kind', 'dbx_classification' = 'internal');

ALTER TABLE `__CATALOG__`.`provider`.`provider` ALTER COLUMN `provider_status` SET TAGS ('dbx_business_glossary_term' = 'Provider Status', 'dbx_classification' = 'internal');

ALTER TABLE `__CATALOG__`.`provider`.`provider` ALTER COLUMN `created_at` SET TAGS ('dbx_business_glossary_term' = 'Created At', 'dbx_classification' = 'internal');

ALTER SCHEMA `__CATALOG__`.`network` SET TAGS ('dbx_division' = 'operations');

ALTER TABLE `__CATALOG__`.`network`.`provider_network` SET TAGS ('dbx_data_type' = 'master_data', 'dbx_steward' = 'example_data_stewards', 'dbx_subdomain' = 'network_participation');

ALTER TABLE `__CATALOG__`.`network`.`provider_network` ALTER COLUMN `provider_network_id` SET TAGS ('dbx_business_glossary_term' = 'Provider Network Identifier', 'dbx_classification' = 'internal');

ALTER TABLE `__CATALOG__`.`network`.`provider_network` ALTER COLUMN `network_code` SET TAGS ('dbx_business_glossary_term' = 'Network Code', 'dbx_classification' = 'internal');

ALTER TABLE `__CATALOG__`.`network`.`provider_network` ALTER COLUMN `network_name` SET TAGS ('dbx_business_glossary_term' = 'Network Name', 'dbx_classification' = 'internal');

ALTER TABLE `__CATALOG__`.`network`.`provider_network` ALTER COLUMN `network_status` SET TAGS ('dbx_business_glossary_term' = 'Network Status', 'dbx_classification' = 'internal');

ALTER TABLE `__CATALOG__`.`network`.`participation` SET TAGS ('dbx_data_type' = 'association_data', 'dbx_steward' = 'example_data_stewards', 'dbx_subdomain' = 'network_participation');

ALTER TABLE `__CATALOG__`.`network`.`participation` ALTER COLUMN `participation_id` SET TAGS ('dbx_business_glossary_term' = 'Participation Identifier', 'dbx_classification' = 'internal');

ALTER TABLE `__CATALOG__`.`network`.`participation` ALTER COLUMN `provider_id` SET TAGS ('dbx_business_glossary_term' = 'Provider Identifier', 'dbx_classification' = 'internal');

ALTER TABLE `__CATALOG__`.`network`.`participation` ALTER COLUMN `provider_network_id` SET TAGS ('dbx_business_glossary_term' = 'Provider Network Identifier', 'dbx_classification' = 'internal');

ALTER TABLE `__CATALOG__`.`network`.`participation` ALTER COLUMN `participation_from` SET TAGS ('dbx_business_glossary_term' = 'Participation From', 'dbx_classification' = 'internal');

ALTER TABLE `__CATALOG__`.`network`.`participation` ALTER COLUMN `participation_to` SET TAGS ('dbx_business_glossary_term' = 'Participation To', 'dbx_classification' = 'internal');

ALTER TABLE `__CATALOG__`.`network`.`participation` ALTER COLUMN `participation_status` SET TAGS ('dbx_business_glossary_term' = 'Participation Status', 'dbx_classification' = 'internal');

ALTER TABLE `__CATALOG__`.`network`.`participation` ALTER COLUMN `created_at` SET TAGS ('dbx_business_glossary_term' = 'Created At', 'dbx_classification' = 'internal');

ALTER SCHEMA `__CATALOG__`.`claim` SET TAGS ('dbx_division' = 'operations');

ALTER TABLE `__CATALOG__`.`claim`.`claim_status` SET TAGS ('dbx_data_type' = 'reference_data', 'dbx_steward' = 'example_data_stewards', 'dbx_subdomain' = 'claim_processing');

ALTER TABLE `__CATALOG__`.`claim`.`claim_status` ALTER COLUMN `claim_status_id` SET TAGS ('dbx_business_glossary_term' = 'Claim Status Identifier', 'dbx_classification' = 'internal');

ALTER TABLE `__CATALOG__`.`claim`.`claim_status` ALTER COLUMN `status_code` SET TAGS ('dbx_business_glossary_term' = 'Status Code', 'dbx_classification' = 'internal');

ALTER TABLE `__CATALOG__`.`claim`.`claim_status` ALTER COLUMN `status_label` SET TAGS ('dbx_business_glossary_term' = 'Status Label', 'dbx_classification' = 'internal');

ALTER TABLE `__CATALOG__`.`claim`.`claim_status` ALTER COLUMN `is_terminal` SET TAGS ('dbx_business_glossary_term' = 'Is Terminal', 'dbx_classification' = 'internal');

ALTER TABLE `__CATALOG__`.`claim`.`header` SET TAGS ('dbx_data_type' = 'transactional_data', 'dbx_steward' = 'example_data_stewards', 'dbx_subdomain' = 'claim_processing');

ALTER TABLE `__CATALOG__`.`claim`.`header` ALTER COLUMN `header_id` SET TAGS ('dbx_business_glossary_term' = 'Header Identifier', 'dbx_classification' = 'restricted', 'sensitivity' = 'health');

ALTER TABLE `__CATALOG__`.`claim`.`header` ALTER COLUMN `coverage_id` SET TAGS ('dbx_business_glossary_term' = 'Coverage Identifier', 'dbx_classification' = 'restricted', 'sensitivity' = 'health');

ALTER TABLE `__CATALOG__`.`claim`.`header` ALTER COLUMN `billing_provider_id` SET TAGS ('dbx_business_glossary_term' = 'Billing Provider Identifier', 'dbx_classification' = 'restricted', 'sensitivity' = 'health');

ALTER TABLE `__CATALOG__`.`claim`.`header` ALTER COLUMN `rendering_provider_id` SET TAGS ('dbx_business_glossary_term' = 'Rendering Provider Identifier', 'dbx_classification' = 'restricted', 'sensitivity' = 'health');

ALTER TABLE `__CATALOG__`.`claim`.`header` ALTER COLUMN `claim_status_id` SET TAGS ('dbx_business_glossary_term' = 'Claim Status Identifier', 'dbx_classification' = 'restricted', 'sensitivity' = 'health');

ALTER TABLE `__CATALOG__`.`claim`.`header` ALTER COLUMN `claim_number` SET TAGS ('dbx_business_glossary_term' = 'Claim Number', 'dbx_classification' = 'restricted', 'sensitivity' = 'health');

ALTER TABLE `__CATALOG__`.`claim`.`header` ALTER COLUMN `submission_version` SET TAGS ('dbx_business_glossary_term' = 'Submission Version', 'dbx_classification' = 'restricted', 'sensitivity' = 'health');

ALTER TABLE `__CATALOG__`.`claim`.`header` ALTER COLUMN `received_at` SET TAGS ('dbx_business_glossary_term' = 'Received At', 'dbx_classification' = 'restricted', 'sensitivity' = 'health');

ALTER TABLE `__CATALOG__`.`claim`.`header` ALTER COLUMN `service_date` SET TAGS ('dbx_business_glossary_term' = 'Service Date', 'dbx_classification' = 'restricted', 'sensitivity' = 'health');

ALTER TABLE `__CATALOG__`.`claim`.`header` ALTER COLUMN `currency_code` SET TAGS ('dbx_business_glossary_term' = 'Currency Code', 'dbx_classification' = 'restricted', 'dbx_standard_references' = 'ISO 4217 currency codes', 'sensitivity' = 'health');

ALTER TABLE `__CATALOG__`.`claim`.`header` ALTER COLUMN `billed_amount` SET TAGS ('dbx_business_glossary_term' = 'Billed Amount', 'dbx_classification' = 'restricted', 'sensitivity' = 'health');

ALTER TABLE `__CATALOG__`.`claim`.`header` ALTER COLUMN `allowed_amount` SET TAGS ('dbx_business_glossary_term' = 'Allowed Amount', 'dbx_classification' = 'restricted', 'sensitivity' = 'health');

ALTER TABLE `__CATALOG__`.`claim`.`header` ALTER COLUMN `paid_amount` SET TAGS ('dbx_business_glossary_term' = 'Paid Amount', 'dbx_classification' = 'restricted', 'sensitivity' = 'health');

ALTER TABLE `__CATALOG__`.`claim`.`line` SET TAGS ('dbx_data_type' = 'transactional_data', 'dbx_steward' = 'example_data_stewards', 'dbx_subdomain' = 'claim_processing');

ALTER TABLE `__CATALOG__`.`claim`.`line` ALTER COLUMN `line_id` SET TAGS ('dbx_business_glossary_term' = 'Line Identifier', 'dbx_classification' = 'restricted', 'sensitivity' = 'health');

ALTER TABLE `__CATALOG__`.`claim`.`line` ALTER COLUMN `header_id` SET TAGS ('dbx_business_glossary_term' = 'Header Identifier', 'dbx_classification' = 'restricted', 'sensitivity' = 'health');

ALTER TABLE `__CATALOG__`.`claim`.`line` ALTER COLUMN `line_number` SET TAGS ('dbx_business_glossary_term' = 'Line Number', 'dbx_classification' = 'restricted', 'sensitivity' = 'health');

ALTER TABLE `__CATALOG__`.`claim`.`line` ALTER COLUMN `service_code` SET TAGS ('dbx_business_glossary_term' = 'Service Code', 'dbx_classification' = 'restricted', 'sensitivity' = 'health');

ALTER TABLE `__CATALOG__`.`claim`.`line` ALTER COLUMN `service_date` SET TAGS ('dbx_business_glossary_term' = 'Service Date', 'dbx_classification' = 'restricted', 'sensitivity' = 'health');

ALTER TABLE `__CATALOG__`.`claim`.`line` ALTER COLUMN `service_quantity` SET TAGS ('dbx_business_glossary_term' = 'Service Quantity', 'dbx_classification' = 'restricted', 'sensitivity' = 'health');

ALTER TABLE `__CATALOG__`.`claim`.`line` ALTER COLUMN `unit_price_at_service` SET TAGS ('dbx_business_glossary_term' = 'Unit Price At Service', 'dbx_classification' = 'restricted', 'sensitivity' = 'health');

ALTER TABLE `__CATALOG__`.`claim`.`adjudication` SET TAGS ('dbx_data_type' = 'transactional_data', 'dbx_steward' = 'example_data_stewards', 'dbx_subdomain' = 'claim_processing');

ALTER TABLE `__CATALOG__`.`claim`.`adjudication` ALTER COLUMN `adjudication_id` SET TAGS ('dbx_business_glossary_term' = 'Adjudication Identifier', 'dbx_classification' = 'restricted', 'sensitivity' = 'health');

ALTER TABLE `__CATALOG__`.`claim`.`adjudication` ALTER COLUMN `header_id` SET TAGS ('dbx_business_glossary_term' = 'Header Identifier', 'dbx_classification' = 'restricted', 'sensitivity' = 'health');

ALTER TABLE `__CATALOG__`.`claim`.`adjudication` ALTER COLUMN `decided_at` SET TAGS ('dbx_business_glossary_term' = 'Decided At', 'dbx_classification' = 'restricted', 'sensitivity' = 'health');

ALTER TABLE `__CATALOG__`.`claim`.`adjudication` ALTER COLUMN `decision_outcome` SET TAGS ('dbx_business_glossary_term' = 'Decision Outcome', 'dbx_classification' = 'restricted', 'sensitivity' = 'health');

ALTER TABLE `__CATALOG__`.`claim`.`adjudication` ALTER COLUMN `decision_reason` SET TAGS ('dbx_business_glossary_term' = 'Decision Reason', 'dbx_classification' = 'restricted', 'sensitivity' = 'health');

ALTER TABLE `__CATALOG__`.`claim`.`adjudication` ALTER COLUMN `allowed_amount_at_decision` SET TAGS ('dbx_business_glossary_term' = 'Allowed Amount At Decision', 'dbx_classification' = 'restricted', 'sensitivity' = 'health');
