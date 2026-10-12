#!/usr/bin/env python3
"""
Panel Data Steward - cluster messy candidate attribute values into a proposed
canonical set, for human approval.

Subcommands:
  keys      inventory every attribute: how populated it is, and which attribute
            names look like duplicates of each other
  cluster   group variant spellings of one attribute and propose a canonical value
  review    print the full per-candidate from -> to list and the held queue
  approve   record approvals, one variant at a time, into approved.json
  plan      turn approved variants into an ordered list of write intents,
            with a reverse plan for undo

Works on an export from any panel, CRM or spreadsheet. Nothing here writes to
a panel - it produces proposals and plans for a human to approve and apply.

Stdlib only. Python 3.9+.
"""

from __future__ import annotations

import argparse
import csv
import datetime
import json
import re
import sys
from collections import Counter, defaultdict
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

# Two thresholds with a clerical-review band between them, as in Fellegi-Sunter
# record linkage. Pairs at or above THRESHOLD are proposed merges. Pairs between
# REVIEW_FLOOR and THRESHOLD go to a review queue and are never merged without a
# person approving them. Below REVIEW_FLOOR they are treated as different values.
# Both numbers are working defaults, not from the literature.
DEFAULT_THRESHOLD = 0.88
DEFAULT_REVIEW_FLOOR = 0.70

# keys: working defaults, not from the literature.
DEFAULT_SPARSE = 0.30
KEY_DUPLICATE_SIMILARITY = 0.85

# Expanded before comparison so "Sr. PM" and "Senior Product Manager" meet.
# These are assumptions, not facts. "pm" in particular is ambiguous - it
# expands to product manager here and the report says so. Override with
# --abbreviations to suit your panel. Not applied to geographic attributes.
DEFAULT_ABBREVIATIONS = {
    "pm": "product manager",
    "tpm": "technical program manager",
    "pmm": "product marketing manager",
    "sr": "senior",
    "snr": "senior",
    "jr": "junior",
    "mgr": "manager",
    "mgmt": "management",
    "dir": "director",
    "vp": "vice president",
    "svp": "senior vice president",
    "evp": "executive vice president",
    "eng": "engineer",
    "engg": "engineering",
    "dev": "developer",
    "ops": "operations",
    "ux": "user experience",
    "ui": "user interface",
    "uxr": "user experience researcher",
    "qa": "quality assurance",
    "hr": "human resources",
    "it": "information technology",
    "ba": "business analyst",
    "csm": "customer success manager",
    "ae": "account executive",
    "sdr": "sales development representative",
    "admin": "administrator",
    "assoc": "associate",
    "exec": "executive",
    "coord": "coordinator",
    "spec": "specialist",
}

# Soft blocks. A token appearing in one value but not the other holds a merge
# for review even when the string similarity clears the threshold. These are
# the words that usually change the job, not the spelling of it. A person can
# approve a soft-blocked merge with `approve --merge`.
DEFAULT_BLOCKING_TOKENS = [
    "marketing", "program", "project", "product", "design", "research",
    "data", "sales", "support", "finance", "legal", "security",
    "senior", "junior", "principal", "staff", "lead", "head", "chief",
    "associate", "assistant", "deputy", "intern", "contractor", "former",
]

# Hard blocks. These pairs are never merged, by the clusterer or by `approve`.
NEGATION_WORDS = {"not", "non", "no"}
NEGATION_PREFIXES = ("un", "in", "non", "dis", "im", "il", "ir")
ANTONYM_PAIRS = {frozenset(p) for p in [
    ("full", "part"), ("active", "inactive"), ("internal", "external"),
    ("current", "former"), ("current", "past"), ("past", "present"),
    ("yes", "no"), ("true", "false"), ("male", "female"), ("man", "woman"),
    ("men", "women"), ("b2b", "b2c"), ("public", "private"),
    ("online", "offline"), ("inbound", "outbound"), ("import", "export"),
    ("permanent", "temporary"), ("primary", "secondary"),
    ("major", "minor"), ("high", "low"), ("higher", "lower"),
    ("upper", "lower"), ("increase", "decrease"), ("more", "less"),
    ("min", "max"), ("minimum", "maximum"), ("before", "after"),
    ("buyer", "seller"), ("early", "late"), ("paid", "free"),
]}

# GDPR Art 9 special categories, matched against attribute-name words. Merges
# in these attributes need a named reviewer. Add your team's own list with
# --sensitive (e.g. income, employment status).
ART9_NAME_WORDS = {
    "race", "racial", "ethnic", "ethnicity", "political", "politics",
    "religion", "religious", "faith", "belief", "beliefs", "philosophical",
    "union", "genetic", "genetics", "dna", "biometric", "biometrics",
    "health", "medical", "disability", "disabled", "diagnosis", "illness",
    "pregnancy", "pregnant", "sexual", "sexuality", "orientation", "lgbt",
    "lgbtq",
}

# Attribute-name words that mark a geographic attribute. Geographic values are
# never fuzzy-matched: Austria/Australia and Niger/Nigeria are close strings and
# different countries. They are grouped by exact spelling, or by ISO 3166-1
# alpha-2 code when the value is a recognised country name.
GEO_NAME_WORDS = {
    "country", "countries", "nation", "nationality", "region", "location",
    "city", "state", "province", "county", "geo", "geography", "territory",
    "locale", "residence",
}

