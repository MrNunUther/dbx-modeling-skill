-- Re-authored teaching artifact; see adaptation-log.csv and NOTICE.
-- NOT EXECUTED. Substitute reviewed __CATALOG__ offline before authorized use.


CREATE TABLE IF NOT EXISTS `__CATALOG__`.`member`.`identity` (
  `identity_id` BIGINT NOT NULL COMMENT 'Stable surrogate identifier for this record.',
  `source_member_number` STRING NOT NULL COMMENT 'Source-system member identity for reconciliation.',
  `given_name` STRING NOT NULL COMMENT 'Person''s given name as recorded by the enrollment source.',
  `family_name` STRING NOT NULL COMMENT 'Person''s family name as recorded by the enrollment source.',
  `date_of_birth` DATE NOT NULL COMMENT 'Person''s date of birth used in eligibility processing.',
  `identity_status` STRING NOT NULL COMMENT 'Current lifecycle state of the insured identity.',
  `created_at` TIMESTAMP NOT NULL COMMENT 'Timestamp when the identity entered this system.',
  CONSTRAINT `pk_identity` PRIMARY KEY (`identity_id`)
) USING DELTA COMMENT 'Authoritative identity for the insured person in this teaching scope.';

CREATE TABLE IF NOT EXISTS `__CATALOG__`.`plan`.`health_plan` (
  `health_plan_id` BIGINT NOT NULL COMMENT 'Stable surrogate identifier for this record.',
  `plan_code` STRING NOT NULL COMMENT 'Source plan code, unique together with the design version.',
  `design_version` INT NOT NULL COMMENT 'Version of the plan benefit design.',
  `plan_name` STRING NOT NULL COMMENT 'Business label of the offered health plan.',
  `effective_from` DATE NOT NULL COMMENT 'First date on which this design is effective.',
  `effective_to` DATE COMMENT 'Exclusive end date of this design, if retired.',
  `currency_code` STRING NOT NULL COMMENT 'ISO 4217 currency for plan monetary terms.',
  `deductible_amount` DECIMAL(18,2) NOT NULL COMMENT 'Individual deductible under this design.',
  CONSTRAINT `pk_health_plan` PRIMARY KEY (`health_plan_id`)
) USING DELTA COMMENT 'Versioned plan design used to define coverage commitments.';

CREATE TABLE IF NOT EXISTS `__CATALOG__`.`enrollment`.`coverage` (
  `coverage_id` BIGINT NOT NULL COMMENT 'Stable surrogate identifier for this record.',
  `identity_id` BIGINT NOT NULL COMMENT 'Covered person owned by the member domain.',
  `health_plan_id` BIGINT NOT NULL COMMENT 'Plan design governing this coverage episode.',
  `coverage_from` DATE NOT NULL COMMENT 'Inclusive start date of coverage.',
  `coverage_to` DATE COMMENT 'Exclusive end date of coverage, if terminated.',
  `coverage_status` STRING NOT NULL COMMENT 'Current state of the coverage episode.',
  `elected_at` TIMESTAMP NOT NULL COMMENT 'Timestamp when the coverage election was accepted.',
  CONSTRAINT `pk_coverage` PRIMARY KEY (`coverage_id`)
) USING DELTA COMMENT 'Coverage episode binding a person to a versioned plan design.';

CREATE TABLE IF NOT EXISTS `__CATALOG__`.`provider`.`provider` (
  `provider_id` BIGINT NOT NULL COMMENT 'Stable surrogate identifier for this record.',
  `provider_number` STRING NOT NULL COMMENT 'Source provider identity used for reconciliation.',
  `provider_name` STRING NOT NULL COMMENT 'Provider''s business display label.',
  `provider_kind` STRING NOT NULL COMMENT 'Provider identity category.',
  `provider_status` STRING NOT NULL COMMENT 'Operational provider lifecycle state.',
  `created_at` TIMESTAMP NOT NULL COMMENT 'Timestamp when the provider record was created.',
  CONSTRAINT `pk_provider` PRIMARY KEY (`provider_id`)
) USING DELTA COMMENT 'Authoritative provider identity used in service and network records.';

CREATE TABLE IF NOT EXISTS `__CATALOG__`.`network`.`provider_network` (
  `provider_network_id` BIGINT NOT NULL COMMENT 'Stable surrogate identifier for this record.',
  `network_code` STRING NOT NULL COMMENT 'Business identifier of the provider network.',
  `network_name` STRING NOT NULL COMMENT 'Business display label of the network.',
  `network_status` STRING NOT NULL COMMENT 'Operational lifecycle state of the network.',
  CONSTRAINT `pk_provider_network` PRIMARY KEY (`provider_network_id`)
) USING DELTA COMMENT 'Named service network used to organize provider participation.';

