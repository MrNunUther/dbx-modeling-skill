-- Re-authored teaching artifact; see adaptation-log.csv and NOTICE.
-- NOT EXECUTED. Substitute reviewed __CATALOG__ offline before authorized use.


-- Run only after existence/visibility checks; zero violations is not existence proof.

SELECT 'member.identity.identity_status:enum' AS check_id, COUNT(*) AS violations FROM `__CATALOG__`.`member`.`identity` WHERE `identity_status` IS NOT NULL AND `identity_status` NOT IN ('active', 'inactive');

SELECT 'member.identity:pk_null' AS check_id, COUNT(*) AS violations FROM `__CATALOG__`.`member`.`identity` WHERE `identity_id` IS NULL;

SELECT 'member.identity:unique_0' AS check_id, COUNT(*) AS violating_groups FROM (SELECT `identity_id` FROM `__CATALOG__`.`member`.`identity` GROUP BY `identity_id` HAVING COUNT(*) > 1);

SELECT 'member.identity:unique_1' AS check_id, COUNT(*) AS violating_groups FROM (SELECT `source_member_number` FROM `__CATALOG__`.`member`.`identity` GROUP BY `source_member_number` HAVING COUNT(*) > 1);

SELECT 'plan.health_plan.currency_code:pattern' AS check_id, COUNT(*) AS violations FROM `__CATALOG__`.`plan`.`health_plan` WHERE `currency_code` IS NOT NULL AND NOT (`currency_code` RLIKE '^[A-Z]{3}$');

SELECT 'plan.health_plan:pk_null' AS check_id, COUNT(*) AS violations FROM `__CATALOG__`.`plan`.`health_plan` WHERE `health_plan_id` IS NULL;

SELECT 'plan.health_plan:unique_0' AS check_id, COUNT(*) AS violating_groups FROM (SELECT `health_plan_id` FROM `__CATALOG__`.`plan`.`health_plan` GROUP BY `health_plan_id` HAVING COUNT(*) > 1);

SELECT 'plan.health_plan:unique_1' AS check_id, COUNT(*) AS violating_groups FROM (SELECT `plan_code`, `design_version` FROM `__CATALOG__`.`plan`.`health_plan` GROUP BY `plan_code`, `design_version` HAVING COUNT(*) > 1);

SELECT 'enrollment.coverage.coverage_status:enum' AS check_id, COUNT(*) AS violations FROM `__CATALOG__`.`enrollment`.`coverage` WHERE `coverage_status` IS NOT NULL AND `coverage_status` NOT IN ('active', 'terminated', 'pending');

SELECT 'enrollment.coverage:pk_null' AS check_id, COUNT(*) AS violations FROM `__CATALOG__`.`enrollment`.`coverage` WHERE `coverage_id` IS NULL;

SELECT 'enrollment.coverage:unique_0' AS check_id, COUNT(*) AS violating_groups FROM (SELECT `coverage_id` FROM `__CATALOG__`.`enrollment`.`coverage` GROUP BY `coverage_id` HAVING COUNT(*) > 1);

SELECT 'enrollment.coverage:unique_1' AS check_id, COUNT(*) AS violating_groups FROM (SELECT `identity_id`, `health_plan_id`, `coverage_from` FROM `__CATALOG__`.`enrollment`.`coverage` GROUP BY `identity_id`, `health_plan_id`, `coverage_from` HAVING COUNT(*) > 1);

SELECT 'provider.provider.provider_kind:enum' AS check_id, COUNT(*) AS violations FROM `__CATALOG__`.`provider`.`provider` WHERE `provider_kind` IS NOT NULL AND `provider_kind` NOT IN ('person', 'organization');

SELECT 'provider.provider.provider_status:enum' AS check_id, COUNT(*) AS violations FROM `__CATALOG__`.`provider`.`provider` WHERE `provider_status` IS NOT NULL AND `provider_status` NOT IN ('active', 'inactive');

SELECT 'provider.provider:pk_null' AS check_id, COUNT(*) AS violations FROM `__CATALOG__`.`provider`.`provider` WHERE `provider_id` IS NULL;

SELECT 'provider.provider:unique_0' AS check_id, COUNT(*) AS violating_groups FROM (SELECT `provider_id` FROM `__CATALOG__`.`provider`.`provider` GROUP BY `provider_id` HAVING COUNT(*) > 1);

SELECT 'provider.provider:unique_1' AS check_id, COUNT(*) AS violating_groups FROM (SELECT `provider_number` FROM `__CATALOG__`.`provider`.`provider` GROUP BY `provider_number` HAVING COUNT(*) > 1);

SELECT 'network.provider_network.network_status:enum' AS check_id, COUNT(*) AS violations FROM `__CATALOG__`.`network`.`provider_network` WHERE `network_status` IS NOT NULL AND `network_status` NOT IN ('active', 'inactive');

