#!/usr/bin/env python3
"""Validate the bounded MVP package and canonical example without workspace access."""
import argparse
import csv
import json
from pathlib import Path
import re
import sys

try:
    from jsonschema import Draft202012Validator
except ImportError:
    raise SystemExit("Missing jsonschema. Install the declared requirements.txt in a virtual environment.")

CHECK_RULES = {
    "SHAPE": "DBX-SHAPE-001", "PROTECTED": "DBX-INTENT-001",
    "OBJECTS": "DBX-OBJ-001", "NAMES": "DBX-NAME-001", "TYPES": "DBX-TYPE-001",
    "ENUMS": "DBX-ENUM-001", "PK": "DBX-KEY-001", "FK_TARGET": "DBX-KEY-002",
    "FK_TYPES": "DBX-KEY-003", "RELATIONS": "DBX-REL-001", "ROLES": "DBX-REL-002",
    "GRAPH": "DBX-GRAPH-001", "CONNECTIVITY": "DBX-GRAPH-002",
    "METADATA": "DBX-META-001", "SENSITIVITY": "DBX-META-002",
    "TAGS": "DBX-META-003", "METRICS": "DBX-MET-001",
    "ARTIFACTS": "DBX-ART-001", "REPORT": "DBX-VERIFY-001",
    "REQUIREMENTS": "DBX-VERIFY-002", "PACKAGE": "DBX-PACK-001",
    "SOURCE_MAP": "DBX-MAP-001",
}
MODEL_CHECKS = set(CHECK_RULES) - {"ARTIFACTS", "REPORT", "PACKAGE", "SOURCE_MAP"}
IDENT = re.compile(r"[a-z][a-z0-9_]*\Z")
SQL_TYPES = {"STRING", "BIGINT", "INT", "SMALLINT", "TINYINT", "BOOLEAN", "DATE", "TIMESTAMP", "DOUBLE", "FLOAT"}
PLACEHOLDERS = {"tbd", "todo", "n/a", "none", "-", "unknown"}
RULE_FIELDS = ["ID", "Group", "Scope", "Name", "Requirement", "Example", "Severity", "Profile", "Phase",
               "Check_ID", "Override_Policy", "Source_Refs"]
DISPOSITIONS = {"adopted", "adapted", "merged", "deferred", "excluded", "incomplete"}


def read_json(path):
    return json.loads(path.read_text())


def schema_errors(value, path):
    schema = read_json(path)
    Draft202012Validator.check_schema(schema)
    return list(Draft202012Validator(schema).iter_errors(value))


def finding(check, obj, status, expected, observed, evidence="model.json", remediation=None):
    return dict(check_id=check, rule_id=CHECK_RULES.get(check, "DBX-VERIFY-001"), object=obj,
                status=status, severity="error", expected=expected, observed=observed,
                evidence=evidence, remediation=remediation or
                ("No action required at this evidence level." if status == "pass" else "Correct the identified contract or design issue and rerun checks."))


class Checks:
    def __init__(self):
        self.results = []
        self.attempted = set()

    def require(self, check, condition, obj, expected, observed):
        self.attempted.add(check)
        if not condition:
            self.results.append(finding(check, obj, "fail", expected, observed))

    def finish(self, checks):
        failed = {item["check_id"] for item in self.results}
        for check in sorted(checks - failed):
            self.results.append(finding(check, "model", "pass",
                                        "Applicable bounded checks satisfied.",
                                        "No violations found in the supplied contract."))
        return self.results


def valid_type(value):
    if value in SQL_TYPES:
        return True
    match = re.fullmatch(r"DECIMAL\((\d+),(\d+)\)", value)
    return bool(match and 1 <= int(match[1]) <= 38 and 0 <= int(match[2]) <= int(match[1]))


def expression_columns(expression, dimension):
    """Only this explicit expression subset is supported; no general SQL parsing."""
    if dimension:
        if IDENT.fullmatch(expression):
            return [expression]
        match = re.fullmatch(r"DATE_TRUNC\('MONTH', ([a-z][a-z0-9_]*)\)", expression)
        return [match[1]] if match else None
    if expression == "COUNT(1)":
        return []
    match = re.fullmatch(r"SUM\(([a-z][a-z0-9_]*)\)", expression)
    if match:
        return [match[1]]
    match = re.fullmatch(r"SUM\(([a-z][a-z0-9_]*)\) / NULLIF\(SUM\(([a-z][a-z0-9_]*)\), 0\)", expression)
    return sorted(set(match.groups())) if match else None


