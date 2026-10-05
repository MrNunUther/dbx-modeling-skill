"""Shape-envelope tests: normalization, metrics, scoring, and a targets->check closed loop."""
import itertools
import json
from pathlib import Path
import random
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import shape_profile as sp

ENVELOPE = json.loads((ROOT / "templates/shape-envelope.json").read_text())


def attr(name, sql_type="STRING", fk=None, tags="", regex=None, description=""):
    return dict(name=name, column_name=name, type=sql_type, foreign_key_to=fk, tags=tags,
                value_regex=regex, description=description)


def tiny_agent_model():
    """Two domains, four products: one cross-domain FK, one same-domain FK, one self-reference."""
    return {"agent_version": "4.3.3", "model": {"metric_views": [{}], "domains": [
        {"name": "party", "division": "Business", "subdomains": ["party identity"], "products": [
            {"name": "person", "primary_key": "person_id", "data_type": "master_data", "type": "Master",
             "attributes": [attr("person_id", "BIGINT"),
                            attr("parent_person_id", "BIGINT", "party.person.person_id"),
                            attr("created_timestamp", "TIMESTAMP")]},
            {"name": "status", "primary_key": "status_id", "data_type": "reference", "type": "reference",
             "attributes": [attr("status_id", "BIGINT"), attr("status_name")]}]},
        {"name": "sales", "division": "Operations", "subdomains": [{"name": "order capture"}], "products": [
            {"name": "order", "primary_key": "order_id", "data_type": "transactional_data", "type": "Transactional",
             "attributes": [attr("order_id", "BIGINT"),
                            attr("person_id", "BIGINT", "party.person.person_id", tags="restricted,pii"),
                            attr("order_status"), attr("order_date", "DATE")]},
            {"name": "order_line", "primary_key": "order_line_id", "data_type": "transactional_data",
             "type": "Transactional",
             "attributes": [attr("order_line_id", "BIGINT"), attr("order_id", "BIGINT", "sales.order.order_id"),
                            attr("line_amount", "DECIMAL(12,2)")]}]}]}}