SELECT 'network.provider_network:pk_null' AS check_id, COUNT(*) AS violations FROM `__CATALOG__`.`network`.`provider_network` WHERE `provider_network_id` IS NULL;

SELECT 'network.provider_network:unique_0' AS check_id, COUNT(*) AS violating_groups FROM (SELECT `provider_network_id` FROM `__CATALOG__`.`network`.`provider_network` GROUP BY `provider_network_id` HAVING COUNT(*) > 1);

SELECT 'network.provider_network:unique_1' AS check_id, COUNT(*) AS violating_groups FROM (SELECT `network_code` FROM `__CATALOG__`.`network`.`provider_network` GROUP BY `network_code` HAVING COUNT(*) > 1);

SELECT 'network.participation.participation_status:enum' AS check_id, COUNT(*) AS violations FROM `__CATALOG__`.`network`.`participation` WHERE `participation_status` IS NOT NULL AND `participation_status` NOT IN ('active', 'ended', 'pending');

SELECT 'network.participation:pk_null' AS check_id, COUNT(*) AS violations FROM `__CATALOG__`.`network`.`participation` WHERE `participation_id` IS NULL;

SELECT 'network.participation:unique_0' AS check_id, COUNT(*) AS violating_groups FROM (SELECT `participation_id` FROM `__CATALOG__`.`network`.`participation` GROUP BY `participation_id` HAVING COUNT(*) > 1);

SELECT 'network.participation:unique_1' AS check_id, COUNT(*) AS violating_groups FROM (SELECT `provider_id`, `provider_network_id`, `participation_from` FROM `__CATALOG__`.`network`.`participation` GROUP BY `provider_id`, `provider_network_id`, `participation_from` HAVING COUNT(*) > 1);

SELECT 'claim.claim_status:pk_null' AS check_id, COUNT(*) AS violations FROM `__CATALOG__`.`claim`.`claim_status` WHERE `claim_status_id` IS NULL;

SELECT 'claim.claim_status:unique_0' AS check_id, COUNT(*) AS violating_groups FROM (SELECT `claim_status_id` FROM `__CATALOG__`.`claim`.`claim_status` GROUP BY `claim_status_id` HAVING COUNT(*) > 1);

SELECT 'claim.claim_status:unique_1' AS check_id, COUNT(*) AS violating_groups FROM (SELECT `status_code` FROM `__CATALOG__`.`claim`.`claim_status` GROUP BY `status_code` HAVING COUNT(*) > 1);

SELECT 'claim.header.currency_code:pattern' AS check_id, COUNT(*) AS violations FROM `__CATALOG__`.`claim`.`header` WHERE `currency_code` IS NOT NULL AND NOT (`currency_code` RLIKE '^[A-Z]{3}$');

SELECT 'claim.header:pk_null' AS check_id, COUNT(*) AS violations FROM `__CATALOG__`.`claim`.`header` WHERE `header_id` IS NULL;

SELECT 'claim.header:unique_0' AS check_id, COUNT(*) AS violating_groups FROM (SELECT `header_id` FROM `__CATALOG__`.`claim`.`header` GROUP BY `header_id` HAVING COUNT(*) > 1);

SELECT 'claim.header:unique_1' AS check_id, COUNT(*) AS violating_groups FROM (SELECT `claim_number`, `submission_version` FROM `__CATALOG__`.`claim`.`header` GROUP BY `claim_number`, `submission_version` HAVING COUNT(*) > 1);

SELECT 'claim.line:pk_null' AS check_id, COUNT(*) AS violations FROM `__CATALOG__`.`claim`.`line` WHERE `line_id` IS NULL;

SELECT 'claim.line:unique_0' AS check_id, COUNT(*) AS violating_groups FROM (SELECT `line_id` FROM `__CATALOG__`.`claim`.`line` GROUP BY `line_id` HAVING COUNT(*) > 1);

SELECT 'claim.line:unique_1' AS check_id, COUNT(*) AS violating_groups FROM (SELECT `header_id`, `line_number` FROM `__CATALOG__`.`claim`.`line` GROUP BY `header_id`, `line_number` HAVING COUNT(*) > 1);

SELECT 'claim.adjudication.decision_outcome:enum' AS check_id, COUNT(*) AS violations FROM `__CATALOG__`.`claim`.`adjudication` WHERE `decision_outcome` IS NOT NULL AND `decision_outcome` NOT IN ('approved', 'denied', 'pended');

SELECT 'claim.adjudication:pk_null' AS check_id, COUNT(*) AS violations FROM `__CATALOG__`.`claim`.`adjudication` WHERE `adjudication_id` IS NULL;

SELECT 'claim.adjudication:unique_0' AS check_id, COUNT(*) AS violating_groups FROM (SELECT `adjudication_id` FROM `__CATALOG__`.`claim`.`adjudication` GROUP BY `adjudication_id` HAVING COUNT(*) > 1);