CREATE TABLE IF NOT EXISTS `__CATALOG__`.`network`.`participation` (
  `participation_id` BIGINT NOT NULL COMMENT 'Stable surrogate identifier for this record.',
  `provider_id` BIGINT NOT NULL COMMENT 'Provider participating in the network.',
  `provider_network_id` BIGINT NOT NULL COMMENT 'Network accepting this provider.',
  `participation_from` DATE NOT NULL COMMENT 'Inclusive first date of this participation agreement.',
  `participation_to` DATE COMMENT 'Exclusive end date if participation ended.',
  `participation_status` STRING NOT NULL COMMENT 'Agreement lifecycle state.',
  `created_at` TIMESTAMP NOT NULL COMMENT 'Timestamp when participation was recorded.',
  CONSTRAINT `pk_participation` PRIMARY KEY (`participation_id`)
) USING DELTA COMMENT 'Effective participation agreement between a provider and network.';

CREATE TABLE IF NOT EXISTS `__CATALOG__`.`claim`.`claim_status` (
  `claim_status_id` BIGINT NOT NULL COMMENT 'Stable surrogate identifier for this record.',
  `status_code` STRING NOT NULL COMMENT 'Stable machine-readable processing state.',
  `status_label` STRING NOT NULL COMMENT 'Human-readable processing state label.',
  `is_terminal` BOOLEAN NOT NULL COMMENT 'Whether this state ends normal processing.',
  CONSTRAINT `pk_claim_status` PRIMARY KEY (`claim_status_id`)
) USING DELTA COMMENT 'Reference vocabulary for claim states, including more than six categories.';

CREATE TABLE IF NOT EXISTS `__CATALOG__`.`claim`.`header` (
  `header_id` BIGINT NOT NULL COMMENT 'Stable surrogate identifier for this record.',
  `coverage_id` BIGINT NOT NULL COMMENT 'Coverage episode for the insured person at service time.',
  `billing_provider_id` BIGINT NOT NULL COMMENT 'Provider submitting the bill.',
  `rendering_provider_id` BIGINT COMMENT 'Provider that performed the service.',
  `claim_status_id` BIGINT NOT NULL COMMENT 'Current processing state in the claim status vocabulary.',
  `claim_number` STRING NOT NULL COMMENT 'Source claim identifier used for reconciliation.',
  `submission_version` INT NOT NULL COMMENT 'Source version of this submitted claim.',
  `received_at` TIMESTAMP NOT NULL COMMENT 'Timestamp when this claim version was received.',
  `service_date` DATE NOT NULL COMMENT 'Business service date attributed to the claim.',
  `currency_code` STRING NOT NULL COMMENT 'ISO 4217 currency for all claim amounts.',
  `billed_amount` DECIMAL(18,2) NOT NULL COMMENT 'Event-time total billed on this submitted version.',
  `allowed_amount` DECIMAL(18,2) COMMENT 'Allowed total for this claim version.',
  `paid_amount` DECIMAL(18,2) COMMENT 'Paid total for this claim version.',
  CONSTRAINT `pk_header` PRIMARY KEY (`header_id`)
) USING DELTA COMMENT 'Claim submission identity and event-time financial totals.';

CREATE TABLE IF NOT EXISTS `__CATALOG__`.`claim`.`line` (
  `line_id` BIGINT NOT NULL COMMENT 'Stable surrogate identifier for this record.',
  `header_id` BIGINT NOT NULL COMMENT 'Owning claim submission header.',
  `line_number` INT NOT NULL COMMENT 'Service line sequence within the owning header.',
  `service_code` STRING NOT NULL COMMENT 'Source service identifier; no licensed code list is distributed.',
  `service_date` DATE NOT NULL COMMENT 'Date when the line''s service was performed.',
  `service_quantity` DECIMAL(12,3) NOT NULL COMMENT 'Quantity billed for the service line.',
  `unit_price_at_service` DECIMAL(18,2) NOT NULL COMMENT 'Price recorded at service time, not today''s price.',
  CONSTRAINT `pk_line` PRIMARY KEY (`line_id`)
) USING DELTA COMMENT 'Service detail retaining price at the time of service.';

CREATE TABLE IF NOT EXISTS `__CATALOG__`.`claim`.`adjudication` (
  `adjudication_id` BIGINT NOT NULL COMMENT 'Stable surrogate identifier for this record.',
  `header_id` BIGINT NOT NULL COMMENT 'Claim version receiving the adjudication event.',
  `decided_at` TIMESTAMP NOT NULL COMMENT 'Timestamp when the decision was recorded.',
  `decision_outcome` STRING NOT NULL COMMENT 'Decision result for this event.',
  `decision_reason` STRING NOT NULL COMMENT 'Business rationale for the decision event.',
  `allowed_amount_at_decision` DECIMAL(18,2) COMMENT 'Allowed amount at this decision event.',
  CONSTRAINT `pk_adjudication` PRIMARY KEY (`adjudication_id`)
) USING DELTA COMMENT 'Auditable decision event; several decisions can exist for a claim.';
