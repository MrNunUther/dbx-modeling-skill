#!/usr/bin/env python3
"""Profile model shape, derive a corpus shape envelope, and check conformance offline.

Commands:
  profile MODEL [MODEL ...]                 Print scale-free shape fingerprints.
  build-envelope --corpus DIR --out FILE    Derive per-scope bands from agent outputs.
  check MODEL --envelope FILE --scope mvm   Score topology, product shape, and a composite.
  targets --envelope FILE --scope mvm       Emit skeleton-first synthesis quotas.
  advise MODEL|DDL.sql --envelope FILE      Per-table guidance toward common shapes.

Reads Vibe Modelling Agent exports (``model.domains[].products[]`` with
``foreign_key_to``), this skill's canonical contract (``relationships``), and
bounded CREATE TABLE DDL (``.sql``). No Databricks connection is used.
"""
import argparse
import collections
import json
import math
from pathlib import Path
import re
import statistics
import sys

DATA_TYPES = ("master_data", "transactional_data", "reference_data", "association_data")
FAMILIES = [
    ("audit", r"^(created|updated|modified|last_modified|last_updated|deleted)_(timestamp|at|by|date)$|^version_number$"),
    ("classifier", r"(_type|_category|_class|_tier|_level|_method|_source|_channel|_mode)(_code)?$"),
    ("identifier", r"(_number|_code|_npi|_ndc|_identifier|_reference)$"),
    ("status", r"(_status|_reason|_reason_code)$|^status$"),
    ("temporal", r"(_date|_year|_month|_timestamp|_at)$"),
    ("amount", r"(_amount|_cost|_price|_fee|_premium|_balance|_total|_charge)$"),
    ("measure", r"(_count|_rate|_pct|_percent|_percentage|_ratio|_score|_factor|_days|_units|_quantity|_hours|_minutes)$"),
    ("flag", r"^(is|has|can|should)_|(_flag|_indicator|_required|_eligible)$"),
    ("text", r"(_name|_description|_notes|_text|_comments)$|^(notes|description|name)$"),
]
TYPE_FAMILY = {"BOOLEAN": "flag", "DATE": "temporal", "TIMESTAMP": "temporal", "DECIMAL": "amount"}
HIERARCHY_ROLES = ("parent_", "prior_", "previous_", "original_", "superseded_", "successor_", "predecessor_")
# Scale metrics depend on scope and tier; ratios/shares are expected to transfer across industries.
SCALE_METRICS = {"domains", "products", "attributes", "fks", "metric_views", "dag_depth_max"}
# Documented ideals: the corpus is evidence of style, but documented principles win where they conflict.
# A value between the observed band and its ideal is treated as in band, never penalized.
IDEALS = {"pk_first_share": 1.0, "fk_front_share": 1.0, "fk_name_ends_with_target_pk": 1.0,
          "cycle_back_edges": 0.0, "siloed_product_share": 0.0, "unresolved_fk_share": 0.0,
          "subdomain_two_word_share": 1.0, "audit_column_product_share": 1.0}


def _norm_type(value):
    return re.sub(r"\(.*", "", str(value or "")).strip().upper()


def _norm_data_type(value):
    value = str(value or "").strip().lower()
    for item in DATA_TYPES:
        if value == item or value == item.split("_")[0] or (value == "associative" and item == "association_data"):
            return item
    return value or "unspecified"


def normalize(raw):
    """Return a format-neutral IR: domains, products, edges, metric view count."""
    if "relationships" in raw and "domains" in raw:
        return _from_canonical(raw)
    model = raw.get("model", raw)
    if "domains" not in model:
        raise ValueError("Unrecognized model: expected domains")
    return _from_agent(model)


def _subdomain_names(domain):
    names = [s.get("name", "") if isinstance(s, dict) else str(s) for s in domain.get("subdomains") or []]
    if not names:
        names = sorted({str(p.get("subdomain")) for p in domain.get("products") or [] if p.get("subdomain")})
    return [n for n in names if n]


def _from_agent(model):
    domains, products, edges = [], {}, []
    for domain in model["domains"]:
        domains.append(dict(name=domain["name"], division=str(domain.get("division", "")).lower(),
                            subdomains=_subdomain_names(domain),
                            description=domain.get("description", "")))
        for product in domain.get("products") or []:
            key = f"{domain['name']}.{product['name']}"
            attrs = []
            for attr in product.get("attributes") or []:
                target = str(attr.get("foreign_key_to") or "")
                tags = {t.strip().lower() for t in str(attr.get("tags") or "").split(",") if t.strip()}
                attrs.append(dict(name=attr["name"], type=_norm_type(attr.get("type")),
                                  fk=".".join(target.split(".")[:2]) if target else None,
                                  tags=tags, regex=bool(attr.get("value_regex")),
                                  description=attr.get("description", "")))
            pk = product.get("primary_key") or ""
            products[key] = dict(domain=domain["name"], name=product["name"],
                                 data_type=_norm_data_type(product.get("data_type") or product.get("type")),
                                 pk=[pk] if isinstance(pk, str) else list(pk), attrs=attrs,
                                 description=product.get("description", ""),
                                 type_label=str(product.get("type", "")))
    for key, product in products.items():
        for attr in product["attrs"]:
            if attr["fk"]:
                edges.append((key, attr["fk"], attr["name"]))
    return dict(domains=domains, products=products, edges=edges,
                metric_views=len(model.get("metric_views") or []))


def _from_canonical(model):
    domains, products = [], {}
    fk_cols = collections.defaultdict(dict)
    for rel in model.get("relationships") or []:
        for col in rel.get("source_columns") or []:
            fk_cols[rel["source"]][col] = rel["target"]
    for domain in model["domains"]:
        domains.append(dict(name=domain["name"], division=str(domain.get("division", "")).lower(),
                            subdomains=_subdomain_names(domain),
                            description=domain.get("description", "")))
        for product in domain.get("products") or []:
            key = f"{domain['name']}.{product['name']}"
            attrs = []
            for attr in product.get("attributes") or []:
                tags = {str(k).lower() for k in (attr.get("tags") or {})}
                if attr.get("sensitivity") not in (None, "", "none", "public", "internal"):
                    tags.add(str(attr["sensitivity"]).lower())
                attrs.append(dict(name=attr["name"], type=_norm_type(attr.get("type")),
                                  fk=fk_cols[key].get(attr["name"]), tags=tags,
                                  regex=bool(attr.get("pattern")), description=attr.get("description", "")))
            products[key] = dict(domain=domain["name"], name=product["name"],
                                 data_type=_norm_data_type(product.get("classification")),
                                 pk=list(product.get("primary_key") or []), attrs=attrs,
                                 description=product.get("description", ""),
                                 type_label=str(product.get("classification", "")))
    edges = [(rel["source"], rel["target"], col) for rel in model.get("relationships") or []
             for col in rel.get("source_columns") or []]
    return dict(domains=domains, products=products, edges=edges,
                metric_views=len(model.get("metric_views") or []))


def family(product, attr):
    if attr["name"] in product["pk"]:
        return "pk"
    if attr["fk"]:
        return "fk"
    for name, pattern in FAMILIES:
        if re.search(pattern, attr["name"]):
            return name
    return TYPE_FAMILY.get(attr["type"], "other")


def _q(values, fraction):
    values = sorted(values)
    if not values:
        return 0.0
    index = (len(values) - 1) * fraction
    low = int(index)
    high = min(low + 1, len(values) - 1)
    return values[low] + (values[high] - values[low]) * (index - low)


def _share(count, total):
    return round(count / total, 4) if total else 0.0


def _depths(products, edges):
    graph = collections.defaultdict(set)
    for src, tgt, _ in edges:
        if src != tgt and tgt in products:
            graph[src].add(tgt)
    memo, active, back_edges = {}, set(), 0

    def depth(node):
        nonlocal back_edges
        if node in memo:
            return memo[node]
        active.add(node)
        best = 0
        for nxt in graph[node]:
            if nxt in active:
                back_edges += 1
                continue
            best = max(best, depth(nxt))
        active.discard(node)
        memo[node] = best + 1
        return memo[node]

    limit = sys.getrecursionlimit()
    sys.setrecursionlimit(max(limit, 10000))
    try:
        values = [depth(key) for key in products]
    finally:
        sys.setrecursionlimit(limit)
    return values, back_edges


