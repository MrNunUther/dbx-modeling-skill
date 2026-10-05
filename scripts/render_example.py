#!/usr/bin/env python3
"""Render only the documented canonical example; never connect to Databricks."""
import argparse
import json
from pathlib import Path


def literal(value):
    return "'" + value.replace("'", "''") + "'"


def identifier(value):
    return "`" + value + "`"


def table(path):
    return "`__CATALOG__`." + ".".join(identifier(part) for part in path.split("."))


def columns(names):
    return ", ".join(identifier(name) for name in names)


def products(model):
    return {domain["name"] + "." + product["name"]: product
            for domain in model["domains"] for product in domain["products"]}


def effective_tags(attribute):
    tags = {**attribute["tags"], "dbx_business_glossary_term": attribute["glossary"],
            "dbx_classification": attribute["classification"]}
    if attribute["references"]:
        tags["dbx_standard_references"] = "; ".join(attribute["references"])
    return tags


def render(model):
    """Return deterministic files for the supported contract, not arbitrary SQL."""
    notice = "-- Re-authored teaching artifact; see adaptation-log.csv and NOTICE.\n"
    warning = "-- NOT EXECUTED. Substitute reviewed __CATALOG__ offline before authorized use.\n"
    preamble = notice + warning
    namespace = [preamble, "CREATE CATALOG IF NOT EXISTS `__CATALOG__`;"]
    ddl = [preamble]
    fks = [preamble, "-- ADD CONSTRAINT is not rerun-idempotent; inspect existing declarations."]
    tags = [preamble]
    dbml = ["// Re-authored conceptual diagram; matched to the canonical model.",
            "Project teaching_slice {", "  database_type: 'Databricks'", "}"]
    integrity = [preamble, "-- Run only after existence/visibility checks; zero violations is not existence proof."]
    items = products(model)
    expected_tables = []
    expected_columns = []
    for domain in model["domains"]:
        name = domain["physical_schema"]
        namespace.append(f"CREATE SCHEMA IF NOT EXISTS {table(name)} COMMENT {literal(domain['description'])};")
        tags.append(f"ALTER SCHEMA {table(name)} SET TAGS ('dbx_division' = {literal(domain['division'])});")
        for product in domain["products"]:
            path = name + "." + product["physical_name"]
            expected_tables.append((name, product["physical_name"]))
            declarations = []
            diagram_columns = []
            expected_tags = {"dbx_data_type": product["classification"], "dbx_subdomain": product["subdomain"],
                             "dbx_steward": product["steward"], **product["tags"]}
            tag_sql = ", ".join(literal(k) + " = " + literal(v) for k, v in sorted(expected_tags.items()))
            tags.append(f"ALTER TABLE {table(path)} SET TAGS ({tag_sql});")
            for ordinal, attribute in enumerate(product["attributes"], 1):
                column = attribute["physical_name"]
                null = "" if attribute["nullable"] else " NOT NULL"
                declarations.append(f"  {identifier(column)} {attribute['type']}{null} COMMENT {literal(attribute['description'])}")
                diagram_options = []
                if column in product["primary_key"] and len(product["primary_key"]) == 1:
                    diagram_options.append("pk")
                if not attribute["nullable"]:
                    diagram_options.append("not null")
                options = " [" + ", ".join(diagram_options) + "]" if diagram_options else ""
                # Quoted types preserve DECIMAL parameters in DBML.
                diagram_columns.append(f'  {column} "{attribute["type"]}"{options}')
                tag_sql = ", ".join(literal(k) + " = " + literal(v) for k, v in sorted(effective_tags(attribute).items()))
                tags.append(f"ALTER TABLE {table(path)} ALTER COLUMN {identifier(column)} SET TAGS ({tag_sql});")
                expected_columns.append((name, product["physical_name"], column, ordinal,
                                         attribute["type"], "YES" if attribute["nullable"] else "NO"))
                if attribute["allowed_values"]:
                    allowed = ", ".join(literal(v) for v in attribute["allowed_values"])
                    integrity.append(f"SELECT {literal(path + '.' + column + ':enum')} AS check_id, COUNT(*) AS violations FROM {table(path)} WHERE {identifier(column)} IS NOT NULL AND {identifier(column)} NOT IN ({allowed});")
                if attribute["pattern"]:
                    integrity.append(f"SELECT {literal(path + '.' + column + ':pattern')} AS check_id, COUNT(*) AS violations FROM {table(path)} WHERE {identifier(column)} IS NOT NULL AND NOT ({identifier(column)} RLIKE {literal(attribute['pattern'])});")
            pk = product["primary_key"]
            declarations.append(f"  CONSTRAINT {identifier('pk_' + product['name'])} PRIMARY KEY ({columns(pk)})")
            ddl.append(f"CREATE TABLE IF NOT EXISTS {table(path)} (\n" + ",\n".join(declarations)
                       + f"\n) USING DELTA COMMENT {literal(product['description'])};")
            if len(pk) > 1:
                diagram_columns.extend(["  indexes {", "    (" + ", ".join(pk) + ") [pk]", "  }"])
            dbml.append("Table " + path + " {\n" + "\n".join(diagram_columns) + "\n}")
            missing = " OR ".join(identifier(c) + " IS NULL" for c in pk)
            integrity.append(f"SELECT {literal(path + ':pk_null')} AS check_id, COUNT(*) AS violations FROM {table(path)} WHERE {missing};")
            for index, key in enumerate([pk] + product["business_keys"]):
                integrity.append(f"SELECT {literal(path + ':unique_' + str(index))} AS check_id, COUNT(*) AS violating_groups FROM (SELECT {columns(key)} FROM {table(path)} GROUP BY {columns(key)} HAVING COUNT(*) > 1);")
    for relation in model["relationships"]:
        source = relation["source"]
        target = relation["target"]
        fks.append(f"ALTER TABLE {table(source)} ADD CONSTRAINT {identifier(relation['id'])} FOREIGN KEY ({columns(relation['source_columns'])}) REFERENCES {table(target)} ({columns(relation['target_columns'])});")
        dbml.append(f"Ref: {source}.({', '.join(relation['source_columns'])}) > {target}.({', '.join(relation['target_columns'])})")
        present = " AND ".join("s." + identifier(c) + " IS NOT NULL" for c in relation["source_columns"])
        join = " AND ".join("s." + identifier(s) + " = t." + identifier(t)
                            for s, t in zip(relation["source_columns"], relation["target_columns"]))
        integrity.append(f"SELECT {literal(relation['id'] + ':orphan')} AS check_id, COUNT(*) AS violations FROM {table(source)} s WHERE {present} AND NOT EXISTS (SELECT 1 FROM {table(target)} t WHERE {join});")
    for path, start, end in [
        ("plan.health_plan", "effective_from", "effective_to"),
        ("enrollment.coverage", "coverage_from", "coverage_to"),
        ("network.participation", "participation_from", "participation_to"),
    ]:
        if path in items and {start, end}.issubset({a["name"] for a in items[path]["attributes"]}):
            integrity.append(f"SELECT {literal(path + ':interval')} AS check_id, COUNT(*) AS violations FROM {table(path)} WHERE {identifier(end)} <= {identifier(start)};")
    coverage = items.get("enrollment.coverage", {})
    if {"identity_id", "health_plan_id", "coverage_id", "coverage_from", "coverage_to"}.issubset(
        {a["name"] for a in coverage.get("attributes", [])}
    ):
        integrity.append(
            f"SELECT 'coverage_overlap' AS check_id, COUNT(*) AS violations FROM {table('enrollment.coverage')} a JOIN {table('enrollment.coverage')} b ON a.identity_id = b.identity_id AND a.health_plan_id = b.health_plan_id AND a.coverage_id < b.coverage_id AND (b.coverage_to IS NULL OR a.coverage_from < b.coverage_to) AND (a.coverage_to IS NULL OR b.coverage_from < a.coverage_to);")
    metrics = {}
    for metric in model["metric_views"]:
        namespace.append(f"CREATE SCHEMA IF NOT EXISTS {table(metric['schema'])};")
        yaml = ["version: 1.1", "comment: " + json.dumps(metric["description"]),
                "source: " + json.dumps(table(metric["source"])), "fields:"]
        for dimension in metric["dimensions"]:
            yaml += ["  - name: " + dimension["name"], "    expr: " + dimension["expression"]]
        yaml.append("measures:")
        for measure in metric["measures"]:
            yaml += ["  - name: " + measure["name"], "    expr: " + measure["expression"]]
        metrics["metrics/" + metric["name"].replace("_", "-") + ".sql"] = (
            preamble + f"CREATE VIEW {table(metric['schema'] + '.' + metric['name'])}\nWITH METRICS LANGUAGE YAML AS $$\n"
            + "\n".join(yaml) + "\n$$;\n")

    table_rows = ",\n".join("  (" + ", ".join(literal(v) for v in row) + ")" for row in expected_tables)
    column_rows = ",\n".join("  (" + ", ".join(str(v) if isinstance(v, int) else literal(v) for v in row) + ")" for row in expected_columns)
    parity = preamble + """-- Expected table/column comparisons; remaining metadata queries require explicit review.
WITH expected(schema_name, table_name) AS (VALUES
""" + table_rows + """)
SELECT e.*, CASE WHEN t.table_name IS NULL THEN 'missing_or_invisible' ELSE 'present' END AS observed
FROM expected e LEFT JOIN `__CATALOG__`.information_schema.tables t
ON t.table_schema = e.schema_name AND t.table_name = e.table_name;

WITH expected(schema_name, table_name, column_name, ordinal_position, full_type, nullable) AS (VALUES
""" + column_rows + """)
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
"""
    for metric in model["metric_views"]:
        parity += "SHOW CREATE TABLE " + table(metric["schema"] + "." + metric["name"]) + ";\n"
    files = {
        "schemas/01-catalog-and-schemas.sql": "\n\n".join(namespace) + "\n",
        "schemas/02-tables.sql": "\n\n".join(ddl) + "\n",
        "schemas/03-foreign-keys.sql": "\n\n".join(fks) + "\n",
        "schemas/04-comments-and-tags.sql": "\n\n".join(tags) + "\n",
        "diagram/model.dbml": "\n\n".join(dbml) + "\n",
        "validation/data-integrity.sql": "\n\n".join(integrity) + "\n",
        "validation/catalog-parity.sql": parity,
    }
    return {**files, **metrics}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    args = parser.parse_args()
    root = args.root.resolve()
    base = root / "examples/health-insurance"
    from validate_skill import read_json, validate_model
    model = read_json(base / "model.json")
    failures = [finding for finding in validate_model(model, root) if finding["status"] == "fail"]
    if failures:
        parser.exit(1, "Invalid model: " + json.dumps(failures, indent=2) + "\n")
    failed = False
    for relative, text in render(model).items():
        path = base / relative
        if args.write:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text)
        elif not path.is_file() or path.read_text() != text:
            print("Artifact drift:", relative)
            failed = True
    parser.exit(1 if failed else 0, "Example artifacts " + ("written" if args.write else "checked") + ".\n")


if __name__ == "__main__":
    main()