def synthesize(brief, seed=7):
    """Deterministically realize a targets brief as an agent-format skeleton (names are placeholders)."""
    rng = random.Random(seed)
    sizing, graph, conv = brief["sizing"], brief["graph"], brief["conventions"]
    n_domains, per_domain = sizing["domains"], int(sizing["products_per_domain"]["target"])
    n_products = n_domains * per_domain
    roles = graph["domain_roles"]
    role = (["producer"] * roles["producers"] + ["consumer"] * roles["consumers"] + ["balanced"] * n_domains)[:n_domains]
    divisions = [d for d, n in brief["divisions"].items() for _ in range(n)]
    divisions += ["operations"] * (n_domains - len(divisions))
    quota = brief["data_types"]
    n_core = n_products - min(quota["transactional_data"], n_products)
    weight = {"producer": 0.85, "consumer": 0.15, "balanced": 0.5}
    scale = n_core / sum(weight[r] for r in role)
    core_per_domain, carry_core = [], 0.0
    for r in role:
        carry_core += min(per_domain, weight[r] * scale)
        core_per_domain.append(int(round(carry_core)) - sum(core_per_domain))
    core_types = [dt for dt in ("master_data", "reference_data", "association_data") for _ in range(quota[dt])]
    core_types = (core_types + ["master_data"] * n_core)[:n_core]
    products = []
    for d in range(n_domains):
        for k in range(per_domain):
            products.append(dict(domain=f"d{d}", data_type="core" if k < core_per_domain[d] else "transactional_data"))
    core = [p for p in products if p["data_type"] == "core"]
    for p, dt in zip(sorted(core, key=lambda p: rng.random()), core_types):
        p["data_type"] = dt
    # Global order: hubs and reference first, then remaining core, then transactions (keeps the graph acyclic).
    rank = {"master_data": 0, "reference_data": 0, "association_data": 1, "transactional_data": 2}
    products.sort(key=lambda p: (rank[p["data_type"]], rng.random()))
    for i, p in enumerate(products):
        p.update(index=i, name=f"p{i}", pk=f"p{i}_id")
    tx = [p for p in products if p["data_type"] == "transactional_data"]
    hubs = {p["index"] for p in products if p["data_type"] == "master_data"
            and role[int(p["domain"][1:])] == "producer"}
    hubs = set(sorted(hubs)[:graph["inbound_hubs"]["products"]])
    tx_target_rate = graph["in_degree"]["transactional"]["target"] * len(tx) / max(1, graph["fks"])
    arche = brief["archetypes"]
    span = set(rng.sample(range(n_products), arche["span"]))
    versioned = set(rng.sample(range(n_products), arche["versioned"]))
    hierarchy = set(rng.sample([p["index"] for p in products if p["data_type"] == "master_data"], arche["hierarchy"]))
    line = set(rng.sample([p["index"] for p in tx], arche["line"]))
    for p in products:
        if p["index"] in line:
            p["name"] = f"p{p['index']}_line"
    families = brief["attribute_families_per_product"]
    naming = dict(flag=("is_{}", "BOOLEAN"), identifier=("{}_number", "STRING"),
                  classifier=("{}_type", "STRING"), amount=("{}_amount", "DECIMAL(12,2)"),
                  status=("{}_status", "STRING"), text=("{}_name", "STRING"), measure=("{}_count", "INT"),
                  other=("{}_detail", "STRING"))
    carry = dict.fromkeys(families, 0.0)
    date_carry = 0.0
    cross_share = graph["cross_domain_fks"] / max(1, graph["fks"])
    hub_share = graph["inbound_hubs"]["share_of_inbound"]
    domains = {}
    for p in products:
        i = p["index"]
        key = f"{p['domain']}.{p['name']}"
        cols = [attr(p["pk"], "BIGINT", description="Surrogate key. " + "k" * 120)]
        kind = "transactional" if p["data_type"] == "transactional_data" else "master"
        fanout = max(0, round(rng.gauss(graph["out_degree"][kind]["target"], 1.5)))
        earlier = products[:i]
        chosen = set()
        for _ in range(fanout * 6):
            if len(chosen) >= fanout or not earlier:
                break
            cross = rng.random() < cross_share
            pool = [q for q in earlier if (q["domain"] != p["domain"]) == cross]
            want_tx = rng.random() < tx_target_rate
            typed = [q for q in pool if (q["data_type"] == "transactional_data") == want_tx] or pool
            hub_pool = [q for q in typed if q["index"] in hubs]
            pick = hub_pool if hub_pool and rng.random() < hub_share else typed
            if pick:
                chosen.add(rng.choice(pick)["index"])
        if i in hierarchy:
            cols.append(attr(f"parent_{p['pk']}", "BIGINT", f"{key}.{p['pk']}"))
        for t in sorted(chosen):
            tp = products[t]
            cols.append(attr(tp["pk"], "BIGINT", f"{tp['domain']}.{tp['name']}.{tp['pk']}",
                             description="Reference. " + "f" * 130))
        business = []
        temporal = []
        if i in span:
            temporal += ["effective", "termination"]
        carry["temporal"] += families["temporal"]
        temporal += [f"temporal{k}" for k in range(int(carry["temporal"]) - len(temporal))]
        carry["temporal"] -= int(carry["temporal"])
        for stem in temporal:
            date_carry += conv["temporal_date_share"]
            is_date = date_carry >= 1
            date_carry -= int(date_carry)
            business.append((f"{stem}_date" if is_date else f"{stem}_timestamp", "DATE" if is_date else "TIMESTAMP"))
        if i in versioned:
            business.append(("version_number", "INT"))
        if kind == "transactional":
            business.append((f"p{i}_status", "STRING"))
        for fam, (pattern, sql_type) in naming.items():
            carry[fam] += families[fam]
            count = int(carry[fam])
            carry[fam] -= count
            business += [(pattern.format(f"{fam}{k}"), sql_type) for k in range(count)]
        for k, (name, sql_type) in enumerate(business):
            regex = "^[A-Z0-9]+$" if rng.random() < conv["value_pattern_share"] * 1.25 else None
            tags = "confidential" if sql_type == "STRING" and rng.random() < conv["sensitive_tag_share"] * 2.5 else ""
            cols.append(attr(name, sql_type, tags=tags, regex=regex, description="Business attribute. " + "b" * 130))
        if rng.random() < conv["audit_column_product_share"]:
            cols += [attr("created_timestamp", "TIMESTAMP"), attr("updated_timestamp", "TIMESTAMP")]
        domains.setdefault(p["domain"], []).append(dict(
            name=p["name"], primary_key=p["pk"], data_type=p["data_type"], type=p["data_type"],
            description="Product grain. " + "g" * conv["product_description_chars"], attributes=cols))
    return {"model": {
        "metric_views": [{} for _ in range(sizing["metric_views"])],
        "domains": [dict(name=f"d{n}", division=divisions[n],
                         subdomains=[f"area{n} part{k}" for k in range(int(sizing["subdomains_per_domain"]["target"]))],
                         description="Domain charter. " + "c" * 400,
                         products=domains.get(f"d{n}", [])) for n in range(n_domains)]}}