# Country names and common aliases -> ISO 3166-1 alpha-2. Used to group
# geographic values and to refuse merges between two different countries in
# any attribute.
COUNTRIES = {
    "afghanistan": "AF", "albania": "AL", "algeria": "DZ", "andorra": "AD",
    "angola": "AO", "antigua and barbuda": "AG", "argentina": "AR",
    "armenia": "AM", "australia": "AU", "austria": "AT", "azerbaijan": "AZ",
    "bahamas": "BS", "bahrain": "BH", "bangladesh": "BD", "barbados": "BB",
    "belarus": "BY", "belgium": "BE", "belize": "BZ", "benin": "BJ",
    "bhutan": "BT", "bolivia": "BO", "bosnia and herzegovina": "BA",
    "botswana": "BW", "brazil": "BR", "brunei": "BN", "bulgaria": "BG",
    "burkina faso": "BF", "burundi": "BI", "cabo verde": "CV",
    "cape verde": "CV", "cambodia": "KH", "cameroon": "CM", "canada": "CA",
    "central african republic": "CF", "chad": "TD", "chile": "CL",
    "china": "CN", "colombia": "CO", "comoros": "KM", "congo": "CG",
    "democratic republic of the congo": "CD", "drc": "CD",
    "costa rica": "CR", "cote d ivoire": "CI", "ivory coast": "CI",
    "croatia": "HR", "cuba": "CU", "cyprus": "CY", "czechia": "CZ",
    "czech republic": "CZ", "denmark": "DK", "djibouti": "DJ",
    "dominica": "DM", "dominican republic": "DO", "ecuador": "EC",
    "egypt": "EG", "el salvador": "SV", "equatorial guinea": "GQ",
    "eritrea": "ER", "estonia": "EE", "eswatini": "SZ", "swaziland": "SZ",
    "ethiopia": "ET", "fiji": "FJ", "finland": "FI", "france": "FR",
    "gabon": "GA", "gambia": "GM", "georgia": "GE", "germany": "DE",
    "ghana": "GH", "greece": "GR", "grenada": "GD", "guatemala": "GT",
    "guinea": "GN", "guinea bissau": "GW", "guyana": "GY", "haiti": "HT",
    "honduras": "HN", "hong kong": "HK", "hungary": "HU", "iceland": "IS",
    "india": "IN", "indonesia": "ID", "iran": "IR", "iraq": "IQ",
    "ireland": "IE", "israel": "IL", "italy": "IT", "jamaica": "JM",
    "japan": "JP", "jordan": "JO", "kazakhstan": "KZ", "kenya": "KE",
    "kiribati": "KI", "kosovo": "XK", "kuwait": "KW", "kyrgyzstan": "KG",
    "laos": "LA", "latvia": "LV", "lebanon": "LB", "lesotho": "LS",
    "liberia": "LR", "libya": "LY", "liechtenstein": "LI",
    "lithuania": "LT", "luxembourg": "LU", "madagascar": "MG",
    "malawi": "MW", "malaysia": "MY", "maldives": "MV", "mali": "ML",
    "malta": "MT", "marshall islands": "MH", "mauritania": "MR",
    "mauritius": "MU", "mexico": "MX", "micronesia": "FM", "moldova": "MD",
    "monaco": "MC", "mongolia": "MN", "montenegro": "ME", "morocco": "MA",
    "mozambique": "MZ", "myanmar": "MM", "burma": "MM", "namibia": "NA",
    "nauru": "NR", "nepal": "NP", "netherlands": "NL",
    "the netherlands": "NL", "holland": "NL", "new zealand": "NZ",
    "nicaragua": "NI", "niger": "NE", "nigeria": "NG", "north korea": "KP",
    "north macedonia": "MK", "macedonia": "MK", "norway": "NO",
    "oman": "OM", "pakistan": "PK", "palau": "PW", "palestine": "PS",
    "panama": "PA", "papua new guinea": "PG", "paraguay": "PY",
    "peru": "PE", "philippines": "PH", "poland": "PL", "portugal": "PT",
    "puerto rico": "PR", "qatar": "QA", "romania": "RO", "russia": "RU",
    "russian federation": "RU", "rwanda": "RW",
    "saint kitts and nevis": "KN", "saint lucia": "LC",
    "saint vincent and the grenadines": "VC", "samoa": "WS",
    "san marino": "SM", "sao tome and principe": "ST",
    "saudi arabia": "SA", "senegal": "SN", "serbia": "RS",
    "seychelles": "SC", "sierra leone": "SL", "singapore": "SG",
    "slovakia": "SK", "slovenia": "SI", "solomon islands": "SB",
    "somalia": "SO", "south africa": "ZA", "south korea": "KR",
    "korea": "KR", "south sudan": "SS", "spain": "ES", "sri lanka": "LK",
    "sudan": "SD", "suriname": "SR", "sweden": "SE", "switzerland": "CH",
    "syria": "SY", "taiwan": "TW", "tajikistan": "TJ", "tanzania": "TZ",
    "thailand": "TH", "timor leste": "TL", "east timor": "TL",
    "togo": "TG", "tonga": "TO", "trinidad and tobago": "TT",
    "tunisia": "TN", "turkey": "TR", "turkiye": "TR",
    "turkmenistan": "TM", "tuvalu": "TV", "uganda": "UG", "ukraine": "UA",
    "united arab emirates": "AE", "uae": "AE", "united kingdom": "GB",
    "uk": "GB", "u k": "GB", "great britain": "GB", "britain": "GB",
    "england": "GB", "scotland": "GB", "wales": "GB",
    "northern ireland": "GB", "united states": "US",
    "united states of america": "US", "usa": "US", "u s": "US",
    "u s a": "US", "america": "US", "uruguay": "UY", "uzbekistan": "UZ",
    "vanuatu": "VU", "vatican": "VA", "venezuela": "VE", "vietnam": "VN",
    "viet nam": "VN", "yemen": "YE", "zambia": "ZM", "zimbabwe": "ZW",
}
COUNTRY_CODES = set(COUNTRIES.values())


# ---------------------------------------------------------------- normalise

def normalise(value: str, abbreviations: Dict[str, str]) -> str:
    s = value.lower().strip()
    # Keep + and # so C++ and C# stay different values.
    s = re.sub(r"[^\w\s+#]", " ", s)
    tokens = [t for t in s.split() if not re.fullmatch(r"[+#]+", t)]
    tokens = [abbreviations.get(t, t) for t in tokens]
    # Expansion can introduce duplicates: "product manager pm" -> keep order,
    # drop the immediate repeat.
    out: List[str] = []
    for t in " ".join(tokens).split():
        if not out or out[-1] != t:
            out.append(t)
    return " ".join(out)