def validate_model(model, root):
    checks = Checks()
    errors = schema_errors(model, root / "templates/model.schema.json")
    if errors:
        for error in errors:
            obj = ".".join(str(part) for part in error.absolute_path) or "model"
            checks.require("SHAPE", False, obj, "Canonical model schema 1.0.0.", error.message)
        return checks.results + [
            finding(check, "model", "blocked", "Valid canonical shape before semantic checking.",
                    "Shape errors prevent this check.", remediation="Correct shape errors and rerun validation.")
            for check in sorted(MODEL_CHECKS - {"SHAPE"})
        ]
    items = {}
    domain_names = []
    domain_schemas = []
    attributes = {}
    cap = model["conventions"]["inline_enum_cap"]
    checks.require("TYPES", valid_type(model["conventions"]["key_type"]), "conventions.key_type",
                   "Supported default key type.", model["conventions"]["key_type"])

    def meaningful(text):
        return len(text.strip()) >= 10 and text.strip().lower() not in PLACEHOLDERS

    def tags_valid(tags):
        reserved = {"primary_key", "foreign_key", "dbx_business_glossary_term", "dbx_classification",
                    "dbx_data_type", "dbx_subdomain", "dbx_steward", "dbx_division", "dbx_standard_references"}
        return all(IDENT.fullmatch(key) and key not in reserved and bool(value.strip())
                   for key, value in tags.items())

    def unique(check, names, obj):
        checks.require(check, len(names) == len(set(name.casefold() for name in names)),
                       obj, "Unique case-insensitive scoped names.", repr(names))

    for domain in model["domains"]:
        name = domain["name"]
        domain_names.append(name)
        domain_schemas.append(domain["physical_schema"])
        checks.require("NAMES", name == domain["physical_schema"], name,
                       "Default domain/schema identity.", domain["physical_schema"])
        checks.require("OBJECTS", domain["division"] in model["conventions"]["division_taxonomy"],
                       name, "Division in declared taxonomy.", domain["division"])
        checks.require("METADATA", meaningful(domain["description"]) and bool(domain["owner"].strip()),
                       name, "Substantive domain description and owner.", domain["description"])
        checks.require("TAGS", tags_valid(domain["tags"]), name, "Structured nonreserved tags.", repr(domain["tags"]))
        subdomains = [sub["name"] for sub in domain["subdomains"]]
        unique("NAMES", subdomains, name + ":subdomains")
        for sub in domain["subdomains"]:
            checks.require("METADATA", meaningful(sub["description"]), name + "." + sub["name"],
                           "Substantive grouping description.", sub["description"])
        unique("NAMES", [p["name"] for p in domain["products"]], name + ":products")
        unique("NAMES", [p["physical_name"] for p in domain["products"]], name + ":physical_products")
        for product in domain["products"]:
            path = name + "." + product["name"]
            items[path] = product
            checks.require("NAMES", product["name"] == product["physical_name"], path,
                           "Default logical/physical identity.", product["physical_name"])
            checks.require("OBJECTS", meaningful(product["grain"]) and bool(product["steward"].strip()),
                           path, "Declared grain and steward.", product["grain"])
            checks.require("METADATA", meaningful(product["description"]) and product["subdomain"] in subdomains,
                           path, "Description and existing semantic subdomain.", product["description"])
            checks.require("TAGS", tags_valid(product["tags"]), path, "Structured nonreserved tags.", repr(product["tags"]))
            unique("NAMES", [a["name"] for a in product["attributes"]], path + ":attributes")
            unique("NAMES", [a["physical_name"] for a in product["attributes"]], path + ":physical_attributes")
            aa = {a["name"]: a for a in product["attributes"]}
            attributes[path] = aa
            for attribute in product["attributes"]:
                apath = path + "." + attribute["name"]
                checks.require("NAMES", attribute["name"] == attribute["physical_name"], apath,
                               "Default logical/physical identity.", attribute["physical_name"])
                checks.require("TYPES", valid_type(attribute["type"]), apath,
                               "Supported primitive SQL type; valid DECIMAL bounds.", attribute["type"])
                checks.require("TYPES", not attribute["monetary"] or attribute["type"].startswith("DECIMAL("),
                               apath, "Declared monetary fields preserve explicit DECIMAL precision.", attribute["type"])
                checks.require("METADATA", meaningful(attribute["description"]) and bool(attribute["glossary"].strip())
                               and attribute["glossary"].strip().lower() not in PLACEHOLDERS,
                               apath, "Substantive description and glossary.", attribute["description"])
                checks.require("TAGS", tags_valid(attribute["tags"]), apath, "Structured nonreserved tags.", repr(attribute["tags"]))
                sensitive = attribute["sensitivity"] != "none"
                marker = attribute["tags"].get("sensitivity")
                checks.require("SENSITIVITY", not sensitive or (
                    attribute["classification"] == "restricted" and marker == attribute["sensitivity"]),
                    apath, "Declared sensitive fields have restricted classification and matching marker.",
                    attribute["classification"] + ":" + repr(attribute["tags"]))
                checks.require("SENSITIVITY", marker is None or (sensitive and marker == attribute["sensitivity"]),
                               apath, "Sensitivity marker agrees with explicit sensitivity declaration.", repr(marker))
                enum_values = attribute["allowed_values"]
                pattern = attribute["pattern"]
                checks.require("ENUMS", (not enum_values and not pattern) or (
                    attribute["type"] == "STRING" and not (enum_values and pattern) and len(enum_values) <= cap),
                    apath, "Separate STRING enum/pattern within configured cap.", repr(enum_values) + ":" + pattern)
                if pattern:
                    try:
                        re.compile(pattern)
                    except re.error as error:
                        checks.require("ENUMS", False, apath, "Valid Python pattern; JVM compatibility requires live checks.", str(error))
            pk = product["primary_key"]
            checks.require("PK", all(column in aa and not aa[column]["nullable"] for column in pk),
                           path, "Declared PK tuple of non-null existing columns.", repr(pk))
            for business_key in product["business_keys"]:
                checks.require("PK", all(column in aa for column in business_key),
                               path, "Existing business uniqueness columns.", repr(business_key))
    unique("NAMES", domain_names, "domains")
    unique("NAMES", domain_schemas, "physical_schemas")
    protected = model["protected"]
    checks.require("PROTECTED", set(protected["domains"]).issubset(domain_names), "domains",
                   "All protected domains preserved.", repr(domain_names))
    checks.require("PROTECTED", set(protected["products"]).issubset(items), "products",
                   "All protected products preserved.", repr(list(items)))
    for key, actual in [("exact_domain_count", len(model["domains"])), ("exact_product_count", len(items))]:
        checks.require("PROTECTED", protected[key] is None or protected[key] == actual, key,
                       "Protected exact count.", str(actual))
    unique("NAMES", [relation["id"] for relation in model["relationships"]], "relationship IDs")
    roles = {}
    relationship_tuples = set()
    graph = {path: set() for path in items}
    connected = set()
    for relation in model["relationships"]:
        source, target = relation["source"], relation["target"]
        rid = relation["id"]
        source_columns, target_columns = relation["source_columns"], relation["target_columns"]
        source_attrs, target_attrs = attributes.get(source, {}), attributes.get(target, {})
        endpoints = source in items and target in items
        columns_exist = all(c in source_attrs for c in source_columns) and all(c in target_attrs for c in target_columns)
        checks.require("FK_TARGET", endpoints and columns_exist and target_columns == items.get(target, {}).get("primary_key"),
                       rid, "Existing source columns and exact target PK tuple.", source + " -> " + target)
        checks.require("FK_TYPES", columns_exist and len(source_columns) == len(target_columns) and all(
            source_attrs[s]["type"] == target_attrs[t]["type"] for s, t in zip(source_columns, target_columns)),
            rid, "Exact tuple arity and types.", repr(source_columns) + " -> " + repr(target_columns))
        roles.setdefault((source, target), []).append(relation["role"])
        signature = (source, tuple(source_columns), target, tuple(target_columns))
        checks.require("ROLES", signature not in relationship_tuples, rid,
                       "No duplicate FK tuple disguised by a different role.", repr(signature))
        relationship_tuples.add(signature)
        if columns_exist:
            nullable = [source_attrs[c]["nullable"] for c in source_columns]
            checks.require("RELATIONS", all(n == relation["optional"] for n in nullable), rid,
                           "Uniform tuple nullability equals optionality.", repr(nullable))
        checks.require("RELATIONS", meaningful(relation["justification"]) and (
            relation["population_phase"] == "at_creation" or meaningful(relation["enrichment_path"])),
            rid, "Justification and explicit later-enrichment path.", relation["justification"])
        checks.require("RELATIONS", relation["population_phase"] == "at_creation" or relation["optional"],
                       rid, "Delayed population permits an initially nullable FK.", relation["population_phase"])
        if endpoints and relation["cardinality"] == "one_to_one":
            unique_keys = [items[source]["primary_key"]] + items[source]["business_keys"]
            checks.require("RELATIONS", any(set(source_columns) == set(key) for key in unique_keys),
                           rid, "One-to-one source tuple declares uniqueness; row proof remains separate.", repr(unique_keys))
        self_pk = endpoints and source == target and source_columns == items[source]["primary_key"]
        checks.require("ROLES", not self_pk, rid, "PK never declared as its own self-FK.", repr(source_columns))
        hierarchical = relation["hierarchical"]
        checks.require("RELATIONS", not hierarchical or (source == target and not self_pk),
                       rid, "Hierarchy flag only on distinct self-reference.", str(hierarchical))
        if endpoints:
            if source != target:
                connected.update([source, target])
            if not (source == target and hierarchical and not self_pk):
                graph[source].add(target)
    for pair, labels in roles.items():
        unique("ROLES", labels, " -> ".join(pair))

    # Iterative DFS supports large enterprise graphs without Python recursion limits.
    colors = {node: 0 for node in graph}
    cyclic = False
    for start in graph:
        if colors[start]:
            continue
        colors[start] = 1
        stack = [(start, iter(graph[start]))]
        while stack:
            node, children = stack[-1]
            child = next(children, None)
            if child is None:
                colors[node] = 2
                stack.pop()
            elif colors[child] == 1:
                cyclic = True
            elif colors[child] == 0:
                colors[child] = 1
                stack.append((child, iter(graph[child])))
    checks.require("GRAPH", not cyclic or model["conventions"]["graph_policy"] == "allow_cycles",
                   "relationships", "Declared dependency policy respected.", "Cycle detected." if cyclic else "Acyclic.")
    for path, product in items.items():
        checks.require("CONNECTIVITY", path in connected or meaningful(product["standalone_reason"]),
                       path, "Purposeful connectivity or explicit standalone justification.", product["standalone_reason"] or "No standalone justification.")
    metrics = model["metric_views"]
    metric_paths = [metric["schema"] + "." + metric["name"] for metric in metrics]
    unique("NAMES", metric_paths, "metric identities")
    checks.require("NAMES", not set(metric_paths).intersection(items), "metric identities",
                   "Metric identities do not collide with tables.", repr(metric_paths))
    for metric in metrics:
        mpath = metric["schema"] + "." + metric["name"]
        aa = attributes.get(metric["source"], {})
        checks.require("METRICS", metric["source"] in items, mpath, "Existing declared metric source.", metric["source"])
        unique("METRICS", [e["name"] for e in metric["dimensions"] + metric["measures"]], mpath)
        for dimension, expressions in [(True, metric["dimensions"]), (False, metric["measures"])]:
            for expression in expressions:
                used = expression_columns(expression["expression"], dimension)
                checks.require("METRICS", used is not None and set(used or []) == set(expression["columns"])
                               and all(column in aa for column in expression["columns"]),
                               mpath + "." + expression["name"], "Supported expression with exact existing source dependencies.",
                               expression["expression"] + ":" + repr(expression["columns"]))
                if used and all(column in aa for column in used):
                    if not dimension:
                        numeric = all(aa[column]["type"] in {"INT", "BIGINT", "SMALLINT", "TINYINT", "FLOAT", "DOUBLE"}
                                      or aa[column]["type"].startswith("DECIMAL(") for column in used)
                        checks.require("METRICS", numeric, mpath, "SUM inputs are numeric.", repr(used))
                    elif expression["expression"].startswith("DATE_TRUNC"):
                        checks.require("METRICS", aa[used[0]]["type"] in {"DATE", "TIMESTAMP"}, mpath,
                                       "DATE_TRUNC input is temporal.", aa[used[0]]["type"])
    object_ids = set(domain_names) | set(items) | set(metric_paths)
    object_ids |= {path + "." + attr for path, aa in attributes.items() for attr in aa}
    unique("REQUIREMENTS", [r["id"] for r in model["requirements"]], "requirement IDs")
    for req in model["requirements"]:
        checks.require("REQUIREMENTS", all(o in object_ids for o in req["objects"]), req["id"],
                       "Existing declared requirement targets.", repr(req["objects"]))
        checks.require("REQUIREMENTS", all(c in CHECK_RULES or c == "manual" for c in req["checks"])
                       and (req["manual"] == ("manual" in req["checks"])), req["id"],
                       "Valid check IDs with explicit manual flag.", repr(req["checks"]))
    return checks.finish(MODEL_CHECKS)