class NormalizeTests(unittest.TestCase):
    def test_agent_format_with_mixed_subdomains(self):
        ir = sp.normalize(tiny_agent_model())
        self.assertEqual([d["subdomains"] for d in ir["domains"]], [["party identity"], ["order capture"]])
        self.assertEqual(ir["products"]["sales.order"]["data_type"], "transactional_data")
        self.assertEqual(ir["products"]["party.status"]["data_type"], "reference_data")
        self.assertIn(("sales.order", "party.person", "person_id"), ir["edges"])

    def test_canonical_example(self):
        ir = sp.load(ROOT / "examples/health-insurance/model.json")
        self.assertTrue(ir["products"])
        self.assertTrue(ir["edges"])
        self.assertTrue(all(p["pk"] for p in ir["products"].values()))


class ProfileTests(unittest.TestCase):
    def setUp(self):
        self.ir = sp.normalize(tiny_agent_model())
        self.metrics = sp.profile(self.ir)

    def test_graph_metrics(self):
        m = self.metrics
        self.assertEqual((m["domains"], m["products"], m["fks"]), (2, 4, 3))
        self.assertEqual(m["cross_domain_fk_share"], round(1 / 3, 4))
        self.assertEqual(m["self_ref_share"], round(1 / 3, 4))
        self.assertEqual(m["cycle_back_edges"], 0)
        self.assertEqual(m["siloed_product_share"], 0.25)
        self.assertEqual(m["pk_first_share"], 1.0)
        self.assertEqual(m["fk_name_ends_with_target_pk"], 1.0)

    def test_archetypes_and_defects(self):
        self.assertEqual(self.metrics["archetype_hierarchy"], 0.25)
        self.assertEqual(self.metrics["archetype_line"], 0.25)
        self.assertEqual(self.metrics["archetype_stateful_event"], 0.25)
        found = sp.defects(self.ir)
        self.assertEqual(found["pii_tag_on_fk_share"], round(1 / 3, 4))
        self.assertGreater(found["noncanonical_type_label_share"], 0)

    def test_cycle_detection(self):
        raw = tiny_agent_model()
        person = raw["model"]["domains"][0]["products"][0]
        person["attributes"].append(attr("order_id", "BIGINT", "sales.order.order_id"))
        self.assertGreater(sp.profile(sp.normalize(raw))["cycle_back_edges"], 0)