SELECT 'rel_enrollment_coverage_identity_id:orphan' AS check_id, COUNT(*) AS violations FROM `__CATALOG__`.`enrollment`.`coverage` s WHERE s.`identity_id` IS NOT NULL AND NOT EXISTS (SELECT 1 FROM `__CATALOG__`.`member`.`identity` t WHERE s.`identity_id` = t.`identity_id`);

SELECT 'rel_enrollment_coverage_health_plan_id:orphan' AS check_id, COUNT(*) AS violations FROM `__CATALOG__`.`enrollment`.`coverage` s WHERE s.`health_plan_id` IS NOT NULL AND NOT EXISTS (SELECT 1 FROM `__CATALOG__`.`plan`.`health_plan` t WHERE s.`health_plan_id` = t.`health_plan_id`);

SELECT 'rel_network_participation_provider_id:orphan' AS check_id, COUNT(*) AS violations FROM `__CATALOG__`.`network`.`participation` s WHERE s.`provider_id` IS NOT NULL AND NOT EXISTS (SELECT 1 FROM `__CATALOG__`.`provider`.`provider` t WHERE s.`provider_id` = t.`provider_id`);

SELECT 'rel_network_participation_provider_network_id:orphan' AS check_id, COUNT(*) AS violations FROM `__CATALOG__`.`network`.`participation` s WHERE s.`provider_network_id` IS NOT NULL AND NOT EXISTS (SELECT 1 FROM `__CATALOG__`.`network`.`provider_network` t WHERE s.`provider_network_id` = t.`provider_network_id`);

SELECT 'rel_claim_header_coverage_id:orphan' AS check_id, COUNT(*) AS violations FROM `__CATALOG__`.`claim`.`header` s WHERE s.`coverage_id` IS NOT NULL AND NOT EXISTS (SELECT 1 FROM `__CATALOG__`.`enrollment`.`coverage` t WHERE s.`coverage_id` = t.`coverage_id`);

SELECT 'rel_claim_header_billing_provider_id:orphan' AS check_id, COUNT(*) AS violations FROM `__CATALOG__`.`claim`.`header` s WHERE s.`billing_provider_id` IS NOT NULL AND NOT EXISTS (SELECT 1 FROM `__CATALOG__`.`provider`.`provider` t WHERE s.`billing_provider_id` = t.`provider_id`);

SELECT 'rel_claim_header_rendering_provider_id:orphan' AS check_id, COUNT(*) AS violations FROM `__CATALOG__`.`claim`.`header` s WHERE s.`rendering_provider_id` IS NOT NULL AND NOT EXISTS (SELECT 1 FROM `__CATALOG__`.`provider`.`provider` t WHERE s.`rendering_provider_id` = t.`provider_id`);

SELECT 'rel_claim_header_claim_status_id:orphan' AS check_id, COUNT(*) AS violations FROM `__CATALOG__`.`claim`.`header` s WHERE s.`claim_status_id` IS NOT NULL AND NOT EXISTS (SELECT 1 FROM `__CATALOG__`.`claim`.`claim_status` t WHERE s.`claim_status_id` = t.`claim_status_id`);

SELECT 'rel_claim_line_header_id:orphan' AS check_id, COUNT(*) AS violations FROM `__CATALOG__`.`claim`.`line` s WHERE s.`header_id` IS NOT NULL AND NOT EXISTS (SELECT 1 FROM `__CATALOG__`.`claim`.`header` t WHERE s.`header_id` = t.`header_id`);

SELECT 'rel_claim_adjudication_header_id:orphan' AS check_id, COUNT(*) AS violations FROM `__CATALOG__`.`claim`.`adjudication` s WHERE s.`header_id` IS NOT NULL AND NOT EXISTS (SELECT 1 FROM `__CATALOG__`.`claim`.`header` t WHERE s.`header_id` = t.`header_id`);

SELECT 'plan.health_plan:interval' AS check_id, COUNT(*) AS violations FROM `__CATALOG__`.`plan`.`health_plan` WHERE `effective_to` <= `effective_from`;

SELECT 'enrollment.coverage:interval' AS check_id, COUNT(*) AS violations FROM `__CATALOG__`.`enrollment`.`coverage` WHERE `coverage_to` <= `coverage_from`;

SELECT 'network.participation:interval' AS check_id, COUNT(*) AS violations FROM `__CATALOG__`.`network`.`participation` WHERE `participation_to` <= `participation_from`;

SELECT 'coverage_overlap' AS check_id, COUNT(*) AS violations FROM `__CATALOG__`.`enrollment`.`coverage` a JOIN `__CATALOG__`.`enrollment`.`coverage` b ON a.identity_id = b.identity_id AND a.health_plan_id = b.health_plan_id AND a.coverage_id < b.coverage_id AND (b.coverage_to IS NULL OR a.coverage_from < b.coverage_to) AND (a.coverage_to IS NULL OR b.coverage_from < a.coverage_to);