def _archetypes(product):
    names = [a["name"] for a in product["attrs"]]
    joined = " ".join(names)
    self_key = f"{product['domain']}.{product['name']}"
    return dict(
        span=bool(re.search(r"\b(effective|start|begin)\w*", joined) and
                  re.search(r"\b(termination|end|expiration|effective_end|effective_until)\w*", joined)),
        stateful_event=product["data_type"] == "transactional_data" and any(n.endswith("_status") or n == "status" for n in names),
        versioned=any(re.search(r"version|superseded|^prior_|^previous_", n) for n in names),
        hierarchy=any(a["fk"] == self_key for a in product["attrs"]),
        line=bool(re.search(r"(^|_)line$", product["name"])),
    )


def profile(ir):
    products, edges, domains = ir["products"], ir["edges"], ir["domains"]
    n_products = len(products)
    attrs = [(p, a) for p in products.values() for a in p["attrs"]]
    n_attrs = len(attrs)
    resolved = [e for e in edges if e[1] in products]
    self_edges = [e for e in resolved if e[0] == e[1]]
    cross = [e for e in resolved if products[e[0]]["domain"] != products[e[1]]["domain"]]
    out_deg = collections.Counter(e[0] for e in resolved if e[0] != e[1])
    in_deg = collections.Counter(e[1] for e in resolved if e[0] != e[1])
    linked = {e[0] for e in resolved} | {e[1] for e in resolved}
    depths, back_edges = _depths(products, resolved)
    inbound = sorted((in_deg[k] for k in products), reverse=True)
    top = max(1, round(n_products * 0.1))
    domain_names = [d["name"] for d in domains]
    pairs = {frozenset((products[s]["domain"], products[t]["domain"])) for s, t, _ in cross}
    possible_pairs = len(domain_names) * (len(domain_names) - 1) // 2
    polarity = []
    for name in domain_names:
        d_in = sum(1 for s, t, _ in cross if products[t]["domain"] == name)
        d_out = sum(1 for s, t, _ in cross if products[s]["domain"] == name)
        if d_in + d_out:
            polarity.append((d_in - d_out) / (d_in + d_out))
    n_temporal = sum(1 for p in products.values() for a in p["attrs"] if a["type"] in ("DATE", "TIMESTAMP"))
    data_types = collections.Counter(p["data_type"] for p in products.values())
    divisions = collections.Counter(d["division"] for d in domains)
    families = collections.Counter(family(p, a) for p, a in attrs)
    types = collections.Counter(a["type"] for _, a in attrs)
    arche = collections.Counter(k for p in products.values() for k, v in _archetypes(p).items() if v)
    per_type_out = {dt: statistics.mean([out_deg[k] for k, p in products.items() if p["data_type"] == dt] or [0])
                    for dt in ("master_data", "transactional_data")}
    per_type_in = {dt: statistics.mean([in_deg[k] for k, p in products.items() if p["data_type"] == dt] or [0])
                   for dt in ("master_data", "transactional_data")}
    attr_counts = [len(p["attrs"]) for p in products.values()] or [0]
    pk_first = sum(1 for p in products.values() if p["attrs"] and p["attrs"][0]["name"] in p["pk"])
    fk_front = 0
    for p in products.values():
        positions = [i for i, a in enumerate(p["attrs"]) if a["fk"] and a["name"] not in p["pk"]]
        if positions and max(positions) <= len(p["pk"]) + len(positions) + 1:
            fk_front += 1
    fk_products = sum(1 for p in products.values() if any(a["fk"] and a["name"] not in p["pk"] for a in p["attrs"]))
    fk_named = sum(1 for s, t, col in resolved if any(col.endswith(pk) for pk in products[t]["pk"]))
    audit_products = sum(1 for p in products.values() if any(re.match(r"^(created|updated|last_updated)_", a["name"]) for a in p["attrs"]))
    sensitive = sum(1 for _, a in attrs if a["tags"] & {"restricted", "confidential", "personal", "health", "financial"}
                    or any(t.startswith("pii") for t in a["tags"]))
    subdomain_counts = [len(d["subdomains"]) for d in domains] or [0]
    sub_names = [s for d in domains for s in d["subdomains"]]
    metrics = {
        "domains": len(domains), "products": n_products, "attributes": n_attrs, "fks": len(resolved),
        "metric_views": ir["metric_views"],
        "products_per_domain_median": statistics.median([sum(1 for p in products.values() if p["domain"] == d) for d in domain_names] or [0]),
        "attrs_per_product_p25": round(_q(attr_counts, 0.25), 2),
        "attrs_per_product_median": statistics.median(attr_counts),
        "attrs_per_product_p75": round(_q(attr_counts, 0.75), 2),
        "division_operations": _share(divisions["operations"], len(domains)),
        "division_business": _share(divisions["business"], len(domains)),
        "division_corporate": _share(divisions["corporate"], len(domains)),
        **{f"type_{dt.split('_')[0]}": _share(data_types[dt], n_products) for dt in DATA_TYPES},
        "fk_per_product": round(len(resolved) / n_products, 3) if n_products else 0.0,
        "fk_attribute_share": _share(families["fk"], n_attrs),
        "cross_domain_fk_share": _share(len(cross), len(resolved)),
        "self_ref_share": _share(len(self_edges), len(resolved)),
        "cycle_back_edges": back_edges,
        "siloed_product_share": _share(sum(1 for k in products if k not in linked), n_products),
        "unresolved_fk_share": _share(len(edges) - len(resolved), len(edges)),
        "dag_depth_max": max(depths or [0]),
        "dag_depth_median_rel": round(statistics.median(depths or [0]) / max(1, max(depths or [1])), 3),
        "hub_inbound_top10pct_share": _share(sum(inbound[:top]), sum(inbound)),
        "domain_pair_coverage": _share(len(pairs), possible_pairs),
        "domain_polarity_spread": round(statistics.pstdev(polarity), 3) if len(polarity) > 1 else 0.0,
        "domain_producer_share": _share(sum(1 for v in polarity if v > 0.3), len(polarity)),
        "domain_consumer_share": _share(sum(1 for v in polarity if v < -0.3), len(polarity)),
        "out_degree_transactional": round(per_type_out["transactional_data"], 2),
        "out_degree_master": round(per_type_out["master_data"], 2),
        "in_degree_master": round(per_type_in["master_data"], 2),
        "in_degree_transactional": round(per_type_in["transactional_data"], 2),
        **{f"family_{name}": _share(families[name], n_attrs) for name in
           ("temporal", "flag", "identifier", "classifier", "amount", "status", "text", "measure", "audit", "other")},
        **{f"sqltype_{name.lower()}": _share(types[name], n_attrs) for name in
           ("STRING", "BIGINT", "INT", "DATE", "TIMESTAMP", "BOOLEAN", "DECIMAL")},
        "temporal_date_share": _share(types["DATE"], n_temporal),
        "pk_first_share": _share(pk_first, n_products),
        "fk_front_share": _share(fk_front, fk_products),
        "fk_name_ends_with_target_pk": _share(fk_named, len(resolved)),
        "audit_column_product_share": _share(audit_products, n_products),
        "value_pattern_share": _share(sum(1 for _, a in attrs if a["regex"]), n_attrs),
        "sensitive_tag_share": _share(sensitive, n_attrs),
        **{f"archetype_{name}": _share(arche[name], n_products) for name in
           ("span", "stateful_event", "versioned", "hierarchy", "line")},
        "subdomains_per_domain_median": statistics.median(subdomain_counts),
        "subdomain_two_word_share": _share(sum(1 for s in sub_names if len(re.split(r"[_\s]+", s.strip())) == 2), len(sub_names)),
        "metric_views_per_product": round(ir["metric_views"] / n_products, 3) if n_products else 0.0,
        "product_description_chars_median": statistics.median([len(p["description"]) for p in products.values()] or [0]),
        "attribute_description_chars_median": statistics.median([len(a["description"]) for _, a in attrs] or [0]),
    }
    return metrics