def country_code(norm: str, allow_codes: bool) -> Optional[str]:
    code = COUNTRIES.get(norm)
    if code is None and allow_codes and norm.upper() in COUNTRY_CODES:
        code = norm.upper()
    return code


def similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a, b).ratio()


def blocked(a: str, b: str, blocking: List[str]) -> Optional[str]:
    """Return the soft-blocking token that holds a merge, or None."""
    ta, tb = set(a.split()), set(b.split())
    for token in blocking:
        if (token in ta) != (token in tb):
            return token
    return None


def hard_block(a: str, b: str, geographic: bool = False) -> Optional[str]:
    """Return why two normalised values must never merge, or None."""
    if a == b:
        return None
    if re.findall(r"\d+", a) != re.findall(r"\d+", b):
        return "numbers differ"
    ca, cb = country_code(a, geographic), country_code(b, geographic)
    if ca and cb and ca != cb:
        return "different countries (%s / %s)" % (ca, cb)
    ta, tb = set(a.split()), set(b.split())
    only_a, only_b = ta - tb, tb - ta
    for t in only_a | only_b:
        if t in NEGATION_WORDS:
            return "negation (%s)" % t
        if "+" in t or "#" in t:
            return "symbol differs (%s)" % t
    for x in only_a:
        for y in only_b:
            for p in NEGATION_PREFIXES:
                if x == p + y or y == p + x:
                    return "negation prefix (%s / %s)" % (x, y)
            if frozenset((x, y)) in ANTONYM_PAIRS:
                return "opposites (%s / %s)" % (x, y)
    return None


def _name_words(name: str) -> Set[str]:
    spaced = re.sub(r"([a-z])([A-Z])", r"\1 \2", name)
    return set(w for w in re.split(r"[^a-z0-9]+", spaced.lower()) if w)


def is_geographic(name: str) -> bool:
    return bool(_name_words(name) & GEO_NAME_WORDS)


def sensitive_reason(name: str, team_list: List[str]) -> Optional[str]:
    if name.lower() in {t.lower() for t in team_list}:
        return "on the team's sensitive list"
    words = _name_words(name)
    if words & ART9_NAME_WORDS or {"sex", "life"} <= words:
        return "looks like a GDPR Art 9 special category"
    return None


# ------------------------------------------------------------------- input

def _record_list(data: Any) -> List[Any]:
    if isinstance(data, dict):
        for key in ("candidates", "data", "results", "items"):
            if isinstance(data.get(key), list):
                return data[key]
        return []
    return data if isinstance(data, list) else []