class BandAndCheckTests(unittest.TestCase):
    def test_stability_classes_and_scoring(self):
        fps = {f"i{k}": {"steady": 10.0 + k * 0.1, "noisy": float(1 + k * k), "domains": 10.0} for k in range(10)}
        bands = sp.build_bands(fps)
        self.assertEqual(bands["steady"]["stability"], "invariant")
        self.assertEqual(bands["noisy"]["stability"], "variable")
        self.assertTrue(bands["domains"]["scale"])
        inside = sp.check({"steady": 10.4, "noisy": 30.0, "domains": 10.0}, bands)
        self.assertEqual(inside["score"], 100.0)
        outside = sp.check({"steady": 50.0, "noisy": 30.0, "domains": 99.0}, bands)
        self.assertLess(outside["score"], 30)
        self.assertNotIn("domains", {r["metric"] for r in sp.check(fps["i0"], bands, ignore_scale=True)["metrics"]})


class EnvelopeTests(unittest.TestCase):
    def test_shipped_envelope_has_signature_and_holdout_evidence(self):
        for scope in ("mvm", "ecm"):
            data = ENVELOPE["scopes"][scope]
            self.assertGreaterEqual(data["count"], 10)
            invariant = {k for k, b in data["bands"].items() if b["stability"] == "invariant"}
            self.assertTrue({"pk_first_share", "fk_name_ends_with_target_pk", "cross_domain_fk_share",
                             "attrs_per_product_median"} <= invariant)
            self.assertGreaterEqual(data["leave_one_out"]["median"], 80)
        self.assertGreaterEqual(ENVELOPE["corpus_filter"]["min_agent_major"], 4)

    def test_teaching_slice_scores_low_without_scale(self):
        result = sp.check(sp.profile(sp.load(ROOT / "examples/health-insurance/model.json")),
                          ENVELOPE["scopes"]["mvm"]["bands"], ignore_scale=True)
        self.assertLess(result["score"], 50)

    def test_targets_closed_loop_scores_in_envelope(self):
        for scope in ("mvm", "ecm"):
            brief = sp.targets(ENVELOPE, scope)
            ir = sp.normalize(synthesize(brief))
            result = sp.check(sp.profile(ir), ENVELOPE["scopes"][scope]["bands"])
            self.assertGreaterEqual(result["score"], 80, (scope, [r for r in result["metrics"] if r["status"] == "out"]))
            self.assertTrue(all(v == 0 for v in sp.defects(ir).values()))

    def test_cli_check_text_and_threshold(self):
        command = [sys.executable, str(ROOT / "scripts/shape_profile.py"), "check",
                   str(ROOT / "examples/health-insurance/model.json"), "--envelope",
                   str(ROOT / "templates/shape-envelope.json"), "--scope", "mvm", "--ignore-scale",
                   "--format", "text", "--min-score", "90"]
        run = subprocess.run(command, capture_output=True, text=True)
        self.assertEqual(run.returncode, 1)
        self.assertTrue(run.stdout.startswith("shape score:"))