def defects(ir):
    """Agent-output patterns that contradict documented principles; never imitate these."""
    products = ir["products"]
    fk_attrs = [(p, a) for p in products.values() for a in p["attrs"] if a["fk"]]
    pii_fk = sum(1 for _, a in fk_attrs if any(t.startswith("pii") for t in a["tags"]))
    domain_prefixed = sum(1 for p, a in fk_attrs if a["fk"] in products and
                          a["name"].startswith(products[a["fk"]]["domain"] + "_" + products[a["fk"]]["name"]))
    labels = collections.Counter(p["type_label"] for p in products.values() if p["type_label"])
    canonical_labels = {"Master", "Transactional", "Reference", "Association", *DATA_TYPES}
    templated_pk = sum(1 for p in products.values() for a in p["attrs"]
                       if a["name"] in p["pk"] and re.fullmatch(r"(?i)primary key for \w+\.?", a["description"].strip()))
    return {
        "pii_tag_on_fk_share": _share(pii_fk, len(fk_attrs)),
        "domain_prefixed_fk_name_share": _share(domain_prefixed, len(fk_attrs)),
        "noncanonical_type_label_share": _share(sum(v for k, v in labels.items() if k not in canonical_labels), len(products)),
        "templated_pk_description_share": _share(templated_pk, len(products)),
    }


def load(path):
    path = Path(path)
    text = path.read_text()
    if path.suffix.lower() == ".sql":
        return normalize(parse_ddl(text))
    return normalize(json.loads(text))


_COLUMN = re.compile(r"^`?(?P<name>[A-Za-z_][\w]*)`?\s+(?P<type>[A-Za-z]+(?:\s*\([^)]*\))?(?:<[^>]*>)?)(?P<rest>.*)$", re.S)
_TABLE = re.compile(r"CREATE\s+(?:OR\s+REPLACE\s+)?TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?(?P<name>[`\w.]+)\s*\(", re.I)
_PK = re.compile(r"PRIMARY\s+KEY\s*\((?P<cols>[^)]*)\)", re.I)
_FK = re.compile(r"FOREIGN\s+KEY\s*\((?P<cols>[^)]*)\)\s*REFERENCES\s+(?P<target>[`\w.]+)\s*\((?P<tcols>[^)]*)\)", re.I)
_ALTER_FK = re.compile(r"ALTER\s+TABLE\s+(?P<table>[`\w.]+)\s+ADD\s+(?:CONSTRAINT\s+\w+\s+)?" + _FK.pattern, re.I)
_COMMENT = re.compile(r"COMMENT\s+'((?:[^']|'')*)'", re.I)


def _ident(value):
    return [part for part in value.replace("`", "").split(".") if part]


def _split_top(body):
    parts, depth, current, quoted = [], 0, [], False
    for char in body:
        if char == "'":
            quoted = not quoted
        elif not quoted and char in "(<":
            depth += 1
        elif not quoted and char in ")>":
            depth -= 1
        if char == "," and depth == 0 and not quoted:
            parts.append("".join(current).strip())
            current = []
        else:
            current.append(char)
    if "".join(current).strip():
        parts.append("".join(current).strip())
    return parts


def parse_ddl(text):
    """Parse bounded Databricks CREATE TABLE DDL into the agent export shape.

    Supports column lists, inline/table PRIMARY KEY and FOREIGN KEY constraints,
    ALTER TABLE ... ADD FOREIGN KEY, NOT NULL, and COMMENT. Schema maps to domain;
    tables without a schema use ``default``. Data type is left unspecified for inference.
    """
    text = re.sub(r"--[^\n]*", "", text)
    domains = collections.OrderedDict()
    fks = []
    for match in _TABLE.finditer(text):
        depth, index = 1, match.end()
        while depth and index < len(text):
            depth += {"(": 1, ")": -1}.get(text[index], 0)
            index += 1
        body = text[match.end():index - 1]
        parts = _ident(match.group("name"))
        schema, table = (parts[-2] if len(parts) > 1 else "default"), parts[-1]
        tail = text[index:index + 400].split(";")[0]
        comment = _COMMENT.search(tail)
        attrs, pk = [], []
        for item in _split_top(body):
            if re.match(r"(CONSTRAINT\s+\w+\s+)?PRIMARY\s+KEY", item, re.I):
                pk = [c.strip(" `") for c in _PK.search(item).group("cols").split(",")]
                continue
            fk = _FK.search(item)
            if re.match(r"(CONSTRAINT\s+\w+\s+)?FOREIGN\s+KEY", item, re.I) and fk:
                fks.append((schema, table, fk))
                continue
            column = _COLUMN.match(item)
            if not column:
                raise ValueError(f"Unsupported DDL element in {table}: {item[:60]}")
            rest = column.group("rest")
            if re.search(r"\bPRIMARY\s+KEY\b", rest, re.I):
                pk = [column.group("name")]
            note = _COMMENT.search(rest)
            attrs.append(dict(name=column.group("name"), type=column.group("type").upper(), foreign_key_to=None,
                              tags="", value_regex=None, description=note.group(1) if note else ""))
            inline = re.search(r"REFERENCES\s+([`\w.]+)\s*\(([^)]*)\)", rest, re.I)
            if inline:
                target = _ident(inline.group(1))
                attrs[-1]["foreign_key_to"] = ".".join([target[-2] if len(target) > 1 else "default", target[-1],
                                                        inline.group(2).strip(" `")])
        domains.setdefault(schema, []).append(dict(name=table, primary_key=pk[0] if len(pk) == 1 else pk,
                                                   description=comment.group(1) if comment else "",
                                                   attributes=attrs))
    for match in _ALTER_FK.finditer(text):
        parts = _ident(match.group("table"))
        fks.append((parts[-2] if len(parts) > 1 else "default", parts[-1], match))
    for schema, table, fk in fks:
        product = next((p for p in domains.get(schema, []) if p["name"] == table), None)
        target = _ident(fk.group("target"))
        target_domain = target[-2] if len(target) > 1 else "default"
        for col, tcol in zip(fk.group("cols").split(","), fk.group("tcols").split(",")):
            for attr in (product or {}).get("attributes", []):
                if attr["name"] == col.strip(" `"):
                    attr["foreign_key_to"] = f"{target_domain}.{target[-1]}.{tcol.strip(' `')}"
    if not domains:
        raise ValueError("No CREATE TABLE statements found")
    return {"model": {"domains": [dict(name=name, products=products) for name, products in domains.items()]}}


PRODUCT_FAMILIES = ("temporal", "flag", "identifier", "classifier", "amount", "status", "text", "measure", "audit", "other")
# Numbered columns the agent corpus treats as normal (address lines, admin levels); matched on the '#' stem.
ACCEPTED_SERIES = re.compile(r"(^|_)(address_line|admin_level|street_line|line|admin)#(_name|_code)?$")
GENERIC_COLUMNS = re.compile(r"(value|data|misc|other|info|details?|field\d*|col\d*|column\d*|attr\d*|"
                             r"attribute\d*|extra|payload|blob|json|raw|custom\d*|udf\d*)")
DESCRIPTIVE_SUFFIX = re.compile(r"_(name|email|phone|address|address_line_\d|city|state|postal_code|zip|country|"
                                r"type|status|description|title|dob|birth_date|gender)$")
AUDIT_NAME = re.compile(r"^(created|updated|modified|last_modified|last_updated)_(timestamp|at|by|date)$")
ADDRESS_PARTS = {"address", "city", "state", "postal_code", "zip", "country"} | {f"address_line_{n}" for n in range(1, 10)}
IDENTITY_PARTS = {"name", "email", "phone", "dob", "birth_date", "gender"}


def _class_features(product):
    """Generic name-token and structure features for classification (no industry nouns survive training)."""
    feats = {"p:" + t for t in product["name"].split("_")} | {"plast:" + product["name"].split("_")[-1]}
    attrs = product["attrs"]
    fks = [a for a in attrs if a["fk"] and a["name"] not in product["pk"]]
    for a in attrs:
        if a["name"] in product["pk"] or a["fk"]:
            continue
        tokens = a["name"].split("_")
        feats.add("c:" + tokens[-1])
        if len(tokens) > 1:
            feats.add("c2:" + "_".join(tokens[-2:]))
        feats.add("t:" + _norm_type(a["type"]))
    feats.add(f"nfk:{min(len(fks), 6)}")
    return feats


