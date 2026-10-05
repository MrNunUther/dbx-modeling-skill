-- Remodel of claim_flat.sql toward the common shapes in references/shape-topology.md.
-- Teaching artifact: illustrative columns only, not a complete claim model. Do not deploy.
-- Masters (member, provider, health_plan) are referenced, not embedded; repeating groups become children.

CREATE TABLE IF NOT EXISTS member.member (
  member_id BIGINT NOT NULL COMMENT 'Surrogate key for one enrolled person.',
  member_number STRING COMMENT 'Payer-assigned member identifier.',
  full_name STRING,
  birth_date DATE,
  gender_code STRING,
  primary_phone_number STRING,
  member_status STRING,
  effective_date DATE,
  termination_date DATE,
  created_timestamp TIMESTAMP,
  updated_timestamp TIMESTAMP,
  CONSTRAINT pk_member PRIMARY KEY (member_id)
) COMMENT 'One row per enrolled person.';

CREATE TABLE IF NOT EXISTS provider.provider (
  provider_id BIGINT NOT NULL,
  npi_number STRING,
  provider_name STRING,
  provider_type STRING,
  practice_city STRING,
  primary_phone_number STRING,
  provider_status STRING,
  created_timestamp TIMESTAMP,
  updated_timestamp TIMESTAMP,
  CONSTRAINT pk_provider PRIMARY KEY (provider_id)
) COMMENT 'One row per rendering or billing provider.';

CREATE TABLE IF NOT EXISTS plan.health_plan (
  health_plan_id BIGINT NOT NULL,
  plan_code STRING,
  plan_name STRING,
  effective_date DATE,
  termination_date DATE,
  created_timestamp TIMESTAMP,
  updated_timestamp TIMESTAMP,
  CONSTRAINT pk_health_plan PRIMARY KEY (health_plan_id)
) COMMENT 'One row per benefit plan.';

CREATE TABLE IF NOT EXISTS claim.claim (
  claim_id BIGINT NOT NULL COMMENT 'Surrogate key for one submitted claim.',
  member_id BIGINT NOT NULL,
  rendering_provider_id BIGINT,
  health_plan_id BIGINT NOT NULL,
  claim_number STRING COMMENT 'Business key assigned at intake.',
  claim_type STRING,
  claim_status STRING,
  service_date DATE,
  received_date DATE,
  adjudicated_timestamp TIMESTAMP,
  total_billed_amount DECIMAL(18,2),
  total_paid_amount DECIMAL(18,2),
  is_emergency BOOLEAN,
  created_timestamp TIMESTAMP,
  updated_timestamp TIMESTAMP,
  CONSTRAINT pk_claim PRIMARY KEY (claim_id),
  CONSTRAINT fk_claim_member FOREIGN KEY (member_id) REFERENCES member.member (member_id),
  CONSTRAINT fk_claim_provider FOREIGN KEY (rendering_provider_id) REFERENCES provider.provider (provider_id),
  CONSTRAINT fk_claim_plan FOREIGN KEY (health_plan_id) REFERENCES plan.health_plan (health_plan_id)
) COMMENT 'One row per submitted claim.';

CREATE TABLE IF NOT EXISTS claim.claim_line (
  claim_line_id BIGINT NOT NULL,
  claim_id BIGINT NOT NULL,
  line_number INT,
  procedure_code STRING,
  line_status STRING,
  service_date DATE,
  billed_amount DECIMAL(18,2),
  paid_amount DECIMAL(18,2),
  created_timestamp TIMESTAMP,
  updated_timestamp TIMESTAMP,
  CONSTRAINT pk_claim_line PRIMARY KEY (claim_line_id),
  CONSTRAINT fk_claim_line_claim FOREIGN KEY (claim_id) REFERENCES claim.claim (claim_id)
) COMMENT 'One row per service line on a claim.';

CREATE TABLE IF NOT EXISTS claim.claim_diagnosis (
  claim_diagnosis_id BIGINT NOT NULL,
  claim_id BIGINT NOT NULL,
  diagnosis_sequence INT,
  diagnosis_code STRING,
  is_principal BOOLEAN,
  created_timestamp TIMESTAMP,
  updated_timestamp TIMESTAMP,
  CONSTRAINT pk_claim_diagnosis PRIMARY KEY (claim_diagnosis_id),
  CONSTRAINT fk_claim_diagnosis_claim FOREIGN KEY (claim_id) REFERENCES claim.claim (claim_id)
) COMMENT 'One row per diagnosis reported on a claim, in submitted order.';
