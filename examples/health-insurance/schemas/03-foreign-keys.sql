-- Re-authored teaching artifact; see adaptation-log.csv and NOTICE.
-- NOT EXECUTED. Substitute reviewed __CATALOG__ offline before authorized use.


-- ADD CONSTRAINT is not rerun-idempotent; inspect existing declarations.

ALTER TABLE `__CATALOG__`.`enrollment`.`coverage` ADD CONSTRAINT `rel_enrollment_coverage_identity_id` FOREIGN KEY (`identity_id`) REFERENCES `__CATALOG__`.`member`.`identity` (`identity_id`);

ALTER TABLE `__CATALOG__`.`enrollment`.`coverage` ADD CONSTRAINT `rel_enrollment_coverage_health_plan_id` FOREIGN KEY (`health_plan_id`) REFERENCES `__CATALOG__`.`plan`.`health_plan` (`health_plan_id`);

ALTER TABLE `__CATALOG__`.`network`.`participation` ADD CONSTRAINT `rel_network_participation_provider_id` FOREIGN KEY (`provider_id`) REFERENCES `__CATALOG__`.`provider`.`provider` (`provider_id`);

ALTER TABLE `__CATALOG__`.`network`.`participation` ADD CONSTRAINT `rel_network_participation_provider_network_id` FOREIGN KEY (`provider_network_id`) REFERENCES `__CATALOG__`.`network`.`provider_network` (`provider_network_id`);

ALTER TABLE `__CATALOG__`.`claim`.`header` ADD CONSTRAINT `rel_claim_header_coverage_id` FOREIGN KEY (`coverage_id`) REFERENCES `__CATALOG__`.`enrollment`.`coverage` (`coverage_id`);

ALTER TABLE `__CATALOG__`.`claim`.`header` ADD CONSTRAINT `rel_claim_header_billing_provider_id` FOREIGN KEY (`billing_provider_id`) REFERENCES `__CATALOG__`.`provider`.`provider` (`provider_id`);

ALTER TABLE `__CATALOG__`.`claim`.`header` ADD CONSTRAINT `rel_claim_header_rendering_provider_id` FOREIGN KEY (`rendering_provider_id`) REFERENCES `__CATALOG__`.`provider`.`provider` (`provider_id`);

ALTER TABLE `__CATALOG__`.`claim`.`header` ADD CONSTRAINT `rel_claim_header_claim_status_id` FOREIGN KEY (`claim_status_id`) REFERENCES `__CATALOG__`.`claim`.`claim_status` (`claim_status_id`);

ALTER TABLE `__CATALOG__`.`claim`.`line` ADD CONSTRAINT `rel_claim_line_header_id` FOREIGN KEY (`header_id`) REFERENCES `__CATALOG__`.`claim`.`header` (`header_id`);

ALTER TABLE `__CATALOG__`.`claim`.`adjudication` ADD CONSTRAINT `rel_claim_adjudication_header_id` FOREIGN KEY (`header_id`) REFERENCES `__CATALOG__`.`claim`.`header` (`header_id`);
