-- Re-authored teaching artifact; see adaptation-log.csv and NOTICE.
-- NOT EXECUTED. Substitute reviewed __CATALOG__ offline before authorized use.


CREATE CATALOG IF NOT EXISTS `__CATALOG__`;

CREATE SCHEMA IF NOT EXISTS `__CATALOG__`.`member` COMMENT 'Owns the member business records within the explicitly bounded teaching scope.';

CREATE SCHEMA IF NOT EXISTS `__CATALOG__`.`plan` COMMENT 'Owns the plan business records within the explicitly bounded teaching scope.';

CREATE SCHEMA IF NOT EXISTS `__CATALOG__`.`enrollment` COMMENT 'Owns the enrollment business records within the explicitly bounded teaching scope.';

CREATE SCHEMA IF NOT EXISTS `__CATALOG__`.`provider` COMMENT 'Owns the provider business records within the explicitly bounded teaching scope.';

CREATE SCHEMA IF NOT EXISTS `__CATALOG__`.`network` COMMENT 'Owns the network business records within the explicitly bounded teaching scope.';

CREATE SCHEMA IF NOT EXISTS `__CATALOG__`.`claim` COMMENT 'Owns the claim business records within the explicitly bounded teaching scope.';

CREATE SCHEMA IF NOT EXISTS `__CATALOG__`.`metrics`;