def train_classifier(irs, min_industries=8):
    """Bernoulli naive Bayes over features seen in at least ``min_industries`` industries."""
    seen = collections.defaultdict(set)
    rows = []
    for industry, ir in irs.items():
        for product in ir["products"].values():
            if product["data_type"] in DATA_TYPES:
                feats = _class_features(product)
                rows.append((product["data_type"], feats))
                for f in feats:
                    seen[f].add(industry)
    vocab = sorted(f for f, inds in seen.items() if len(inds) >= min_industries)
    index = {f: i for i, f in enumerate(vocab)}
    totals = [0] * len(DATA_TYPES)
    counts = [[0] * len(DATA_TYPES) for _ in vocab]
    for label, feats in rows:
        c = DATA_TYPES.index(label)
        totals[c] += 1
        for f in feats:
            if f in index:
                counts[index[f]][c] += 1
    return dict(method="bernoulli_naive_bayes", min_industries=min_industries, classes=list(DATA_TYPES),
                totals=totals, features=vocab, counts=counts)


_CLASSIFIER_CACHE = {}


def _classifier_tables(classifier):
    key = id(classifier)
    if key not in _CLASSIFIER_CACHE or _CLASSIFIER_CACHE[key][0] is not classifier:
        totals, k = classifier["totals"], len(classifier["classes"])
        n = sum(totals)
        base = [math.log((totals[c] + 1) / (n + k)) for c in range(k)]
        delta = {}
        for feature, row in zip(classifier["features"], classifier["counts"]):
            probs = [(row[c] + 1) / (totals[c] + 2) for c in range(k)]
            for c in range(k):
                base[c] += math.log(1 - probs[c])
            delta[feature] = [math.log(probs[c]) - math.log(1 - probs[c]) for c in range(k)]
        _CLASSIFIER_CACHE[key] = (classifier, base, delta)
    return _CLASSIFIER_CACHE[key][1:]


def classify(product, classifier):
    base, delta = _classifier_tables(classifier)
    scores = list(base)
    for feature in _class_features(product):
        for c, value in enumerate(delta.get(feature, ())):
            scores[c] += value
    classes = classifier["classes"]
    fks = sum(1 for a in product["attrs"] if a["fk"] and a["name"] not in product["pk"])
    if fks < 2 and "association_data" in classes:  # 99% of corpus associations carry two or more references
        scores[classes.index("association_data")] = float("-inf")
    return classes[max(range(len(scores)), key=scores.__getitem__)]


def infer_data_type(product, products=None, _seen=None, classifier=None):
    """Guess when no classification is declared; always reported as inferred.

    Uses the corpus-trained classifier when available, otherwise structural heuristics.
    """
    if classifier:
        return classify(product, classifier)
    names = [a["name"] for a in product["attrs"]]
    fks = [a for a in product["attrs"] if a["fk"] and a["name"] not in product["pk"]]
    business = [a for a in product["attrs"] if not a["fk"] and a["name"] not in product["pk"]
                and not AUDIT_NAME.match(a["name"])]
    event_time = any(re.search(r"_(date|timestamp|at)$", n) and not AUDIT_NAME.match(n) and
                     not re.search(r"effective|termination|expiration|birth", n) for n in names)
    status = any(n.endswith("_status") or n == "status" for n in names)
    if len(fks) >= 2 and len(business) <= 4:
        return "association_data"
    if len(product["attrs"]) <= 8 and any(re.search(r"(_code|_name|_description)$", n) for n in names) and not fks:
        return "reference_data"
    if (status and event_time) or (event_time and len(fks) >= 3) or re.search(r"(^|_)line$", product["name"]):
        return "transactional_data"
    # A dependent child named after a transactional parent (claim -> claim_diagnosis) shares its lifecycle.
    seen = (_seen or set()) | {product["name"]}
    for a in fks:
        parent = (products or {}).get(a["fk"])
        if parent and parent["name"] not in seen and product["name"].startswith(parent["name"] + "_"):
            parent_type = parent["data_type"] if parent["data_type"] in DATA_TYPES else \
                infer_data_type(parent, products, seen)
            if parent_type == "transactional_data":
                return "transactional_data"
    return "master_data"


def product_metrics(product):
    attrs = product["attrs"]
    n = len(attrs)
    families = collections.Counter(family(product, a) for a in attrs)
    return {
        "attributes": n,
        "fk_out": sum(1 for a in attrs if a["fk"] and a["name"] not in product["pk"]),
        "business_attributes": sum(1 for a in attrs if family(product, a) not in ("pk", "fk", "audit")),
        **{f"family_{name}": _share(families[name], n) for name in PRODUCT_FAMILIES},
        "value_pattern_share": _share(sum(1 for a in attrs if a["regex"]), n),
        "has_audit": int(any(AUDIT_NAME.match(a["name"]) for a in attrs)),
    }


def _finding(code, severity, message, remedy, evidence=None):
    return dict(code=code, severity=severity, message=message, remedy=remedy, evidence=evidence)


