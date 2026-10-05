"""Behavioral tests; mutated copies never alter the shipped canonical example."""
import copy
import csv
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import render_example
import validate_skill as validator


class ModelTests(unittest.TestCase):
    def setUp(self):
        self.model = validator.read_json(ROOT / "examples/health-insurance/model.json")

    def product(self, path):
        return render_example.products(self.model)[path]

    def attribute(self, path, name):
        return next(a for a in self.product(path)["attributes"] if a["name"] == name)

    def fail_ids(self):
        return {f["check_id"] for f in validator.validate_model(self.model, ROOT) if f["status"] == "fail"}

    def test_passing_suite_and_shape(self):
        self.assertEqual(self.fail_ids(), set())

    def test_unknown_field_rejected(self):
        self.model["deploy_now"] = True
        self.assertIn("SHAPE", self.fail_ids())

    def test_wrong_boolean_type_rejected(self):
        self.attribute("claim.header", "header_id")["nullable"] = "false"
        self.assertIn("SHAPE", self.fail_ids())

    def test_malformed_root_reports_not_crashes(self):
        findings = validator.validate_model([], ROOT)
        report = validator.report_for([], findings)
        self.assertEqual(report["status"], "fail")
        self.assertEqual(report["coverage"]["verified_static"], 0)

    def test_shape_failure_keeps_requirement_denominator(self):
        self.attribute("claim.line", "line_id")["nullable"] = "false"
        report = validator.report_for(self.model, validator.validate_model(self.model, ROOT))
        self.assertEqual(report["status"], "fail")
        self.assertEqual(report["coverage"]["applicable"], 6)
        self.assertEqual(report["coverage"]["verified_static"], 0)
        self.assertTrue(any(c["status"] == "blocked" for c in report["checks"]))

    def test_missing_pk(self):
        self.product("claim.line")["primary_key"] = ["absent_id"]
        self.assertIn("PK", self.fail_ids())

    def test_empty_pk(self):
        self.product("claim.line")["primary_key"] = []
        self.assertIn("SHAPE", self.fail_ids())

    def test_nullable_pk(self):
        self.attribute("claim.line", "line_id")["nullable"] = True
        self.assertIn("PK", self.fail_ids())

    def test_missing_target_product(self):
        self.model["relationships"][0]["target"] = "member.absent"
        self.assertIn("FK_TARGET", self.fail_ids())

    def test_missing_target_column(self):
        self.model["relationships"][0]["target_columns"] = ["absent_id"]
        self.assertIn("FK_TARGET", self.fail_ids())

    def test_non_pk_target(self):
        self.model["relationships"][0]["target_columns"] = ["identity_status"]
        self.assertIn("FK_TARGET", self.fail_ids())

    def test_missing_source_column(self):
        self.model["relationships"][0]["source_columns"] = ["absent_id"]
        self.assertIn("FK_TARGET", self.fail_ids())

    def test_tuple_arity_mismatch(self):
        self.model["relationships"][0]["source_columns"] = ["identity_id", "health_plan_id"]
        self.assertIn("FK_TYPES", self.fail_ids())

    def test_type_mismatch(self):
        self.attribute("enrollment.coverage", "identity_id")["type"] = "INT"
        self.assertIn("FK_TYPES", self.fail_ids())

    def test_decimal_bounds(self):
        for typ in ["DECIMAL(39,2)", "DECIMAL(12,13)", "DECIMAL(0,0)", "MAP<STRING,STRING>"]:
            with self.subTest(typ=typ):
                self.attribute("claim.header", "paid_amount")["type"] = typ
                self.assertIn("TYPES", self.fail_ids())

    def test_monetary_field_cannot_silently_become_float(self):
        self.attribute("claim.header", "paid_amount")["type"] = "DOUBLE"
        self.assertIn("TYPES", self.fail_ids())

    def test_distinct_role_labels_pass(self):
        self.assertEqual(self.fail_ids(), set())
        relation = next(r for r in self.model["relationships"] if r["role"] == "rendering")
        relation["role"] = "billing"
        self.assertIn("ROLES", self.fail_ids())

    def test_duplicate_fk_tuple_is_not_a_new_business_role(self):
        relation = copy.deepcopy(self.model["relationships"][0])
        relation.update(id="duplicate_fk", role="pretend_second_role")
        self.model["relationships"].append(relation)
        self.assertIn("ROLES", self.fail_ids())

    def test_one_to_one_requires_declared_source_uniqueness(self):
        relation = self.model["relationships"][0]
        relation["cardinality"] = "one_to_one"
        self.assertIn("RELATIONS", self.fail_ids())
        self.product("enrollment.coverage")["business_keys"].append(["identity_id"])
        self.assertNotIn("RELATIONS", self.fail_ids())

    def add_reverse(self):
        attribute = copy.deepcopy(self.attribute("claim.header", "billing_provider_id"))
        attribute.update(name="latest_header_id", physical_name="latest_header_id")
        self.product("provider.provider")["attributes"].append(attribute)
        relation = copy.deepcopy(self.model["relationships"][0])
        relation.update(id="reverse", source="provider.provider", source_columns=["latest_header_id"],
                        target="claim.header", target_columns=["header_id"], role="latest_claim")
        self.model["relationships"].append(relation)

    def test_cycle_and_explicit_alternate_policy(self):
        self.add_reverse()
        self.assertIn("GRAPH", self.fail_ids())
        self.model["conventions"]["graph_policy"] = "allow_cycles"
        self.assertNotIn("GRAPH", self.fail_ids())

    def add_hierarchy(self):
        attribute = copy.deepcopy(self.attribute("claim.header", "rendering_provider_id"))
        attribute.update(name="parent_provider_id", physical_name="parent_provider_id")
        self.product("provider.provider")["attributes"].append(attribute)
        relation = copy.deepcopy(next(r for r in self.model["relationships"] if r["role"] == "rendering"))
        relation.update(id="hierarchy", source="provider.provider", source_columns=["parent_provider_id"],
                        target="provider.provider", target_columns=["provider_id"], role="parent", hierarchical=True)
        self.model["relationships"].append(relation)

    def test_hierarchy_passes_only_with_explicit_exception(self):
        self.add_hierarchy()
        self.assertEqual(self.fail_ids(), set())
        self.model["relationships"][-1]["hierarchical"] = False
        self.assertIn("GRAPH", self.fail_ids())

    def test_self_pk_always_fails(self):
        self.add_hierarchy()
        self.model["relationships"][-1].update(source_columns=["provider_id"], optional=False)
        self.assertIn("ROLES", self.fail_ids())
        self.model["conventions"]["graph_policy"] = "allow_cycles"
        self.assertIn("ROLES", self.fail_ids())

    def test_later_fk_needs_enrichment_and_optionality(self):
        relation = next(r for r in self.model["relationships"] if r["role"] == "rendering")
        relation["enrichment_path"] = ""
        self.assertIn("RELATIONS", self.fail_ids())
        relation["enrichment_path"] = "Enrich before processing completion."
        relation["optional"] = False
        self.assertIn("RELATIONS", self.fail_ids())

    def test_six_values_pass_seven_fail(self):
        attribute = self.attribute("member.identity", "identity_status")
        attribute["allowed_values"] = ["a", "b", "c", "d", "e", "f"]
        self.assertNotIn("ENUMS", self.fail_ids())
        attribute["allowed_values"].append("g")
        self.assertIn("ENUMS", self.fail_ids())
        self.assertEqual(self.product("claim.claim_status")["classification"], "reference_data")

    def test_pattern_only_on_string_and_separate_from_enum(self):
        attribute = self.attribute("member.identity", "date_of_birth")
        attribute["pattern"] = "^2026"
        self.assertIn("ENUMS", self.fail_ids())
        attribute["pattern"] = ""
        attribute = self.attribute("member.identity", "identity_status")
        attribute["pattern"] = "^a"
        self.assertIn("ENUMS", self.fail_ids())

    def test_invalid_regex_reported(self):
        self.attribute("plan.health_plan", "currency_code")["pattern"] = "["
        self.assertIn("ENUMS", self.fail_ids())

    def test_missing_glossary(self):
        self.attribute("member.identity", "given_name")["glossary"] = ""
        self.assertIn("SHAPE", self.fail_ids())

    def test_missing_sensitivity_marker(self):
        self.attribute("member.identity", "given_name")["tags"] = {}
        self.assertIn("SENSITIVITY", self.fail_ids())

    def test_structural_and_generated_tags_rejected(self):
        self.attribute("claim.line", "line_id")["tags"]["primary_key"] = "true"
        self.assertIn("TAGS", self.fail_ids())
        del self.attribute("claim.line", "line_id")["tags"]["primary_key"]
        self.attribute("claim.line", "line_id")["tags"]["dbx_classification"] = "public"
        self.assertIn("TAGS", self.fail_ids())

    def test_sensitivity_marker_cannot_hide_behind_none(self):
        attribute = self.attribute("plan.health_plan", "plan_name")
        attribute["tags"]["sensitivity"] = "health"
        self.assertIn("SENSITIVITY", self.fail_ids())

    def test_mapping_drift_and_collision(self):
        self.attribute("claim.line", "line_number")["physical_name"] = "header_id"
        self.assertIn("NAMES", self.fail_ids())
        self.attribute("claim.line", "line_number")["physical_name"] = "Header_Id"
        self.assertIn("SHAPE", self.fail_ids())

    def test_protected_names_and_counts(self):
        self.model["protected"]["domains"].append("finance")
        self.assertIn("PROTECTED", self.fail_ids())
        self.model["protected"]["domains"].remove("finance")
        self.model["protected"]["exact_product_count"] = 9
        self.assertIn("PROTECTED", self.fail_ids())

    def test_tiny_scope_not_expanded_by_ratios(self):
        domain = copy.deepcopy(next(d for d in self.model["domains"] if d["name"] == "claim"))
        domain["products"] = [copy.deepcopy(self.product("claim.claim_status"))]
        domain["products"][0]["standalone_reason"] = "Standalone reference vocabulary requested by the user."
        domain["division"] = "corporate"
        self.model.update(domains=[domain], relationships=[], metric_views=[],
                          protected={"domains": ["claim"], "products": ["claim.claim_status"],
                                     "exact_domain_count": 1, "exact_product_count": 1})
        self.model["requirements"] = [dict(id="tiny", description="One reference vocabulary only.",
                                           objects=["claim.claim_status"], checks=["PROTECTED"], manual=False)]
        before = copy.deepcopy(self.model)
        self.assertEqual(self.fail_ids(), set())
        self.assertEqual(self.model, before)

    def test_snapshot_preserved_no_semantic_autofix(self):
        attribute = self.attribute("claim.line", "unit_price_at_service")
        self.assertTrue(attribute["snapshot"])
        before = copy.deepcopy(self.model)
        output = render_example.render(self.model)
        self.assertIn("unit_price_at_service", output["schemas/02-tables.sql"])
        self.assertEqual(self.model, before)
        self.assertNotIn("manual", validator.CHECK_RULES)

    def test_metric_missing_source_column(self):
        self.model["metric_views"][0]["measures"][1].update(expression="SUM(nonexistent)", columns=["nonexistent"])
        self.assertIn("METRICS", self.fail_ids())

    def test_metric_dependency_lie_and_unsupported_expression(self):
        self.model["metric_views"][0]["measures"][1]["columns"] = []
        self.assertIn("METRICS", self.fail_ids())
        self.model["metric_views"][0]["measures"][1].update(expression="SUM(billed_amount); DROP TABLE x", columns=["billed_amount"])
        self.assertIn("METRICS", self.fail_ids())

    def test_composite_keys_and_rendering(self):
        status = self.product("claim.claim_status")
        status["primary_key"] = ["claim_status_id", "status_code"]
        attribute = copy.deepcopy(next(a for a in status["attributes"] if a["name"] == "status_code"))
        self.product("claim.header")["attributes"].append(attribute)
        relation = next(r for r in self.model["relationships"] if r["target"] == "claim.claim_status")
        relation.update(source_columns=["claim_status_id", "status_code"],
                        target_columns=["claim_status_id", "status_code"])
        self.assertEqual(self.fail_ids(), set())
        output = render_example.render(self.model)
        self.assertIn("PRIMARY KEY (`claim_status_id`, `status_code`)", output["schemas/02-tables.sql"])
        self.assertIn("(claim_status_id, status_code) [pk]", output["diagram/model.dbml"])
        self.attribute("claim.header", "status_code")["nullable"] = True
        self.assertIn("RELATIONS", self.fail_ids())

    def test_requirement_targets_and_check_ids(self):
        self.model["requirements"][0]["objects"] = ["not.real"]
        self.assertIn("REQUIREMENTS", self.fail_ids())
        self.model["requirements"][0]["checks"] = ["NOT_IMPLEMENTED"]
        self.assertIn("REQUIREMENTS", self.fail_ids())

    def test_report_does_not_claim_manual_or_live_pass(self):
        report = validator.report_for(self.model, validator.validate_model(self.model, ROOT))
        self.assertEqual(report["coverage"]["manual_unverified"], 1)
        self.assertTrue(all(c["status"] == "not_run" for c in report["checks"] if c["check_id"] in {"WORKSPACE", "PHYSICAL", "DATA"}))
        next(c for c in report["checks"] if c["check_id"] == "PHYSICAL")["status"] = "pass"
        self.assertTrue(any(c["status"] == "fail" for c in validator.validate_report(report, ROOT)))
        report["evidence_level"] = "physical"
        self.assertTrue(any(c["status"] == "fail" for c in validator.validate_report(report, ROOT)))

    def test_hard_failure_never_hidden_by_coverage(self):
        self.attribute("claim.line", "header_id")["type"] = "STRING"
        report = validator.report_for(self.model, validator.validate_model(self.model, ROOT))
        self.assertEqual(report["status"], "fail")
        self.assertLess(report["coverage"]["verified_static"], 5)


class PackageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name) / "package"
        shutil.copytree(ROOT, self.root, ignore=shutil.ignore_patterns(".venv", "__pycache__", "*.pyc"))
        self.addCleanup(self.temp.cleanup)

    def edit_csv(self, relative, change):
        path = self.root / relative
        fields, rows = validator.read_csv(path)
        change(rows)
        with path.open("w", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)

    def rule_failures(self):
        return {c["check_id"] for c in validator.validate_rules(self.root) if c["status"] == "fail"}

    def test_duplicate_source_ids_are_distinct_and_valid(self):
        self.assertEqual(self.rule_failures(), set())
        _, rows = validator.read_csv(self.root / "rules/source-rule-map.csv")
        self.assertEqual(len(rows), 264)
        self.assertEqual(len([r for r in rows if r["Source_ID"] == "QGATE-RUL-011"]), 2)

    def test_duplicate_canonical_id_fails(self):
        self.edit_csv("rules/modeling-rules.csv", lambda rows: rows.append(copy.deepcopy(rows[0])))
        self.assertIn("PACKAGE", self.rule_failures())

    def test_missing_disposition_and_source_occurrence_fail(self):
        self.edit_csv("rules/source-rule-map.csv", lambda rows: rows[0].update(Disposition=""))
        self.assertIn("SOURCE_MAP", self.rule_failures())
        self.edit_csv("rules/source-rule-map.csv", lambda rows: rows.pop())
        self.assertIn("SOURCE_MAP", self.rule_failures())

    def test_incomplete_requirement_not_falsely_adopted(self):
        self.edit_csv("rules/source-rule-map.csv", lambda rows: rows[0].update(Disposition="adopted"))
        self.assertIn("SOURCE_MAP", self.rule_failures())

    def test_missing_instruction_disposition_fails(self):
        self.edit_csv("rules/source-instruction-map.csv", lambda rows: rows[4].update(Disposition=""))
        self.assertIn("SOURCE_MAP", self.rule_failures())

    def test_output_drift_fails(self):
        path = self.root / "examples/health-insurance/schemas/02-tables.sql"
        path.write_text(path.read_text().replace("DECIMAL(18,2)", "DOUBLE", 1))
        model = validator.read_json(self.root / "examples/health-insurance/model.json")
        self.assertTrue(any(c["status"] == "fail" for c in validator.validate_artifacts(model, self.root)))

    def test_missing_link_and_asset_fail(self):
        path = self.root / "README.md"
        path.write_text(path.read_text() + "\n[missing](absent.md)\n")
        (self.root / "assets/modeling.png").unlink()
        self.assertTrue(any(c["status"] == "fail" for c in validator.validate_package(self.root)))

    def test_traceability_mismatch_fails(self):
        self.edit_csv("examples/health-insurance/traceability.csv", lambda rows: rows[0].update(Objects="claim.line"))
        self.assertEqual(validator.validate(self.root)["status"], "fail")

    def test_manual_traceability_cannot_claim_static_pass(self):
        self.edit_csv("examples/health-insurance/traceability.csv", lambda rows: rows[-1].update(Static_Status="pass"))
        self.assertEqual(validator.validate(self.root)["status"], "fail")

    def test_source_references_are_bidirectional(self):
        self.edit_csv("rules/modeling-rules.csv", lambda rows: rows[0].update(Source_Refs="MVP synthesis"))
        self.assertIn("SOURCE_MAP", self.rule_failures())

    def test_cli_missing_input_is_explicit_failure(self):
        (self.root / "examples/health-insurance/model.json").write_text("{")
        result = subprocess.run([sys.executable, str(self.root / "scripts/validate_skill.py"), "--root", str(self.root)],
                                capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Validation input/output error", result.stderr)

    def test_full_package_and_persisted_report(self):
        report = validator.validate(self.root)
        self.assertEqual(report["status"], "pass", report["checks"])
        self.assertEqual(report, validator.read_json(self.root / "examples/health-insurance/validation/static-report.json"))


if __name__ == "__main__":
    unittest.main()