def read_csv(path):
    with path.open(newline="") as stream:
        reader = csv.DictReader(stream)
        rows = list(reader)
        if reader.fieldnames is None or any(None in row or any(v is None for v in row.values()) for row in rows):
            raise ValueError("Malformed CSV fields in " + str(path))
        return reader.fieldnames, rows


def validate_rules(root):
    checks = Checks()
    fields, rules = read_csv(root / "rules/modeling-rules.csv")
    checks.require("PACKAGE", fields == RULE_FIELDS, "modeling-rules.csv", "Canonical rule fields.", repr(fields))
    ids = [r["ID"] for r in rules]
    checks.require("PACKAGE", len(ids) == len(set(ids)), "modeling-rules.csv", "Unique canonical IDs.", repr(ids))
    checks.require("PACKAGE", set(CHECK_RULES.values()).issubset(ids), "modeling-rules.csv",
                   "Every automated check maps to a rule.", repr(set(CHECK_RULES.values()) - set(ids)))
    for row in rules:
        checks.require("PACKAGE", all(row[field].strip() for field in RULE_FIELDS) and
                       row["Check_ID"] in set(CHECK_RULES) | {"manual"} and
                       row["Severity"] in {"error", "advisory"} and
                       row["Override_Policy"] in {"not_overridable", "explicit_policy_or_review"}, row["ID"],
                       "Complete rule metadata and supported/manual check ID.", row["Check_ID"])
    _, mapping = read_csv(root / "rules/source-rule-map.csv")
    occurrences = [(r["Source_File"], r["Source_Line"]) for r in mapping]
    checks.require("SOURCE_MAP", len(mapping) == 264 and len(set(occurrences)) == 264,
                   "source-rule-map.csv", "All 264 unique source occurrences.", str(len(mapping)))
    duplicate = [r for r in mapping if r["Source_ID"] == "QGATE-RUL-011"]
    checks.require("SOURCE_MAP", len(duplicate) == 2 and len({r["Canonical_IDs"] for r in duplicate}) == 2,
                   "QGATE-RUL-011", "Both source occurrences map distinctly.", repr(duplicate))
    for row in mapping:
        checks.require("SOURCE_MAP", row["Disposition"] in DISPOSITIONS and bool(row["Rationale"].strip())
                       and all(target in ids for target in row["Canonical_IDs"].split(";")), row["Source_ID"],
                       "Explicit disposition, rationale, and existing canonical targets.", row["Disposition"])
        if row["Source_ID"] in {"ATT-RUL-069", "ATT-RUL-070"}:
            checks.require("SOURCE_MAP", row["Disposition"] == "incomplete", row["Source_ID"],
                           "Truncated source remains explicitly incomplete.", row["Disposition"])
    references = {}
    for row in mapping:
        for target in row["Canonical_IDs"].split(";"):
            references.setdefault(target, set()).add(row["Source_ID"] + "@" + row["Source_Line"])
    for row in rules:
        expected = references.get(row["ID"], {"MVP synthesis"})
        checks.require("SOURCE_MAP", set(row["Source_Refs"].split(";")) == expected,
                       row["ID"], "Bidirectional occurrence-level source references.", row["Source_Refs"])
    _, instructions = read_csv(root / "rules/source-instruction-map.csv")
    lines = [r["Source_Line"] for r in instructions]
    checks.require("SOURCE_MAP", len(instructions) == 434 and len(set(lines)) == 434,
                   "source-instruction-map.csv", "Every nonblank source line has one disposition.", str(len(instructions)))
    for row in instructions:
        target = row["Canonical_Instruction"]
        checks.require("SOURCE_MAP", row["Disposition"] in DISPOSITIONS and bool(row["Rationale"].strip()) and
                       (target in {"I-0" + str(i) for i in range(1, 9)} if row["Disposition"] != "excluded" else not target),
                       "instruction:" + row["Source_Line"], "Valid explicit instruction disposition.", row["Disposition"])
    return checks.finish({"PACKAGE", "SOURCE_MAP"})