def product_smells(ir, key):
    """Structural anti-patterns for one product, each with a remedy toward the common shape."""
    products = ir["products"]
    product = products[key]
    attrs, pk = product["attrs"], product["pk"]
    names = [a["name"] for a in attrs]
    out = []
    if not pk:
        out.append(_finding("SHP-PK-01", "warn", "No declared primary key.",
                            f"Declare one surrogate key `{product['name']}_id BIGINT NOT NULL` and keep business keys as attributes."))
    elif names and names[0] not in pk:
        out.append(_finding("SHP-PK-02", "warn", "Primary key is not the first column.",
                            "Move the key to position 1 (body plan: key, foreign keys, business, audit).", names[0]))
    pk_types = {a["type"] for a in attrs if a["name"] in pk}
    if pk and pk_types and pk_types != {"BIGINT"}:
        out.append(_finding("SHP-PK-03", "advise", "Primary key is not BIGINT.",
                            "Agent products use BIGINT surrogate keys; keep natural/source keys as separate attributes.",
                            sorted(pk_types)))
    fk_pos = [i for i, a in enumerate(attrs) if a["fk"] and a["name"] not in pk]
    if fk_pos and max(fk_pos) > len(pk) + len(fk_pos) + 1:
        out.append(_finding("SHP-FK-01", "warn", "Foreign keys are scattered among business columns.",
                            "Cluster foreign keys immediately after the primary key.",
                            [attrs[i]["name"] for i in fk_pos]))
    for a in attrs:
        if not a["fk"] or a["name"] in pk:
            continue
        target = products.get(a["fk"])
        target_pk = target["pk"] if target else []
        if target_pk and not any(a["name"].endswith(t) for t in target_pk):
            out.append(_finding("SHP-FK-02", "advise", f"`{a['name']}` does not end with the target key.",
                                f"Prefer `<role_>{target_pk[0]}` so the target is recognizable.", a["fk"]))
        if target and a["name"].startswith(f"{target['domain']}_{target['name']}") and target["domain"] != target["name"]:
            out.append(_finding("SHP-FK-03", "warn", f"`{a['name']}` repeats the target domain prefix.",
                                f"Use `{target_pk[0] if target_pk else 'target_id'}` or a business role prefix.", a["fk"]))
        if any(t.startswith("pii") for t in a["tags"]):
            out.append(_finding("SHP-FK-05", "warn", f"Foreign key `{a['name']}` is tagged PII.",
                                "Tag the attributes that hold personal data, not surrogate keys.", sorted(a["tags"])))
    stems = collections.defaultdict(list)
    for name in names:
        stem = re.sub(r"(?<=[a-z])\d+(?=_|$)|_\d+(?=_|$)", "#", name)
        base = stem.split("#")[0].rstrip("_")
        if "#" in stem and base and not ACCEPTED_SERIES.search(stem):
            stems[base].append(name)
    for stem, cols in stems.items():
        ordinals = sorted({int(n) for c in cols for n in re.findall(r"\d+", c[len(stem):])[:1]})
        # Ordinal series (1..N) only; standards codes such as iso_9001 or 30/60/90-day buckets are named measures.
        if len(ordinals) >= 2 and ordinals == list(range(1, len(ordinals) + 1)):
            out.append(_finding("SHP-COL-01", "warn", f"Repeating group `{stem}_N`.",
                                f"Move `{stem}` values to a child product (one row per occurrence) keyed to this product.", cols))
    if any(re.search(r"(^|_)(attribute|field|property|key)_?name$", n) for n in names) and \
            any(re.search(r"(^|_)(attribute|field|property)?_?value$", n) for n in names):
        out.append(_finding("SHP-COL-02", "warn", "Entity-attribute-value pair.",
                            "Model known characteristics as typed attributes; use a reference + association product for open sets."))
    generic = [n for n in names if GENERIC_COLUMNS.fullmatch(n) or n.endswith("_json")]
    if generic:
        out.append(_finding("SHP-COL-03", "warn", "Generic or opaque columns.",
                            "Replace with named, typed business attributes; keep raw payloads in a source layer.", generic))
    fk_prefixes = {a["name"].rsplit("_id", 1)[0] for a in attrs if a["fk"]}
    product_names = {p["name"] for p in products.values()} - {product["name"]}
    own_tokens = set(product["name"].split("_"))
    clusters = collections.defaultdict(list)
    for a in attrs:
        if a["fk"] or a["name"] in pk or not DESCRIPTIVE_SUFFIX.search(a["name"]):
            continue
        prefix = DESCRIPTIVE_SUFFIX.sub("", a["name"])
        if prefix and not set(prefix.split("_")) <= own_tokens and prefix not in fk_prefixes:
            clusters[prefix].append(a["name"])
    for prefix, cols in clusters.items():
        suffixes = {DESCRIPTIVE_SUFFIX.search(c).group(1) for c in cols}
        if len(cols) < 3 or suffixes <= ADDRESS_PARTS:
            continue
        known = prefix in product_names
        identity = bool(suffixes & IDENTITY_PARTS)
        if known or identity:
            out.append(_finding("SHP-COL-04", "warn" if known or len(cols) >= 4 else "advise",
                                f"Embedded `{prefix}` entity ({len(cols)} descriptive columns).",
                                f"Extract or reuse a `{prefix}` master product and reference it with `{prefix}_id`.", cols))
    for a in attrs:
        name, sql_type = a["name"], a["type"]
        if re.search(r"_(amount|price|cost|fee|premium|balance|charge|total)$", name) and sql_type not in ("DECIMAL",):
            out.append(_finding("SHP-TYPE-01", "warn", f"`{name}` is {sql_type}.", "Use DECIMAL(18,2) for money.", name))
        elif re.search(r"^(is|has)_|_flag$", name) and sql_type != "BOOLEAN":
            out.append(_finding("SHP-TYPE-02", "warn", f"`{name}` is {sql_type}.", "Use BOOLEAN for flags.", name))
        elif re.search(r"_(date|timestamp|at)$", name) and sql_type in ("STRING", "INT", "BIGINT"):
            out.append(_finding("SHP-TYPE-03", "warn", f"`{name}` is {sql_type}.", "Use DATE or TIMESTAMP.", name))
    audit_idx = [i for i, n in enumerate(names) if AUDIT_NAME.match(n)]
    if not audit_idx:
        out.append(_finding("SHP-AUD-01", "advise", "No audit columns.",
                            "Add `created_timestamp` and `updated_timestamp` (conventionally the last columns)."))
    joined = " ".join(names)
    if re.search(r"\beffective\w*", joined) and not re.search(r"(termination|end|expiration|until)\w*", joined):
        out.append(_finding("SHP-SPAN-01", "advise", "Effective date without an end of span.",
                            "Add `termination_date` (or `expiration_date`) so the span is closed."))
    dependent = any(a["fk"] in products and product["name"].startswith(products[a["fk"]]["name"] + "_")
                    for a in attrs if a["fk"] and a["fk"] != key)
    if product["data_type"] == "transactional_data" and not dependent and \
            not any(n.endswith("_status") or n == "status" for n in names):
        out.append(_finding("SHP-EVT-01", "advise", "Transactional product without a lifecycle status.",
                            "Add `<event>_status` and the date/timestamp of each state that matters."))
    return out


def product_bands(irs):
    """Per-data-type product bands pooled across industries, plus smell prevalence."""
    pooled = collections.defaultdict(lambda: collections.defaultdict(list))
    smell_hits, total = collections.Counter(), 0
    for ir in irs.values():
        for key, product in ir["products"].items():
            dt = product["data_type"] if product["data_type"] in DATA_TYPES else infer_data_type(product, ir["products"])
            for name, value in product_metrics(product).items():
                pooled[dt][name].append(value)
            total += 1
            smell_hits.update({f["code"] for f in product_smells(ir, key)})
    bands = {}
    for dt, metrics in pooled.items():
        bands[dt] = dict(count=len(metrics["attributes"]), metrics={
            name: dict(p02=round(_q(v, 0.02), 4), p10=round(_q(v, 0.10), 4), median=round(_q(v, 0.5), 4),
                       p90=round(_q(v, 0.90), 4), p98=round(_q(v, 0.98), 4))
            for name, v in metrics.items()})
    return dict(by_data_type=bands, smell_prevalence={k: round(v / total, 4) for k, v in sorted(smell_hits.items())},
                products=total)


BAND_ADVICE = {  # metric: (label, remedy when above band, remedy when below band)
    "attributes": ("Column count", "Check for mixed grain or embedded entities; split by grain or subdomain.",
                   "Enrich with real business attributes the process needs; never pad to reach a count."),
    "fk_out": ("Outbound references", "Check whether the product mixes grains or should reference an intermediate product.",
               "Reference the parties, products, locations, and classifications this row depends on instead of copying them."),
    "family_temporal": ("Temporal share", "Confirm each date marks a distinct business event.",
                        "Capture the date or timestamp of each business event and span."),
    "family_flag": ("Flag share", "Consider a status or classifier instead of many flags.",
                    "Express binary business facts as BOOLEAN `is_`/`has_` attributes."),
    "family_amount": ("Amount share", "Confirm amounts belong at this grain rather than a line or ledger product.",
                      "Record monetary facts as DECIMAL amounts."),
    "family_status": ("Status share", "Consolidate overlapping statuses into one lifecycle.", "Track lifecycle state explicitly."),
    "family_classifier": ("Classifier share", "Move large code sets to reference products.",
                          "Use `_type`/`_category` classifiers or reference products."),
    "family_other": ("Unclassified share", "Prefer conventional suffixes (`_date`, `_amount`, `_type`, `_status`, `_flag`, `_code`).", ""),
}


def advise(ir, bands, only=None):
    """Per-product guidance: inferred classification, archetypes, smells, and band deviations."""
    report = []
    for key, product in ir["products"].items():
        if only and product["name"] not in only and key not in only:
            continue
        declared = product["data_type"] in DATA_TYPES
        dt = product["data_type"] if declared else infer_data_type(product, ir["products"],
                                                                    classifier=bands.get("classifier"))
        product = dict(product, data_type=dt)
        scoped = dict(ir, products={**ir["products"], key: product})
        findings = product_smells(scoped, key)
        metrics = product_metrics(product)
        band = bands["by_data_type"].get(dt, {}).get("metrics", {})
        lean = metrics["attributes"] < 15
        for name, (label, above, below) in BAND_ADVICE.items():
            if name not in band or (lean and name.startswith("family_")):
                continue
            b, value = band[name], metrics[name]
            if b["p10"] <= value <= b["p90"] or (name == "family_other" and value < b["p10"]):
                continue
            severity = "warn" if name == "attributes" and value > 1.4 * b["p90"] else "advise"
            direction = "above" if value > b["p90"] else "below"
            remedy = above if direction == "above" else below
            findings.append(_finding(f"SHP-BAND-{name}", severity,
                                     f"{label} {value} is {direction} the {dt} band {b['p10']}..{b['p90']} (median {b['median']}).",
                                     remedy))
        warn = sum(1 for f in findings if f["severity"] == "warn")
        report.append(dict(product=key, data_type=dt, data_type_source="declared" if declared else "inferred",
                           archetypes=sorted(k for k, v in _archetypes(product).items() if v),
                           metrics=metrics, warnings=warn, advisories=len(findings) - warn, findings=findings))
    return report