def _layers(rec: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Split a record into (custom attributes, system fields). Great Question's
    MCP returns custom attributes under attributes.extra. Custom attributes win
    over system fields of the same name, so a top-level `type` never hides
    extra.type."""
    attrs = rec.get("attributes") if isinstance(rec.get("attributes"), dict) else {}
    custom: Dict[str, Any] = {}
    for layer in (attrs.get("extra"), rec.get("extra")):
        if isinstance(layer, dict):
            for k, v in layer.items():
                custom.setdefault(k, v)
    system: Dict[str, Any] = {}
    for layer in (rec, attrs):
        for k, v in layer.items():
            if k in ("attributes", "extra"):
                continue
            system.setdefault(k, v)
    return custom, system


def _attr_bag(rec: Dict[str, Any]) -> Dict[str, Any]:
    custom, system = _layers(rec)
    bag = dict(system)
    bag.update(custom)
    return bag


def _empty(v: Any) -> bool:
    return v is None or (isinstance(v, str) and not v.strip()) or v == []


def _read_csv(p: Path) -> Tuple[List[str], List[Dict[str, str]]]:
    with p.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        if reader.fieldnames is None:
            sys.exit("error: %s has no header row" % p)
        return list(reader.fieldnames), list(reader)


def load_values(path: str, attribute: str) -> Dict[str, Any]:
    """Read one attribute. Returns rows [(candidate_id, raw_value)], list
    attributes {candidate_id: original_list}, the exact attribute name each
    candidate has {candidate_id: name}, and collisions: candidates holding the
    attribute under two spellings at once."""
    p = Path(path)
    if not p.exists():
        sys.exit("error: no such file: %s" % path)

    rows: List[Tuple[str, str]] = []
    lists: Dict[str, List[str]] = {}
    keys_by_cid: Dict[str, str] = {}
    collisions: List[Dict[str, Any]] = []
    low = attribute.lower()

    if p.suffix.lower() == ".csv":
        fieldnames, records = _read_csv(p)
        id_col = _pick(fieldnames, ["candidate_id", "id", "uuid", "email"])
        val_cols = [c for c in fieldnames if c.lower() == low]
        if not val_cols:
            sys.exit("error: no column named %r in %s. Columns: %s"
                     % (attribute, path, ", ".join(fieldnames)))
        for i, row in enumerate(records):
            cid = row.get(id_col) or "row%d" % i
            filled = [c for c in val_cols if (row.get(c) or "").strip()]
            if len(filled) > 1:
                collisions.append({"candidate_id": cid, "attributes": filled})
                continue
            if filled:
                rows.append((cid, row[filled[0]]))
                keys_by_cid[cid] = filled[0]
        return {"rows": rows, "lists": lists, "keys": keys_by_cid,
                "collisions": collisions, "column_spellings": val_cols}

    records = _read_json_records(p)
    if not records:
        sys.exit("error: expected a list of records in %s" % path)

    # When any record holds the attribute as a custom attribute, read only
    # custom attributes: a top-level `type` (the JSON:API resource type) must
    # never stand in for extra.type.
    custom_only = any(isinstance(r, dict) and any(k.lower() == low for k in _layers(r)[0])
                      for r in records)
    for i, rec in enumerate(records):
        if isinstance(rec, str):
            if rec.strip():
                rows.append(("row%d" % i, rec))
            continue
        if not isinstance(rec, dict):
            continue
        custom, system = _layers(rec)
        cid = str(system.get("candidate_id") or rec.get("id") or system.get("id") or
                  system.get("uuid") or system.get("email") or "row%d" % i)
        layer = custom if custom_only else system
        filled = [k for k, v in layer.items() if k.lower() == low and not _empty(v)]
        if len(filled) > 1:
            collisions.append({"candidate_id": cid, "attributes": sorted(filled)})
            continue
        if not filled:
            continue
        name, val = filled[0], layer[filled[0]]
        if isinstance(val, list):
            items = [str(x) for x in val if x is not None and str(x).strip()]
            if items:
                lists[cid] = items
                keys_by_cid[cid] = name
                for x in items:
                    rows.append((cid, x))
            continue
        if isinstance(val, (bool, dict)):
            continue  # booleans are not spellings; nothing to canonicalise
        if str(val).strip():
            rows.append((cid, str(val)))
            keys_by_cid[cid] = name
    return {"rows": rows, "lists": lists, "keys": keys_by_cid,
            "collisions": collisions, "column_spellings": []}


def _read_json_records(p: Path) -> List[Any]:
    """One JSON file, or a directory of them — e.g. one file per page saved from
    a paginated API such as the Great Question MCP's list_candidates. Records
    are de-duplicated on id so an overlapping page is not double-counted."""
    files = sorted(p.glob("*.json")) if p.is_dir() else [p]
    if p.is_dir() and not files:
        sys.exit("error: no .json files in %s" % p)
    out: List[Any] = []
    seen = set()
    for f in files:
        for rec in _record_list(json.loads(f.read_text(encoding="utf-8"))):
            rid = rec.get("id") if isinstance(rec, dict) else None
            if rid is not None:
                if rid in seen:
                    continue
                seen.add(rid)
            out.append(rec)
    return out


def load_records(path: str) -> List[Tuple[Dict[str, Any], Dict[str, Any]]]:
    """Every record as (custom attributes, system fields). CSV columns count as
    system fields."""
    p = Path(path)
    if not p.exists():
        sys.exit("error: no such path: %s" % path)
    if p.is_file() and p.suffix.lower() == ".csv":
        _, rows = _read_csv(p)
        return [({}, dict(r)) for r in rows]
    return [_layers(r) for r in _read_json_records(p) if isinstance(r, dict)]


def _pick(fieldnames: List[str], candidates: List[str]) -> Optional[str]:
    for c in candidates:
        if c and c in fieldnames:
            return c
    return fieldnames[0] if fieldnames else None


# ----------------------------------------------------------------- cluster

def cluster_values(rows: List[Tuple[str, str]], threshold: float,
                   abbreviations: Dict[str, str],
                   blocking: List[str],
                   min_cluster: int,
                   review_floor: float = DEFAULT_REVIEW_FLOOR,
                   geographic: bool = False,
                   sensitive: bool = False) -> Dict[str, Any]:
    counts = Counter(v for _, v in rows)
    members = defaultdict(list)
    for cid, val in rows:
        members[val].append(cid)

    abbrev = {} if geographic else abbreviations

    # Exact-normalised grouping first: the free win, no similarity needed. In a
    # geographic attribute, recognised country names group on ISO code.
    groups: Dict[str, List[str]] = defaultdict(list)
    for val in counts:
        norm = normalise(val, abbrev)
        if geographic:
            code = country_code(norm, True)
            if code:
                norm = "iso:" + code
        groups[norm].append(val)

    keys = sorted(groups, key=lambda k: -sum(counts[v] for v in groups[k]))
    clusters: Dict[str, List[str]] = {}
    held: List[Dict[str, Any]] = []

    for key in keys:
        best_root, best_score = None, 0.0
        if not geographic:  # geographic values are never fuzzy-matched
            for root in clusters:
                score = similarity(key, root)
                if score < review_floor:
                    continue
                pair = {"a": key, "b": root, "similarity": round(score, 3),
                        "a_values": list(groups[key]), "b_values": list(groups[root])}
                hard = hard_block(key, root)
                if hard:
                    held.append(dict(pair, kind="never", reason=hard))
                    continue
                soft = blocked(key, root, blocking)
                if score >= threshold and not soft:
                    if score > best_score:
                        best_root, best_score = root, score
                    continue
                if soft:
                    held.append(dict(pair, kind="blocked", reason="token: %s" % soft))
                else:
                    held.append(dict(pair, kind="review_band",
                                     reason="similarity between %.2f and %.2f"
                                     % (review_floor, threshold)))
        if best_root is None:
            clusters[key] = [key]
        else:
            clusters[best_root].append(key)

    for n, h in enumerate(held, 1):
        h["id"] = "H%d" % n

    out_clusters, orphans = [], []
    for root, norm_keys in clusters.items():
        variants = []
        total = 0
        for nk in norm_keys:
            for surface in groups[nk]:
                variants.append({"value": surface, "count": counts[surface],
                                 "candidate_ids": members[surface]})
                total += counts[surface]
        variants.sort(key=lambda v: -v["count"])
        # Trim the majority spelling so a stray space is never made canonical.
        canonical = re.sub(r"\s+", " ", variants[0]["value"]).strip()

        worst = min((similarity(nk, root) for nk in norm_keys), default=1.0)
        needs_change = any(v["value"] != canonical for v in variants)
        entry = {
            "canonical": canonical,
            "count": total,
            "distinct_variants": len(variants),
            "needs_change": needs_change,
            "confidence": round(worst, 3),
            # Fuzzy-merged clusters go first in the review list; in a
            # sensitive attribute every merge is reviewed.
            "review": len(variants) > 1 and (len(norm_keys) > 1 or sensitive),
            "variants": variants,
        }
        if len(variants) == 1 and total < min_cluster and not needs_change:
            orphans.append(entry)
        else:
            out_clusters.append(entry)

    out_clusters.sort(key=lambda c: -c["count"])
    orphans.sort(key=lambda c: -c["count"])
    used_abbrev = sorted({tok for val in counts
                          for tok in re.split(r"[^\w]+", val.lower())
                          if tok in abbrev})
    return {
        "abbreviations_used": used_abbrev,
        "total_records": len(rows),
        "distinct_values": len(counts),
        "clusters": out_clusters,
        "orphans": orphans,
        "held": held,
    }


def render_report(result: Dict[str, Any], attribute: str, threshold: float,
                  abbrev_used: Dict[str, str]) -> str:
    L = []
    L.append("Attribute value clustering: %s" % attribute)
    L.append("=" * 60)
    merged = sum(1 for c in result["clusters"] if c["distinct_variants"] > 1)
    L.append("%d records · %d distinct values · %d clusters (%d merge more than "
             "one value) · %d orphans · threshold %.2f, review band from %.2f"
             % (result["total_records"], result["distinct_values"],
                len(result["clusters"]), merged, len(result["orphans"]), threshold,
                result.get("review_floor", DEFAULT_REVIEW_FLOOR)))
    L.append("")

    if result.get("sensitive"):
        L.append("SENSITIVE ATTRIBUTE (%s). Every merge needs manual review, and "
                 "`approve` will ask for --reviewer." % result["sensitive"])
        L.append("")
    if result.get("geographic"):
        L.append("GEOGRAPHIC ATTRIBUTE. No fuzzy matching: values group only on exact "
                 "spelling or the same ISO 3166 country code.")
        L.append("")
    spellings = result.get("attribute_spellings") or {}
    if len(spellings) > 1:
        L.append("ATTRIBUTE NAME SPELLED %d WAYS: %s. Each candidate's write uses the "
                 "spelling that candidate already has, so no new attribute is "
                 "created. Merge the attribute names separately."
                 % (len(spellings), ", ".join("%s (%d)" % kv for kv in spellings.items())))
        L.append("")
    if result.get("collisions"):
        L.append("COLLISIONS (%d) — candidates holding the value under two attribute "
                 "spellings at once. Left out of every proposal; fix by hand first:"
                 % len(result["collisions"]))
        for c in result["collisions"][:20]:
            L.append("  %s: %s" % (c["candidate_id"], ", ".join(c["attributes"])))
        L.append("")

    review = [c for c in result["clusters"] if c["review"]]
    if review:
        L.append("REVIEW THESE FIRST (%d) — merged on similarity rather than an exact "
                 "match, which is where false merges live" % len(review))
        for c in review:
            L.append("  %-38s conf %.2f  %d candidates"
                     % (c["canonical"], c["confidence"], c["count"]))
            for v in c["variants"]:
                L.append("      %-34s %d" % (v["value"], v["count"]))
        L.append("")

    L.append("PROPOSED MERGES (%d)" % merged)
    for c in result["clusters"]:
        if c["distinct_variants"] < 2:
            continue
        flag = "  <-- review" if c["review"] else ""
        L.append("  %-38s %d candidates from %d variants%s"
                 % (c["canonical"], c["count"], c["distinct_variants"], flag))
        for v in c["variants"]:
            mark = "*" if v["value"] == c["canonical"] else " "
            L.append("     %s %-33s %d" % (mark, v["value"], v["count"]))
    L.append("")

    for kind, title in (
            ("review_band", "HELD FOR REVIEW (%d) — similarity in the review band; "
                            "not merged unless a person approves it"),
            ("blocked", "BLOCKED MERGES (%d) — similar enough to merge, held apart "
                        "by a token that usually changes the meaning"),
            ("never", "NEVER MERGED (%d) — negation, opposites, different numbers, "
                      "symbols or countries; cannot be approved")):
        items = [h for h in result["held"] if h["kind"] == kind]
        if not items:
            continue
        L.append(title % len(items))
        for h in items[:20]:
            L.append("  %-4s %.2f  %-26s / %-26s  (%s)"
                     % (h["id"], h["similarity"], h["a"], h["b"], h["reason"]))
        if len(items) > 20:
            L.append("  ... and %d more" % (len(items) - 20))
        L.append("")

    ws = [c for c in result["clusters"] if c["distinct_variants"] == 1 and c.get("needs_change")]
    if ws:
        L.append("WHITESPACE FIXES (%d) — one spelling, but with stray spaces" % len(ws))
        for c in ws:
            L.append('  %-38r -> %r  (%d)' % (c["variants"][0]["value"], c["canonical"], c["count"]))
        L.append("")

    singles = [c for c in result["clusters"]
               if c["distinct_variants"] == 1 and not c.get("needs_change")]
    if singles:
        L.append("LEFT ALONE (%d) — one spelling only, nothing to merge" % len(singles))
        L.append("  " + ", ".join("%s (%d)" % (c["canonical"], c["count"])
                                  for c in singles))
        L.append("")

    if result["orphans"]:
        L.append("ORPHANS (%d) — single low-count values, left alone"
                 % len(result["orphans"]))
        L.append("  " + ", ".join("%s (%d)" % (o["canonical"], o["count"])
                                  for o in result["orphans"][:25]))
        if len(result["orphans"]) > 25:
            L.append("  ... and %d more" % (len(result["orphans"]) - 25))
        L.append("")

    ambiguous = [k for k in ("pm", "ba", "it", "ae")
                 if k in result.get("abbreviations_used", [])]
    if ambiguous:
        L.append("Ambiguous expansions applied — check these fit your panel:")
        for k in ambiguous:
            L.append("  %-5s -> %s" % (k, abbrev_used[k]))
        L.append("")

    L.append("Nothing has been written. Next: `review` to see every candidate's "
             "change, `approve` each variant, then `plan`.")
    return "\n".join(L)


def _load_json_file(path: Optional[str], what: str) -> Any:
    if not path:
        return None
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except FileNotFoundError:
        sys.exit("error: %s file not found: %s" % (what, path))


def cmd_cluster(args: argparse.Namespace) -> int:
    abbrev = dict(DEFAULT_ABBREVIATIONS)
    if args.abbreviations:
        abbrev.update(_load_json_file(args.abbreviations, "abbreviations"))
    blocking = list(DEFAULT_BLOCKING_TOKENS)
    if args.blocking_tokens:
        blocking = _load_json_file(args.blocking_tokens, "blocking tokens")
    team_sensitive = _load_json_file(args.sensitive, "sensitive list") or []
    if args.review_threshold > args.threshold:
        sys.exit("error: --review-threshold must not be above --threshold")

    loaded = load_values(args.input, args.attribute)
    rows, lists = loaded["rows"], loaded["lists"]
    if not rows:
        sys.exit("error: no non-empty values for attribute %r in %s. Run `keys` to "
                 "see the attribute names actually present." % (args.attribute, args.input))

    spellings = Counter(loaded["keys"].values())
    attr_name = spellings.most_common(1)[0][0] if spellings else args.attribute
    if args.geographic is None:
        geographic = is_geographic(attr_name)
    else:
        geographic = args.geographic
    sens = sensitive_reason(attr_name, team_sensitive)

    result = cluster_values(rows, args.threshold, abbrev, blocking, args.min_cluster,
                            review_floor=args.review_threshold,
                            geographic=geographic, sensitive=bool(sens))
    if attr_name != args.attribute and len(spellings) == 1:
        print("note: matched %r as %r (attribute names are case-sensitive in "
              "most tools; writes must use %r)\n" % (args.attribute, attr_name, attr_name))
    result.update({
        "attribute": attr_name,
        "attribute_spellings": dict(spellings),
        "attribute_keys": loaded["keys"],
        "collisions": loaded["collisions"],
        "threshold": args.threshold,
        "review_floor": args.review_threshold,
        "geographic": geographic,
        "sensitive": sens,
        "abbreviations": {} if geographic else abbrev,
        "list_values": lists,
    })
    if lists:
        print("note: %r is a list attribute on %d record(s); each item is clustered "
              "separately and the plan rewrites the whole list.\n"
              % (attr_name, len(lists)))

    Path(args.output).write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(render_report(result, attr_name, args.threshold, abbrev))
    print("\nwrote %s" % args.output)
    return 0


# ---------------------------------------------------- review / approve / plan

def _all_entries(proposal: Dict[str, Any]) -> List[Dict[str, Any]]:
    return list(proposal.get("clusters", [])) + list(proposal.get("orphans", []))


def _find_variant(proposal: Dict[str, Any], value: str) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Return (cluster, variant) for a surface value, exact first, then ignoring
    surrounding whitespace."""
    for exact in (True, False):
        hits = []
        for c in _all_entries(proposal):
            for v in c["variants"]:
                if (v["value"] == value) if exact else (v["value"].strip() == value.strip()):
                    hits.append((c, v))
        if len(hits) == 1:
            return hits[0]
        if len(hits) > 1:
            sys.exit("error: %r matches more than one stored value; give the exact "
                     "spelling" % value)
    sys.exit("error: %r is not a value in this proposal" % value)


def _find_target(proposal: Dict[str, Any], value: str) -> Dict[str, Any]:
    for c in _all_entries(proposal):
        if c["canonical"] == value:
            return c
    return _find_variant(proposal, value)[0]


def _hard_reason(proposal: Dict[str, Any], a: str, b: str) -> Optional[str]:
    abbrev = proposal.get("abbreviations") or {}
    geo = bool(proposal.get("geographic"))
    na, nb = normalise(a, abbrev), normalise(b, abbrev)
    return hard_block(na, nb, geographic=geo)


def cmd_review(args: argparse.Namespace) -> int:
    proposal = _load_json_file(args.input, "proposal")
    keys = proposal.get("attribute_keys") or {}
    attribute = proposal.get("attribute")
    print("Per-candidate changes if every proposed variant were approved: %s" % attribute)
    print("=" * 60)
    n = 0
    for c in proposal.get("clusters", []):
        for v in c["variants"]:
            if v["value"] == c["canonical"]:
                continue
            print("%r -> %r  (%d candidates)" % (v["value"], c["canonical"], v["count"]))
            for cid in v["candidate_ids"]:
                print("    %-14s %-20s %r -> %r" % (cid, keys.get(cid, attribute),
                                                   v["value"], c["canonical"]))
                n += 1
    print("\n%d candidate value(s) would change." % n)
    held = proposal.get("held", [])
    if held:
        print("\nHELD QUEUE (%d) — not in any proposal unless approved with "
              "`approve --merge VALUE --into VALUE`:" % len(held))
        for h in held:
            print("  %-4s %-11s %.2f  %s / %s  (%s)"
                  % (h["id"], h["kind"], h["similarity"], " | ".join(h["a_values"]),
                     " | ".join(h["b_values"]), h["reason"]))
    if proposal.get("collisions"):
        print("\nCOLLISIONS (%d) — excluded; fix by hand:" % len(proposal["collisions"]))
        for c in proposal["collisions"]:
            print("  %s: %s" % (c["candidate_id"], ", ".join(c["attributes"])))
    if proposal.get("sensitive"):
        print("\nSensitive attribute (%s): every approval needs --reviewer."
              % proposal["sensitive"])
    print("\nRead only. Nothing has been approved or written.")
    return 0


def cmd_approve(args: argparse.Namespace) -> int:
    proposal = _load_json_file(args.input, "proposal")
    attribute = proposal.get("attribute")
    merges = args.merge or []
    intos = args.into or []
    if len(merges) != len(intos):
        sys.exit("error: every --merge needs a matching --into")
    if not args.variant and not merges:
        sys.exit("error: nothing to approve. Use --variant VALUE (once per variant) "
                 "or --merge VALUE --into VALUE")
    if proposal.get("sensitive") and not args.reviewer:
        sys.exit("error: %r is sensitive (%s). Every merge needs manual review: add "
                 "--reviewer NAME." % (attribute, proposal["sensitive"]))

    out = Path(args.output)
    existing = _load_json_file(str(out), "approved") if out.exists() else None
    if isinstance(existing, dict):
        if existing.get("attribute") != attribute:
            sys.exit("error: %s holds approvals for %r, not %r. Use a different -o."
                     % (out, existing.get("attribute"), attribute))
        approvals = existing.get("approvals", [])
    elif existing is None:
        approvals = []
    else:
        sys.exit("error: %s is not in the approval format; delete it and re-approve "
                 "with `approve`." % out)

    by_from = {a["from"]: a for a in approvals}
    stamp = datetime.datetime.now().isoformat(timespec="seconds")
    new: List[Dict[str, Any]] = []
    for value in args.variant or []:
        cluster, variant = _find_variant(proposal, value)
        if variant["value"] == cluster["canonical"]:
            print("skip: %r is already the canonical value" % variant["value"])
            continue
        new.append({"from": variant["value"], "to": cluster["canonical"],
                    "kind": "proposed"})
    for value, into in zip(merges, intos):
        _, variant = _find_variant(proposal, value)
        target = _find_target(proposal, into)
        hard = _hard_reason(proposal, variant["value"], target["canonical"])
        if hard:
            sys.exit("error: %r and %r can never be merged: %s"
                     % (variant["value"], target["canonical"], hard))
        if variant["value"] == target["canonical"]:
            continue
        new.append({"from": variant["value"], "to": target["canonical"],
                    "kind": "manual"})
    for a in new:
        prev = by_from.get(a["from"])
        if prev and prev["to"] != a["to"]:
            sys.exit("error: %r is already approved into %r; edit that first"
                     % (a["from"], prev["to"]))
        a["approved_at"] = stamp
        if args.reviewer:
            a["reviewer"] = args.reviewer
        by_from[a["from"]] = a
        print("approved: %r -> %r (%s)" % (a["from"], a["to"], a["kind"]))

    out.write_text(json.dumps({"attribute": attribute,
                               "approvals": list(by_from.values())}, indent=2) + "\n",
                   encoding="utf-8")
    print("wrote %s — %d approval(s) in total" % (out, len(by_from)))
    return 0


def cmd_plan(args: argparse.Namespace) -> int:
    if not args.approved:
        sys.exit("error: plan needs --approved. Run `review`, then record approvals "
                 "one variant at a time with `approve`.")
    proposal = _load_json_file(args.input, "proposal")
    attribute = proposal.get("attribute", args.attribute)
    if not attribute:
        sys.exit("error: proposal has no attribute and --attribute was not given")
    approved = _load_json_file(args.approved, "approved")
    if not isinstance(approved, dict) or "approvals" not in approved:
        sys.exit("error: %s is not an approval file. Approvals are per variant; "
                 "create the file with `approve`." % args.approved)
    if approved.get("attribute") != attribute:
        sys.exit("error: approvals are for %r, proposal is for %r"
                 % (approved.get("attribute"), attribute))

    mapping: Dict[str, str] = {}
    skipped: List[str] = []
    for a in approved["approvals"]:
        cluster, variant = _find_variant(proposal, a["from"])
        if proposal.get("sensitive") and not a.get("reviewer"):
            sys.exit("error: %r is sensitive; approval of %r has no reviewer"
                     % (attribute, a["from"]))
        if a.get("kind") == "proposed" and cluster["canonical"] != a["to"]:
            skipped.append("%r: proposal now says %r, approval says %r"
                           % (a["from"], cluster["canonical"], a["to"]))
            continue
        hard = _hard_reason(proposal, a["from"], a["to"])
        if hard:
            sys.exit("error: %r -> %r can never be merged: %s" % (a["from"], a["to"], hard))
        mapping[variant["value"]] = a["to"]

    def resolve(v: str) -> str:
        seen = {v}
        while v in mapping:
            v = mapping[v]
            if v in seen:
                sys.exit("error: approvals form a loop at %r" % v)
            seen.add(v)
        return v

    mapping = {k: resolve(k) for k in mapping}
    mapping = {k: v for k, v in mapping.items() if k != v}

    lists = proposal.get("list_values") or {}
    keys = proposal.get("attribute_keys") or {}
    steps: List[Dict[str, Any]] = []
    touched: Dict[str, Dict[str, Any]] = {}
    for c in _all_entries(proposal):
        for variant in c["variants"]:
            if variant["value"] not in mapping:
                continue
            for cid in variant["candidate_ids"]:
                attr = keys.get(cid, attribute)
                if cid in lists:
                    if cid in touched:
                        continue
                    old = lists[cid]
                    new, seen = [], set()
                    for item in old:
                        item2 = mapping.get(item, item)
                        if item2 not in seen:
                            new.append(item2)
                            seen.add(item2)
                    touched[cid] = {"intent": "update one candidate's attribute value",
                                    "candidate_id": cid, "attribute": attr,
                                    "from": old, "to": new, "list": True}
                else:
                    steps.append({"intent": "update one candidate's attribute value",
                                  "candidate_id": cid, "attribute": attr,
                                  "from": variant["value"],
                                  "to": mapping[variant["value"]]})
    steps.extend(touched.values())
    reverse = [dict(s, intent="undo: restore the previous value",
                    **{"from": s["to"], "to": s["from"]}) for s in reversed(steps)]

    plan = {
        "attribute": attribute,
        "created_at": datetime.datetime.now().isoformat(timespec="seconds"),
        "proposal": str(args.input),
        "approvals": approved["approvals"],
        "excluded_collisions": proposal.get("collisions", []),
        "write_count": len(steps),
        "steps": steps,
        "reverse_steps": reverse,
        "applied": [],
    }
    Path(args.output).write_text(json.dumps(plan, indent=2) + "\n", encoding="utf-8")
    print("Write plan: %s" % attribute)
    print("=" * 60)
    for s in steps:
        print("  %-14s %-20s %r -> %r" % (s["candidate_id"], s["attribute"], s["from"], s["to"]))
    print("\nwrote %s — %d candidate update(s), with a reverse plan for undo"
          % (args.output, len(steps)))
    for s in skipped:
        print("skipped, re-approve: %s" % s)
    if proposal.get("collisions"):
        print("%d candidate(s) excluded: attribute stored under two spellings"
              % len(proposal["collisions"]))
    return 0


# -------------------------------------------------------------------- keys

def _key_norm(k: str) -> str:
    k = re.sub(r"[^a-z0-9]", "", k.lower())
    for suffix in ("multiple", "multi", "list", "s"):
        if k.endswith(suffix) and len(k) > len(suffix) + 2:
            k = k[: -len(suffix)]
    return k


def cmd_keys(args: argparse.Namespace) -> int:
    records = load_records(args.input)
    if not records:
        sys.exit("error: no records found in %s" % args.input)
    n = len(records)
    counts: Counter = Counter()
    kinds: Dict[str, set] = defaultdict(set)
    skip = {"id", "candidate_id", "uuid", "email", "name", "first_name", "last_name",
            "created_at", "updated_at", "deleted_at", "type"}
    for custom, system in records:
        # Custom attributes are always inventoried, even when a system field
        # shares the name.
        fields = [(k, v) for k, v in system.items() if k not in skip and k not in custom]
        fields += list(custom.items())
        for k, v in fields:
            if _empty(v) or isinstance(v, dict):
                continue
            counts[k] += 1
            kinds[k].add("list" if isinstance(v, list) else
                         "bool" if isinstance(v, bool) else
                         "number" if isinstance(v, (int, float)) else "text")

    print("Attribute inventory: %d records" % n)
    print("=" * 60)
    print("  %-28s %8s  %s" % ("attribute", "populated", "kind"))
    for k, c in sorted(counts.items(), key=lambda kv: -kv[1]):
        print("  %-28s %7.0f%%  %s" % (k, 100 * c / n, "/".join(sorted(kinds[k]))))
    print()

    keys = sorted(counts)
    dupes = []
    for i, a in enumerate(keys):
        for b in keys[i + 1:]:
            na, nb = _key_norm(a), _key_norm(b)
            if na == nb or SequenceMatcher(None, na, nb).ratio() >= args.duplicate:
                dupes.append((a, b))
    if dupes:
        print("POSSIBLE DUPLICATE ATTRIBUTES (%d) — two names for one thing splits "
              "the data across both, and a filter on either misses the other" % len(dupes))
        for a, b in dupes:
            print("  %-28s %-28s  (%d / %d records)" % (a, b, counts[a], counts[b]))
        print()
    sparse = [k for k, c in counts.items() if c / n < args.sparse]
    if sparse:
        print("SPARSE (%d) — under %.0f%% populated; a filter on these excludes most "
              "of the panel regardless of fit" % (len(sparse), 100 * args.sparse))
        print("  " + ", ".join(sorted(sparse, key=lambda k: counts[k])))
        print()
    print("Read only. Nothing has been changed.")
    return 0


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(
        prog="attribute_clean.py",
        description="Propose a canonical value set for a candidate attribute.")
    sub = ap.add_subparsers(dest="command", required=True)

    p = sub.add_parser("keys", help="inventory attributes and find duplicate names")
    p.add_argument("input", help="JSON or CSV export, or a directory of JSON pages")
    p.add_argument("--sparse", type=float, default=DEFAULT_SPARSE,
                   help="flag attributes populated below this share (default %.2f; "
                        "working default, not from the literature)" % DEFAULT_SPARSE)
    p.add_argument("--duplicate", type=float, default=KEY_DUPLICATE_SIMILARITY,
                   help="name similarity that flags two attributes as possible "
                        "duplicates (default %.2f; working default, not from the "
                        "literature)" % KEY_DUPLICATE_SIMILARITY)
    p.set_defaults(func=cmd_keys)

    p = sub.add_parser("cluster", help="group variant spellings")
    p.add_argument("input", help="JSON or CSV export, or a directory of JSON pages")
    p.add_argument("--attribute", required=True)
    p.add_argument("--threshold", type=float, default=DEFAULT_THRESHOLD,
                   help="similarity at or above which values are proposed as one "
                        "(default %.2f; working default)" % DEFAULT_THRESHOLD)
    p.add_argument("--review-threshold", type=float, default=DEFAULT_REVIEW_FLOOR,
                   help="pairs between this and --threshold go to the review queue "
                        "(default %.2f; working default)" % DEFAULT_REVIEW_FLOOR)
    p.add_argument("--min-cluster", type=int, default=2,
                   help="single values below this count are listed as orphans")
    p.add_argument("--abbreviations", help="JSON map of overrides")
    p.add_argument("--blocking-tokens", help="JSON list replacing the defaults")
    p.add_argument("--sensitive", help="JSON list of your team's sensitive attribute "
                                       "names, added to the GDPR Art 9 categories")
    g = p.add_mutually_exclusive_group()
    g.add_argument("--geographic", dest="geographic", action="store_true", default=None,
                   help="treat the attribute as geographic: no fuzzy matching")
    g.add_argument("--not-geographic", dest="geographic", action="store_false",
                   help="override geographic detection from the attribute name")
    p.add_argument("-o", "--output", default="proposal.json")
    p.set_defaults(func=cmd_cluster)

    p = sub.add_parser("review", help="show every candidate's proposed change and "
                                      "the held queue")
    p.add_argument("input", help="proposal.json")
    p.set_defaults(func=cmd_review)

    p = sub.add_parser("approve", help="approve variants one at a time")
    p.add_argument("input", help="proposal.json")
    p.add_argument("--variant", action="append",
                   help="approve one variant into its proposed canonical; repeat")
    p.add_argument("--merge", action="append",
                   help="approve a held or blocked value; pair with --into")
    p.add_argument("--into", action="append", help="target value for --merge")
    p.add_argument("--reviewer", help="name of the person who reviewed; required "
                                      "for sensitive attributes")
    p.add_argument("-o", "--output", default="approved.json")
    p.set_defaults(func=cmd_approve)

    p = sub.add_parser("plan", help="turn approved variants into write intents")
    p.add_argument("input", help="proposal.json")
    p.add_argument("--approved", help="approved.json written by `approve` (required)")
    p.add_argument("--attribute")
    p.add_argument("-o", "--output", default="write_plan.json")
    p.set_defaults(func=cmd_plan)

    args = ap.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