def validate_package(root):
    root = root.resolve()
    checks = Checks()
    required = ["SKILL.md", "README.md", "agents/openai.yaml", "assets/modeling.svg", "assets/modeling.png",
                "LICENSE", "NOTICE", "requirements.txt", "rules/instructions.md", "references/source-assessment.md",
                "references/shape-topology.md", "templates/shape-envelope.json", "scripts/shape_profile.py",
                "examples/anti-patterns/README.md", "examples/anti-patterns/claim_flat.sql",
                "examples/anti-patterns/claim_remodeled.sql"]
    for relative in required:
        checks.require("PACKAGE", (root / relative).is_file(), relative, "Required package file.", "Present" if (root / relative).is_file() else "Missing")
    skill_path = root / "SKILL.md"
    if skill_path.is_file():
        text = skill_path.read_text()
        checks.require("PACKAGE", text.startswith("---\nname: dbx-modeling-skill\n") and
                       "description:" in text and 'version: "0.1.0"' in text and len(text.splitlines()) <= 300,
                       "SKILL.md", "Correct identifier/frontmatter and <=300 lines.", str(len(text.splitlines())) + " lines")
    for path in list((root / "references").glob("*.md")) + list((root / "rules").glob("*.md")) + list((root / "examples").rglob("*.md")) + [root / "SKILL.md", root / "README.md"]:
        if not path.is_file():
            continue
        for link in re.findall(r"\]\(([^)]+)\)", path.read_text()):
            if "://" in link or link.startswith("#"):
                continue
            dest = (path.parent / link.split("#", 1)[0]).resolve()
            checks.require("PACKAGE", dest.is_relative_to(root) and dest.exists(), str(path.relative_to(root)),
                           "Resolvable package-relative link.", link)
    agent = root / "agents/openai.yaml"
    if agent.is_file():
        # Validate exactly the authored JSON-string scalar subset, not arbitrary YAML.
        values = {}
        for line in agent.read_text().splitlines()[1:]:
            key, separator, raw = line.strip().partition(": ")
            if not separator:
                checks.require("PACKAGE", False, "openai.yaml", "JSON-quoted scalar subset.", line)
                continue
            values[key] = json.loads(raw)
        for key in ["display_name", "short_description", "default_prompt", "brand_color", "icon_small", "icon_large"]:
            checks.require("PACKAGE", isinstance(values.get(key), str) and bool(values[key]), key,
                           "Curated metadata value.", repr(values.get(key)))
        for key in ["icon_small", "icon_large"]:
            dest = (root / values.get(key, "")).resolve()
            checks.require("PACKAGE", dest.is_relative_to(root) and dest.is_file(), key, "Existing neutral asset.", str(dest))
    png = root / "assets/modeling.png"
    if png.is_file():
        checks.require("PACKAGE", png.read_bytes().startswith(b"\x89PNG\r\n\x1a\n"), "modeling.png",
                       "PNG raster signature.", str(png.stat().st_size) + " bytes")
    return checks.finish({"PACKAGE"})