def _advise_text(report):
    lines = []
    for item in report:
        lines.append(f"{item['product']} [{item['data_type']} ({item['data_type_source']}); "
                     f"{item['metrics']['attributes']} columns; archetypes: {', '.join(item['archetypes']) or 'none'}] "
                     f"warn={item['warnings']} advise={item['advisories']}")
        for f in sorted(item["findings"], key=lambda f: (f["severity"] != "warn", f["code"])):
            lines.append(f"  {f['severity']:<6} {f['code']:<22} {f['message']}")
            lines.append(f"         -> {f['remedy']}")
    return "\n".join(lines)


def _version_key(path):
    match = re.search(r"/v(\d+)/", str(path))
    return int(match.group(1)) if match else 0


def agent_major(path):
    """Agent major version from an export header, without parsing the whole model."""
    with open(path, encoding="utf-8") as handle:
        head = handle.read(4096)
    match = re.search(r'"agent_version"\s*:\s*"(\d+)', head)
    return int(match.group(1)) if match else 0


def latest_corpus(corpus, scope, min_agent_major=0):
    """Latest qualifying version of each industry for one scope (mvm or ecm)."""
    chosen = {}
    for path in sorted(Path(corpus).glob(f"*/v*/{scope}/model.json")):
        if agent_major(path) < min_agent_major:
            continue
        industry = path.parts[-4]
        if industry not in chosen or _version_key(path) > _version_key(chosen[industry]):
            chosen[industry] = path
    return chosen


def build_bands(fingerprints):
    names = sorted(next(iter(fingerprints.values())))
    bands = {}
    for name in names:
        values = [fp[name] for fp in fingerprints.values()]
        mean = statistics.mean(values)
        cv = statistics.pstdev(values) / mean if mean else 0.0
        bands[name] = dict(p10=round(_q(values, 0.10), 4), median=round(_q(values, 0.5), 4),
                           p90=round(_q(values, 0.90), 4), min=round(min(values), 4), max=round(max(values), 4),
                           cv=round(cv, 3), scale=name in SCALE_METRICS,
                           stability="invariant" if cv <= 0.15 else "stable" if cv <= 0.35 else "variable")
        if name in IDEALS:
            bands[name]["ideal"] = IDEALS[name]
    return bands


def check(fingerprint, bands, ignore_scale=False):
    """Weighted in-band score. Invariant metrics weigh 3, stable 2, variable 1."""
    weights = {"invariant": 3, "stable": 2, "variable": 1}
    rows, total, earned = [], 0, 0
    for name, band in bands.items():
        if name not in fingerprint or (ignore_scale and band["scale"]):
            continue
        value = fingerprint[name]
        low, high = band["p10"], band["p90"]
        if "ideal" in band:
            low, high = min(low, band["ideal"]), max(high, band["ideal"])
        status = "in_band" if low <= value <= high else ("near" if band["min"] <= value <= band["max"] else "out")
        weight = weights[band["stability"]]
        total += weight
        earned += weight * {"in_band": 1.0, "near": 0.5, "out": 0.0}[status]
        rows.append(dict(metric=name, value=value, band=[low, high], median=band["median"],
                         stability=band["stability"], status=status))
    return dict(score=round(100 * earned / total, 1) if total else 0.0, metrics=rows)


AGENT_DEFECT_SMELLS = {"SHP-FK-03", "SHP-FK-05"}


def product_score(report, bands):
    """Product-level score: structural conformance and column-depth fit, each 0..1.

    Conformance is the share of products with no structural warning; documented agent defects
    (AGENT_DEFECT_SMELLS) are reported separately rather than scored. Depth fit gives 1 for
    column counts inside the class p10..p90 band, 0.5 inside p02..p98, else 0.
    """
    if not report:
        return dict(score=0.0, conformance=0.0, depth_fit=0.0, products=0, warn_codes={}, agent_defect_warnings=0)
    clean, depth, codes, defect_warns = 0, 0.0, collections.Counter(), 0
    for item in report:
        warns = [f["code"] for f in item["findings"] if f["severity"] == "warn"]
        structural = [c for c in warns if c not in AGENT_DEFECT_SMELLS]
        defect_warns += len(warns) - len(structural)
        codes.update(structural)
        clean += not structural
        band = bands["by_data_type"].get(item["data_type"], {}).get("metrics", {}).get("attributes")
        if band:
            value = item["metrics"]["attributes"]
            depth += 1.0 if band["p10"] <= value <= band["p90"] else 0.5 if band["p02"] <= value <= band["p98"] else 0.0
    n = len(report)
    conformance, depth_fit = clean / n, depth / n
    return dict(score=round(50 * (conformance + depth_fit), 1), conformance=round(conformance, 3),
                depth_fit=round(depth_fit, 3), products=n, warn_codes=dict(codes.most_common()),
                agent_defect_warnings=defect_warns)


def composite_score(model_score, product_result):
    """Equal weight to model topology and product shape."""
    return round((model_score + product_result["score"]) / 2, 1)


def _classifier_holdout(irs):
    correct = total = 0
    for industry, ir in irs.items():
        model = train_classifier({k: v for k, v in irs.items() if k != industry})
        for product in ir["products"].values():
            if product["data_type"] in DATA_TYPES:
                total += 1
                correct += classify(product, model) == product["data_type"]
    return round(correct / total, 3) if total else 0.0


PADDING_MIN_PRODUCTS = 8
PADDING_UBIQUITY = 0.8
PADDING_ALLOWANCE = 2
PADDING_SENTENCE_MIN = 24


def depad(ir):
    """Discount boilerplate before scoring: depth is not padding.

    Calibrated on the agent corpus, where at most 2 non-key columns appear in 80%+ of a
    model's products (created/updated stamps, which the allowance keeps first) and repeated description sentences are rare
    (MVM max 0.063 per attribute, ECM max 0.014). Beyond that allowance, ubiquitous non-key
    columns, the edges they carry, and sentences repeated across many descriptions are
    stripped, so they cannot raise depth or density. Returns (ir, padding_summary).
    """
    products = ir["products"]
    n = len(products)
    summary = dict(stripped_columns=[], repeated_sentences=0, repeated_sentence_rate=0.0)
    if n < PADDING_MIN_PRODUCTS:
        return ir, summary
    counts = collections.Counter(a["name"] for p in products.values() for a in p["attrs"]
                                 if a["name"] not in p["pk"])
    audit = re.compile(dict(FAMILIES)["audit"])
    ubiquitous = sorted((name for name, c in counts.items() if c >= PADDING_UBIQUITY * n),
                        key=lambda name: (not audit.search(name), "timestamp" not in name, -counts[name], name))
    strip = set(ubiquitous[PADDING_ALLOWANCE:])
    sentences = collections.Counter()
    for p in products.values():
        for text in [p["description"]] + [a["description"] for a in p["attrs"]]:
            sentences.update(_sentences(text))
    repeated = {s for s, c in sentences.items() if c >= max(5, 0.2 * n)}
    n_attrs = sum(len(p["attrs"]) for p in products.values()) or 1
    hits = sum(c for s, c in sentences.items() if s in repeated)

    def clean(text):
        if not repeated:
            return text
        return " ".join(s for s in _sentences(text, keep_short=True) if s not in repeated)

    new_products = {}
    for key, p in products.items():
        attrs = [dict(a, description=clean(a["description"])) for a in p["attrs"]
                 if a["name"] not in strip or a["name"] in p["pk"]]
        new_products[key] = dict(p, attrs=attrs, description=clean(p["description"]))
    edges = [e for e in ir["edges"] if e[2] not in strip]
    summary.update(stripped_columns=sorted(strip), repeated_sentences=len(repeated),
                   repeated_sentence_rate=round(hits / n_attrs, 3))
    return dict(ir, products=new_products, edges=edges), summary