class AdviseTests(unittest.TestCase):
    BANDS = ENVELOPE["product_bands"]

    def advise_file(self, rel):
        return {r["product"]: r for r in sp.advise(sp.load(ROOT / rel), self.BANDS)}

    def test_parse_ddl_keys_and_references(self):
        ddl = """
        CREATE TABLE IF NOT EXISTS `cat`.`sales`.`customer` (
          customer_id BIGINT NOT NULL COMMENT 'Surrogate key.',
          customer_name STRING,
          CONSTRAINT pk_customer PRIMARY KEY (customer_id)
        ) USING DELTA;
        CREATE TABLE sales.orders (
          order_id BIGINT PRIMARY KEY,
          customer_id BIGINT REFERENCES sales.customer (customer_id),
          rep_id BIGINT,
          order_total DECIMAL(18,2)
        );
        CREATE TABLE people.rep (rep_id BIGINT, CONSTRAINT pk PRIMARY KEY (rep_id));
        ALTER TABLE sales.orders ADD CONSTRAINT fk_rep FOREIGN KEY (rep_id) REFERENCES people.rep (rep_id);
        """
        ir = sp.normalize(sp.parse_ddl(ddl))
        self.assertEqual(set(ir["products"]), {"sales.customer", "sales.orders", "people.rep"})
        self.assertEqual(ir["products"]["sales.customer"]["pk"], ["customer_id"])
        self.assertEqual(ir["products"]["sales.orders"]["pk"], ["order_id"])
        self.assertIn(("sales.orders", "sales.customer", "customer_id"), ir["edges"])
        self.assertIn(("sales.orders", "people.rep", "rep_id"), ir["edges"])

    def test_flat_table_reports_expected_anti_patterns(self):
        report = self.advise_file("examples/anti-patterns/claim_flat.sql")["claims.claim_flat"]
        codes = [f["code"] for f in report["findings"] if f["severity"] == "warn"]
        for code in ("SHP-COL-02", "SHP-COL-03", "SHP-FK-01", "SHP-PK-02", "SHP-TYPE-01", "SHP-TYPE-02", "SHP-TYPE-03"):
            self.assertIn(code, codes)
        self.assertEqual(codes.count("SHP-COL-01"), 2)
        embedded = {f["message"] for f in report["findings"] if f["code"] == "SHP-COL-04"}
        self.assertTrue(any("`member`" in m for m in embedded) and any("`provider`" in m for m in embedded))
        self.assertGreaterEqual(report["warnings"], 10)
        self.assertEqual(report["data_type_source"], "inferred")

    def test_remodel_and_teaching_slice_have_no_warnings(self):
        remodel = self.advise_file("examples/anti-patterns/claim_remodeled.sql")
        self.assertEqual(len(remodel), 6)
        self.assertEqual({k: r["warnings"] for k, r in remodel.items() if r["warnings"]}, {})
        self.assertEqual(remodel["claim.claim_diagnosis"]["data_type"], "transactional_data")
        self.assertEqual(remodel["claim.claim_line"]["data_type"], "transactional_data")
        teaching = self.advise_file("examples/health-insurance/model.json")
        self.assertEqual({k: r["warnings"] for k, r in teaching.items() if r["warnings"]}, {})

    def test_series_rules_spare_standards_and_address_lines(self):
        product = {"name": "site", "pk": ["site_id"], "data_type": "master_data", "attributes": [
            attr("site_id", "BIGINT"), attr("iso_9001_certified_flag", "BOOLEAN"),
            attr("iso_14001_certified_flag", "BOOLEAN"), attr("address_line_1"), attr("address_line_2"),
            attr("aging_30_amount", "DECIMAL(18,2)"), attr("aging_60_amount", "DECIMAL(18,2)"),
            attr("phone_1"), attr("phone_2"), attr("phone_3")]}
        raw = {"model": {"domains": [{"name": "ops", "products": [product]}]}}
        ir = sp.normalize(raw)
        findings = sp.product_smells(ir, next(iter(ir["products"])))
        groups = [f["message"] for f in findings if f["code"] == "SHP-COL-01"]
        self.assertEqual(len(groups), 1, groups)
        self.assertIn("phone", groups[0])

    def test_structural_smells_are_rare_in_corpus(self):
        prevalence = self.BANDS["smell_prevalence"]
        for code in ("SHP-PK-02", "SHP-COL-01", "SHP-COL-02", "SHP-COL-03", "SHP-TYPE-01", "SHP-TYPE-02", "SHP-TYPE-03"):
            self.assertLess(prevalence.get(code, 0), 0.02, code)
        self.assertGreater(self.BANDS["products"], 1000)
        for dt in ("master_data", "transactional_data", "association_data", "reference_data"):
            self.assertIn("attributes", self.BANDS["by_data_type"][dt]["metrics"])

    def test_classifier_is_generic_and_held_out(self):
        classifier = self.BANDS["classifier"]
        self.assertGreaterEqual(classifier["leave_one_out_accuracy"], 0.75)
        self.assertGreaterEqual(classifier["min_industries"], 8)
        self.assertEqual(len(classifier["features"]), len(classifier["counts"]))
        remodel = self.advise_file("examples/anti-patterns/claim_remodeled.sql")
        self.assertEqual(remodel["member.member"]["data_type"], "master_data")
        self.assertEqual(remodel["claim.claim"]["data_type"], "transactional_data")

    def test_association_needs_two_references(self):
        product = {"name": "member_role_assignment", "pk": ["member_role_assignment_id"], "data_type": "", "attrs": [
            dict(name="member_role_assignment_id", type="BIGINT", fk=None, tags=set(), regex=False, description=""),
            dict(name="role_code", type="STRING", fk=None, tags=set(), regex=False, description="")]}
        self.assertNotEqual(sp.classify(product, self.BANDS["classifier"]), "association_data")

    def test_enterprise_depth_example_is_complete(self):
        ir = sp.load(ROOT / "examples/enterprise-depth/claim.sql")
        report = sp.advise(ir, self.BANDS)
        by_name = {r["product"]: r for r in report}
        self.assertEqual(by_name["member.member"]["data_type"], "master_data")
        self.assertEqual(by_name["claim.claim"]["data_type"], "transactional_data")
        self.assertTrue(all(r["warnings"] == 0 for r in report))
        self.assertEqual(sp.product_score(report, self.BANDS)["score"], 100.0)

    def test_cli_advise_fail_on_warn(self):
        def run(rel):
            return subprocess.run([sys.executable, str(ROOT / "scripts/shape_profile.py"), "advise", str(ROOT / rel),
                                   "--envelope", str(ROOT / "templates/shape-envelope.json"), "--fail-on-warn"],
                                  capture_output=True, text=True)
        self.assertEqual(run("examples/anti-patterns/claim_flat.sql").returncode, 1)
        ok = run("examples/anti-patterns/claim_remodeled.sql")
        self.assertEqual(ok.returncode, 0, ok.stderr)
        self.assertIn("warn=0", ok.stdout)


    def test_composite_is_calibrated_and_separates_inputs(self):
        for scope in ("mvm", "ecm"):
            calibration = ENVELOPE["scopes"][scope]["composite"]
            self.assertGreaterEqual(calibration["median"], 80)
            self.assertGreaterEqual(calibration["product_median"], 85)

        def composite(rel):
            ir = sp.load(ROOT / rel)
            model = sp.check(sp.profile(ir), ENVELOPE["scopes"]["mvm"]["bands"], ignore_scale=True)["score"]
            return sp.composite_score(model, sp.product_score(sp.advise(ir, self.BANDS), self.BANDS))
        flat, remodel = composite("examples/anti-patterns/claim_flat.sql"), composite("examples/anti-patterns/claim_remodeled.sql")
        self.assertLess(flat, remodel)
        self.assertLess(remodel, ENVELOPE["scopes"]["mvm"]["composite"]["min"])

    def test_product_score_excludes_agent_defects(self):
        product = {"product": "x", "data_type": "master_data", "metrics": {"attributes": 39},
                   "findings": [{"code": "SHP-FK-05", "severity": "warn"}, {"code": "SHP-FK-03", "severity": "warn"}]}
        result = sp.product_score([product], self.BANDS)
        self.assertEqual(result["conformance"], 1.0)
        self.assertEqual(result["agent_defect_warnings"], 2)
        self.assertEqual(result["score"], 100.0)

    def test_depad_discounts_boilerplate_only(self):
        raw = synthesize(sp.targets(ENVELOPE, "mvm", 4))
        for domain in raw["model"]["domains"]:
            for product in domain["products"]:
                for a in product["attributes"]:
                    if not a["foreign_key_to"] and a["name"] != product["primary_key"] \
                            and not a["name"].endswith("_timestamp"):
                        a["name"] = a["column_name"] = f"{product['name']}_{a['name']}"
        clean_ir = sp.normalize(raw)
        _, summary = sp.depad(clean_ir)
        self.assertEqual(summary["stripped_columns"], [])
        stock = "This supports municipal audit, routing, reconciliation, and reporting."
        block = ["created_timestamp", "updated_timestamp", "record_quality_score", "lineage_batch_id",
                 "retention_category_code", "stewardship_review_date"]
        for domain in raw["model"]["domains"]:
            for product in domain["products"]:
                have = {a["name"] for a in product["attributes"]}
                product["attributes"] += [attr(n, description=f"Column {n}. {stock}") for n in block if n not in have]
                for a in product["attributes"]:
                    a["description"] = (a["description"] + " " + stock).strip()
        padded, summary = sp.depad(sp.normalize(raw))
        self.assertEqual(len(summary["stripped_columns"]), len(block) - sp.PADDING_ALLOWANCE)
        self.assertGreater(summary["repeated_sentence_rate"], 0.9)
        self.assertTrue(all(stock not in a["description"] for p in padded["products"].values() for a in p["attrs"]))
        widths = lambda ir: sorted(len(p["attrs"]) for p in ir["products"].values())
        self.assertLessEqual(widths(padded), [w + sp.PADDING_ALLOWANCE for w in widths(clean_ir)])
        self.assertEqual(sp.depad(dict(clean_ir, products=dict(list(clean_ir["products"].items())[:3])))[1]["stripped_columns"], [])

    def test_slice_reference_is_calibrated(self):
        for scope in ("mvm", "ecm"):
            ref = ENVELOPE["scopes"][scope]["slice"]
            self.assertGreaterEqual(ref["slices"], 45)
            self.assertGreaterEqual(ref["leave_one_out"]["median"], 80)
            self.assertGreaterEqual(ref["composite"]["min"], 75)

    def test_slice_ir_drops_references_leaving_the_slice(self):
        ir = sp.normalize(tiny_agent_model())
        sliced = sp.slice_ir(ir, {"sales"})
        self.assertEqual(set(p["name"] for p in sliced["products"].values()), {"order", "order_line"})
        order = next(p for p in sliced["products"].values() if p["name"] == "order")
        self.assertNotIn("person_id", [a["name"] for a in order["attrs"]])
        self.assertTrue(all(e[0] in sliced["products"] and e[1] in sliced["products"] for e in sliced["edges"]))

    def test_cli_check_picks_reference_by_scope(self):
        def reference(*extra):
            run = subprocess.run([sys.executable, str(ROOT / "scripts/shape_profile.py"), "check",
                                  str(ROOT / "examples/health-insurance/model.json"), "--envelope",
                                  str(ROOT / "templates/shape-envelope.json"), "--scope", "mvm", *extra],
                                 capture_output=True, text=True)
            return json.loads(run.stdout)["reference"]
        self.assertEqual(reference(), "slice")
        self.assertEqual(reference("--reference", "full"), "full")

    def test_cli_check_reports_composite(self):
        run = subprocess.run([sys.executable, str(ROOT / "scripts/shape_profile.py"), "check",
                              str(ROOT / "examples/health-insurance/model.json"), "--envelope",
                              str(ROOT / "templates/shape-envelope.json"), "--scope", "mvm", "--ignore-scale",
                              "--format", "text", "--min-composite", "80"], capture_output=True, text=True)
        self.assertEqual(run.returncode, 1)
        self.assertIn("composite:", run.stdout)
        self.assertIn("product score:", run.stdout)


if __name__ == "__main__":
    unittest.main()