def validate_artifacts(model, root):
    from render_example import render
    results = []
    base = root / "examples/health-insurance"
    expected = render(model)
    for relative, text in expected.items():
        path = base / relative
        if not path.is_file() or path.read_text() != text:
            results.append(finding("ARTIFACTS", relative, "fail", "Exact deterministic canonical rendering.",
                                   "Missing or changed output.", relative))
    actual = {str(p.relative_to(base)) for area in ["schemas", "metrics", "diagram"]
              for p in (base / area).glob("*") if p.is_file()}
    expected_core = {r for r in expected if r.split("/")[0] in {"schemas", "metrics", "diagram"}}
    if actual != expected_core:
        results.append(finding("ARTIFACTS", "example", "fail", "No extra or missing derivative files.",
                               repr(sorted(actual.symmetric_difference(expected_core)))))
    return results or [finding("ARTIFACTS", "example", "pass", "Canonical file parity.",
                               "All supported derivatives agree; not live parity.")]


def report_for(model, findings):
    invalid_shape = not isinstance(model, dict) or any(
        f["check_id"] == "SHAPE" and f["status"] == "fail" for f in findings
    )
    raw_requirements = model.get("requirements", []) if isinstance(model, dict) else []
    requirements = raw_requirements if isinstance(raw_requirements, list) else []
    version = model.get("model_version", "invalid_input") if isinstance(model, dict) else "invalid_input"
    if not isinstance(version, str) or not version.strip():
        version = "invalid_input"
    passed = {f["check_id"] for f in findings if f["status"] == "pass"}
    failed = {f["check_id"] for f in findings if f["status"] == "fail"}
    verified = 0
    manual = 0
    for req in requirements:
        if not isinstance(req, dict):
            continue
        manual += int(req.get("manual") is True)
        if not invalid_shape and not req["manual"] and all(c in passed - failed for c in req["checks"]) and "REQUIREMENTS" not in failed:
            verified += 1
    live = [finding(check, "catalog" if check != "DATA" else "rows", "not_run",
                    "Actual authorized workspace evidence.", "Offline release; no connection or execution.",
                    "No live evidence.", "Obtain explicit scoped authorization and collect actual results.")
            for check in ["WORKSPACE", "PHYSICAL", "DATA"]]
    return {
        "contract_version": "1.0.0", "model_version": version,
        "evidence_level": "static", "status": "fail" if failed else "pass", "checks": findings + live,
        "coverage": {"applicable": len(requirements), "verified_static": verified, "manual_unverified": manual},
        "limitations": ["Static shape/structural/file-parity checks only; no workspace compatibility, physical parity, or data-integrity evidence.",
                        "Business meaning, sensitivity discovery, snapshots, process coverage, and regulatory correctness require manual review.",
                        "Supported metric expressions and deterministic representations are bounded, not general SQL/YAML parsing."]}