def _sentences(text, keep_short=False):
    parts = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text or "") if s.strip()]
    return parts if keep_short else [s for s in parts if len(s) >= PADDING_SENTENCE_MIN]


SLICE_SIZES = (3, 4, 5, 6)


def slice_ir(ir, domains):
    """A bounded slice of a model: the named domains only, as a designer would bound it.

    FK columns whose targets fall outside the slice are dropped (they could not be declared),
    and metric views are pro-rated by product share.
    """
    keep = {k for k, p in ir["products"].items() if p["domain"] in domains}
    products = {}
    for key in keep:
        p = ir["products"][key]
        products[key] = dict(p, attrs=[a for a in p["attrs"] if not a["fk"] or a["fk"] in keep])
    edges = [e for e in ir["edges"] if e[0] in keep and e[1] in keep]
    share = len(keep) / len(ir["products"]) if ir["products"] else 0.0
    return dict(ir, products=products, edges=edges, domains=[d for d in ir["domains"] if d["name"] in domains],
                metric_views=round(ir["metric_views"] * share))


def connected_slices(ir, sizes=SLICE_SIZES):
    """Most interconnected k-domain subset per k, found greedily (what a bounded request picks)."""
    weight = collections.Counter()
    for source, target, _ in ir["edges"]:
        if target in ir["products"] and source in ir["products"]:
            a, b = ir["products"][source]["domain"], ir["products"][target]["domain"]
            if a != b:
                weight[frozenset((a, b))] += 1
    names = [d["name"] for d in ir["domains"]]
    slices = []
    for k in sizes:
        if k >= len(names):
            continue
        seed = max(weight, key=weight.get, default=frozenset(names[:2]))
        chosen = set(seed)
        while len(chosen) < k:
            chosen.add(max((n for n in names if n not in chosen),
                           key=lambda n: (sum(weight[frozenset((n, c))] for c in chosen), n)))
        slices.append(sorted(chosen)[:k])
    return slices


def _slice_reference(irs, product_bands):
    """Bands, holdout, and composite calibration for bounded slices of agent models."""
    fps = {}
    for industry, ir in irs.items():
        for domains in connected_slices(ir):
            fps[(industry, len(domains))] = (slice_ir(ir, set(domains)), None)
    for key, (sliced, _) in fps.items():
        fps[key] = (sliced, profile(sliced))
    bands = build_bands({k: v[1] for k, v in fps.items()})
    shape, composite = {}, {}
    for industry in irs:
        others = build_bands({k: v[1] for k, v in fps.items() if k[0] != industry})
        own = [k for k in fps if k[0] == industry]
        scores = [check(fps[k][1], others, ignore_scale=True)["score"] for k in own]
        prods = [product_score(advise(fps[k][0], product_bands), product_bands)["score"] for k in own]
        shape[industry] = round(statistics.median(scores), 1)
        composite[industry] = round(statistics.median(
            [composite_score(a, dict(score=b)) for a, b in zip(scores, prods)]), 1)
    summary = lambda d: dict(median=statistics.median(d.values()), min=min(d.values()), max=max(d.values()))
    return dict(sizes=list(SLICE_SIZES), slices=len(fps), selection="most interconnected k domains per industry",
                bands=bands, leave_one_out=dict(**summary(shape), scores=dict(sorted(shape.items()))),
                composite=dict(**summary(composite), scores=dict(sorted(composite.items()))))


def build_envelope(corpus, scopes=("mvm", "ecm"), min_agent_major=4):
    envelope = dict(envelope_version="1.5.0", method="shape-envelope",
                    corpus_filter=dict(min_agent_major=min_agent_major, selection="latest qualifying version per industry"),
                    scopes={})
    corpus_irs = {}
    for scope in scopes:
        paths = latest_corpus(corpus, scope, min_agent_major)
        irs = {industry: depad(load(path))[0] for industry, path in paths.items()}
        corpus_irs[scope] = irs
        fps = {industry: profile(ir) for industry, ir in irs.items()}
        bands = build_bands(fps)
        holdout = {}
        for industry in fps:
            others = {k: v for k, v in fps.items() if k != industry}
            holdout[industry] = check(fps[industry], build_bands(others))["score"]
        defect_rates = collections.defaultdict(list)
        for ir in irs.values():
            for k, v in defects(ir).items():
                defect_rates[k].append(v)
        envelope["scopes"][scope] = dict(
            industries=sorted(fps), count=len(fps),
            sources=sorted(str(p.relative_to(corpus)) for p in paths.values()), bands=bands,
            leave_one_out=dict(median=statistics.median(holdout.values()), min=min(holdout.values()),
                               max=max(holdout.values()), scores=dict(sorted(holdout.items()))),
            observed_defects={k: dict(median=round(statistics.median(v), 4), max=round(max(v), 4)) for k, v in defect_rates.items()})
    # Product shape does not depend on scope (an MVM is a subset of its ECM), so pool the superset.
    source = "ecm" if "ecm" in corpus_irs else scopes[-1]
    envelope["product_bands"] = dict(source_scope=source, **product_bands(corpus_irs[source]))
    classifier = train_classifier(corpus_irs[source])
    classifier["leave_one_out_accuracy"] = _classifier_holdout(corpus_irs[source])
    envelope["product_bands"]["classifier"] = classifier
    # Calibrate the composite on the corpus itself (model part held out; product bands pooled).
    for scope, irs in corpus_irs.items():
        data = envelope["scopes"][scope]
        composites = {}
        for industry, ir in irs.items():
            prod = product_score(advise(ir, envelope["product_bands"]), envelope["product_bands"])
            composites[industry] = dict(product=prod["score"],
                                        composite=composite_score(data["leave_one_out"]["scores"][industry], prod))
        values = [v["composite"] for v in composites.values()]
        product_values = [v["product"] for v in composites.values()]
        data["composite"] = dict(median=statistics.median(values), min=min(values), max=max(values),
                                 product_median=statistics.median(product_values), scores=dict(sorted(composites.items())))
        data["slice"] = _slice_reference(irs, envelope["product_bands"])
    return envelope


def _band(bands, name, digits=2):
    band = bands[name]
    return dict(target=round(band["median"], digits), low=round(band["p10"], digits), high=round(band["p90"], digits))


def targets(envelope, scope, domains=None):
    """Turn envelope bands into a skeleton-first synthesis brief (quotas, not a model)."""
    bands = envelope["scopes"][scope]["bands"]
    n_domains = int(domains or round(bands["domains"]["median"]))
    per_domain = round(bands["products_per_domain_median"]["median"])
    n_products = n_domains * per_domain
    attrs = bands["attrs_per_product_median"]["median"]
    fk_total = round(n_products * bands["fk_per_product"]["median"])
    inbound_hubs = max(1, round(n_products * 0.1))
    families = {name.removeprefix("family_"): round(bands[name]["median"] * attrs, 1)
                for name in bands if name.startswith("family_")}
    return dict(
        scope=scope,
        basis=f"medians of {envelope['scopes'][scope]['count']} industries; use p10-p90 as tolerance",
        sizing=dict(domains=n_domains, subdomains_per_domain=_band(bands, "subdomains_per_domain_median", 0),
                    products_per_domain=_band(bands, "products_per_domain_median", 0), products=n_products,
                    attributes_per_product=dict(p25=bands["attrs_per_product_p25"]["median"], median=attrs,
                                                p75=bands["attrs_per_product_p75"]["median"]),
                    metric_views=round(n_products * bands["metric_views_per_product"]["median"])),
        divisions={k.removeprefix("division_"): round(bands[k]["median"] * n_domains)
                   for k in ("division_operations", "division_business", "division_corporate")},
        data_types={dt: round(bands[f"type_{dt.split('_')[0]}"]["median"] * n_products) for dt in DATA_TYPES},
        archetypes={k.removeprefix("archetype_"): round(bands[k]["median"] * n_products)
                    for k in bands if k.startswith("archetype_")},
        graph=dict(fks=fk_total, cross_domain_fks=round(fk_total * bands["cross_domain_fk_share"]["median"]),
                   self_references=round(fk_total * bands["self_ref_share"]["median"]),
                   out_degree=dict(transactional=_band(bands, "out_degree_transactional", 1),
                                   master=_band(bands, "out_degree_master", 1)),
                   in_degree=dict(master=_band(bands, "in_degree_master", 1),
                                  transactional=_band(bands, "in_degree_transactional", 1)),
                   inbound_hubs=dict(products=inbound_hubs,
                                     share_of_inbound=round(bands["hub_inbound_top10pct_share"]["median"], 2)),
                   domain_roles=dict(producers=round(n_domains * bands["domain_producer_share"]["median"]),
                                     consumers=round(n_domains * bands["domain_consumer_share"]["median"]),
                                     polarity_spread=round(bands["domain_polarity_spread"]["median"], 2),
                                     rule="producers own master hubs (inbound >> outbound); consumers own "
                                          "transactions (outbound >> inbound); polarity = (in - out) / (in + out)"),
                   domain_pair_coverage=round(bands["domain_pair_coverage"]["median"], 2),
                   dag_depth_median_rel=round(bands["dag_depth_median_rel"]["median"], 2),
                   cycles=0, siloed_products=0, unresolved_fks=0),
        attribute_families_per_product=families,
        sql_types={k.removeprefix("sqltype_"): round(bands[k]["median"], 2) for k in bands if k.startswith("sqltype_")},
        body_plan=["primary key first", "foreign keys immediately after the key",
                   "business columns", "audit columns present (conventionally last; corpus order varies)"],
        conventions=dict(fk_name_ends_with_target_pk=True, two_word_subdomains=True,
                         value_pattern_share=round(bands["value_pattern_share"]["median"], 2),
                         sensitive_tag_share=round(bands["sensitive_tag_share"]["median"], 2),
                         temporal_date_share=round(bands["temporal_date_share"]["median"], 2),
                         audit_column_product_share=round(bands["audit_column_product_share"]["median"], 2),
                         product_description_chars=round(bands["product_description_chars_median"]["median"]),
                         attribute_description_chars=round(bands["attribute_description_chars_median"]["median"])),
        forbidden_defects=sorted(envelope["scopes"][scope].get("observed_defects", {})),
    )


def _targets_text(plan, prefix=""):
    lines = []
    for key, value in plan.items():
        if isinstance(value, dict):
            lines.append(f"{prefix}{key}:")
            lines.append(_targets_text(value, prefix + "  "))
        else:
            lines.append(f"{prefix}{key}: {value}")
    return "\n".join(lines)


def _text_report(result, show_all=False):
    lines = [f"shape score: {result['score']}" + (f" (reference: {result['reference']})" if "reference" in result else "")]
    if "products" in result:
        prod = result["products"]
        lines.append(f"product score: {prod['score']} (conformance {prod['conformance']}, depth fit {prod['depth_fit']}, "
                     f"{prod['products']} products)")
        lines.append(f"composite: {result['composite']}")
        if prod["warn_codes"]:
            lines.append("  structural warnings: " + ", ".join(f"{k}={v}" for k, v in prod["warn_codes"].items()))
    order = {"out": 0, "near": 1, "in_band": 2}
    for row in sorted(result["metrics"], key=lambda r: (order[r["status"]], r["stability"], r["metric"])):
        if row["status"] == "in_band" and not show_all:
            continue
        lines.append(f"  {row['status']:<8} {row['stability']:<9} {row['metric']:<36} "
                     f"{row['value']!s:<10} band {row['band'][0]}..{row['band'][1]}")
    padding = result.get("padding") or {}
    if padding.get("stripped_columns") or padding.get("repeated_sentences"):
        lines.append(f"padding discounted: {len(padding['stripped_columns'])} ubiquitous columns "
                     f"({', '.join(padding['stripped_columns'][:6])}{', ...' if len(padding['stripped_columns']) > 6 else ''}), "
                     f"{padding['repeated_sentences']} repeated sentences (rate {padding['repeated_sentence_rate']})")
    flagged = {k: v for k, v in result.get("defects", {}).items() if v}
    lines.append("defects: " + (", ".join(f"{k}={v}" for k, v in flagged.items()) if flagged else "none"))
    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    p_profile = sub.add_parser("profile")
    p_profile.add_argument("models", nargs="+", type=Path)
    p_build = sub.add_parser("build-envelope")
    p_build.add_argument("--corpus", type=Path, required=True)
    p_build.add_argument("--out", type=Path, required=True)
    p_build.add_argument("--min-agent-major", type=int, default=4,
                         help="Exclude earlier agent generations (default 4: current notebook lineage).")
    p_check = sub.add_parser("check")
    p_check.add_argument("model", type=Path)
    p_check.add_argument("--envelope", type=Path, required=True)
    p_check.add_argument("--scope", choices=["mvm", "ecm"], required=True)
    p_check.add_argument("--ignore-scale", action="store_true", help="Skip scope-size metrics for bounded slices.")
    p_check.add_argument("--reference", choices=["auto", "full", "slice"], default="auto",
                         help="Compare with full agent models or with bounded slices of them. "
                              "auto picks slice when the model has fewer domains than the scope's p10.")
    p_check.add_argument("--min-score", type=float, default=None, help="Fail below this model (topology) score.")
    p_check.add_argument("--min-composite", type=float, default=None, help="Fail below this composite score.")
    p_check.add_argument("--format", choices=["json", "text"], default="json")
    p_targets = sub.add_parser("targets")
    p_targets.add_argument("--envelope", type=Path, required=True)
    p_targets.add_argument("--scope", choices=["mvm", "ecm"], required=True)
    p_targets.add_argument("--domains", type=int, default=None, help="Override the domain count.")
    p_targets.add_argument("--format", choices=["json", "text"], default="json")
    p_advise = sub.add_parser("advise", help="Per-table guidance toward common shapes (JSON model or .sql DDL).")
    p_advise.add_argument("model", type=Path)
    p_advise.add_argument("--envelope", type=Path, required=True)
    p_advise.add_argument("--product", action="append", default=None, help="Limit to a product name (repeatable).")
    p_advise.add_argument("--format", choices=["json", "text"], default="text")
    p_advise.add_argument("--fail-on-warn", action="store_true")
    args = parser.parse_args(argv)
    if args.command == "advise":
        envelope = json.loads(args.envelope.read_text())
        report = advise(load(args.model), envelope["product_bands"], args.product)
        print(_advise_text(report) if args.format == "text" else json.dumps(report, indent=2))
        return 1 if args.fail_on_warn and any(item["warnings"] for item in report) else 0
    if args.command == "targets":
        plan = targets(json.loads(args.envelope.read_text()), args.scope, args.domains)
        print(_targets_text(plan) if args.format == "text" else json.dumps(plan, indent=2))
        return 0
    if args.command == "profile":
        out = {str(path): dict(metrics=profile(load(path)), defects=defects(load(path))) for path in args.models}
        print(json.dumps(out, indent=2))
        return 0
    if args.command == "build-envelope":
        envelope = build_envelope(args.corpus, min_agent_major=args.min_agent_major)
        args.out.write_text(json.dumps(envelope, indent=2) + "\n")
        for scope, data in envelope["scopes"].items():
            print(f"{scope}: {data['count']} industries, leave-one-out median {data['leave_one_out']['median']}")
        return 0
    envelope = json.loads(args.envelope.read_text())
    raw_ir = load(args.model)
    ir, padding = depad(raw_ir)
    scope = envelope["scopes"][args.scope]
    reference = args.reference
    if reference == "auto":
        reference = "slice" if "slice" in scope and len(ir["domains"]) < scope["bands"]["domains"]["p10"] else "full"
    bands = scope["slice"]["bands"] if reference == "slice" else scope["bands"]
    result = check(profile(ir), bands, args.ignore_scale or reference == "slice")
    result["reference"] = reference
    result["defects"] = defects(raw_ir)
    result["padding"] = padding
    if "product_bands" in envelope:
        result["products"] = product_score(advise(ir, envelope["product_bands"]), envelope["product_bands"])
        result["composite"] = composite_score(result["score"], result["products"])
    print(_text_report(result) if args.format == "text" else json.dumps(result, indent=2))
    if args.min_score is not None and result["score"] < args.min_score:
        return 1
    if args.min_composite is not None and result.get("composite", 0.0) < args.min_composite:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