def validate_report(report, root):
    results = []
    for error in schema_errors(report, root / "templates/validation-report.schema.json"):
        results.append(finding("REPORT", "report", "fail", "Report schema.", error.message))
    if results:
        return results
    live = {"WORKSPACE", "PHYSICAL", "DATA"}
    if report["evidence_level"] not in {"designed", "static"}:
        results.append(finding("REPORT", "evidence_level", "fail",
                               "This offline implementation validates only designed/static reports.",
                               "Live evidence requires a separately implemented authorized verifier."))
    for check in report["checks"]:
        if check["check_id"] in live and check["status"] == "pass":
            results.append(finding("REPORT", check["check_id"], "fail", "No live pass at offline evidence level.",
                                   "Unsupported live pass claim."))
    failures = any(c["status"] == "fail" and c["severity"] == "error" for c in report["checks"])
    if report["status"] == "pass" and failures:
        results.append(finding("REPORT", "report", "fail", "Hard failures prevent pass.", "Pass with failed checks."))
    coverage = report["coverage"]
    if coverage["verified_static"] + coverage["manual_unverified"] > coverage["applicable"]:
        results.append(finding("REPORT", "coverage", "fail", "Honest coverage counts.", repr(coverage)))
    return results or [finding("REPORT", "report", "pass", "Schema and offline evidence boundaries.",
                               "No contradictory offline claims found.")]


def validate(root, check_trace_status=True):
    model = read_json(root / "examples/health-insurance/model.json")
    findings = validate_model(model, root)
    findings += validate_package(root) + validate_rules(root)
    if not any(f["status"] == "fail" and f["check_id"] == "SHAPE" for f in findings):
        findings += validate_artifacts(model, root)
        _, trace = read_csv(root / "examples/health-insurance/traceability.csv")
        expected_trace = {r["id"]: r for r in model["requirements"]}
        actual_trace = {r["Requirement_ID"]: r for r in trace}
        if len(trace) != len(expected_trace) or set(actual_trace) != set(expected_trace):
            findings.append(finding("REQUIREMENTS", "traceability.csv", "fail",
                                    "One traceability row per canonical requirement.", "Missing/duplicate/extra requirement row."))
        for rid, requirement in expected_trace.items():
            row = actual_trace.get(rid)
            if row and (row["Objects"] != ";".join(requirement["objects"]) or row["Checks"] != ";".join(requirement["checks"])
                        or row["Manual_Review"] != ("required" if requirement["manual"] else "not_applicable")):
                findings.append(finding("REQUIREMENTS", rid, "fail", "CSV targets/checks match canonical requirement.",
                                        "Traceability mismatch."))
        if check_trace_status:
            failed_ids = {c["check_id"] for c in findings if c["status"] == "fail"}
            for rid, requirement in expected_trace.items():
                row = actual_trace.get(rid)
                expected_status = "not_run" if requirement["manual"] else (
                    "fail" if failed_ids.intersection(requirement["checks"]) else "pass")
                if row and row["Static_Status"] != expected_status:
                    findings.append(finding("REQUIREMENTS", rid, "fail",
                                            "Traceability status agrees with actual static checks.", row["Static_Status"]))
    report = report_for(model, findings)
    errors = [r for r in validate_report(report, root) if r["status"] == "fail"]
    if errors:
        report["checks"] += errors
        report["status"] = "fail"
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--write-report", action="store_true",
                        help="Write actual static report and refresh requirement status CSV.")
    args = parser.parse_args()
    root = args.root.resolve()
    try:
        report = validate(root, check_trace_status=not args.write_report)
        destination = root / "examples/health-insurance/validation/static-report.json"
        if args.write_report:
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(json.dumps(report, indent=2) + "\n")
            failed = {c["check_id"] for c in report["checks"] if c["status"] == "fail"}
            if not failed.intersection({"SHAPE", "REQUIREMENTS"}):
                fields, rows = read_csv(root / "examples/health-insurance/traceability.csv")
                model = read_json(root / "examples/health-insurance/model.json")
                for row in rows:
                    requirement = next(r for r in model["requirements"] if r["id"] == row["Requirement_ID"])
                    row["Static_Status"] = "not_run" if requirement["manual"] else (
                        "fail" if failed.intersection(requirement["checks"]) else "pass")
                with (root / "examples/health-insurance/traceability.csv").open("w", newline="") as stream:
                    writer = csv.DictWriter(stream, fieldnames=fields)
                    writer.writeheader()
                    writer.writerows(rows)
        elif not destination.is_file() or read_json(destination) != report:
            report["checks"].append(finding("REPORT", "static-report.json", "fail",
                                             "Current reproducible static evidence.",
                                             "Report missing or stale; rerun with --write-report."))
            report["status"] = "fail"
    except (OSError, ValueError) as error:
        print("Validation input/output error: " + str(error), file=sys.stderr)
        return 1
    failures = [c for c in report["checks"] if c["status"] == "fail"]
    print(json.dumps({"status": report["status"], "evidence_level": report["evidence_level"],
                      "coverage": report["coverage"], "failures": failures}, indent=2))
    return 1 if report["status"] != "pass" else 0


if __name__ == "__main__":
    sys.exit(main())
