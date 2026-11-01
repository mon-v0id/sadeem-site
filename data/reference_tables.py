"""Builds the reference table an observer adds objects from.

Two open catalogues, both CC BY-SA 4.0, converted into one compact file the
app ships (`Sadeem/Resources/Reference/reference-objects.json`):

* **OpenNGC** (Mattia Verga) — the NGC and IC catalogues and their addendum:
  galaxies, clusters, nebulae, planetary nebulae, supernova remnants.
* **HYG 4.4** (David Nash, astronexus) — stars: every star brighter than
  magnitude 6.5, the naked-eye limit, and every star with a proper name.

What is left out, and why:

* OpenNGC's single and double stars, asterisms and associations — the stars
  come from HYG, which measures them; an OpenNGC `*` row is a pointer.
* OpenNGC's duplicates (`Dup`) — their names become aliases of the object they
  duplicate, so "NGC 3" still finds it.
* Galaxy pairs, triplets and groups — each member is its own row; a group is
  not one of Sadeem's object kinds, and calling it a galaxy would be wrong.
* `NonEx`, `Nova` and `Other` — not objects to observe.
* The Sun.

Each row records which of Sadeem's own objects it is, when it is one, so the
app opens the existing page instead of adding a copy.

The raw sources are downloaded into `Research/External/ReferenceTables/` (not
committed); this script is the only path from them to the app.
"""
import csv
import gzip
import json
import math
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[1]
SOURCES = ROOT / "Research/External/ReferenceTables"
OUTPUT = ROOT / "Sadeem/Resources/Reference/reference-objects.json"
OBJECTS = ROOT / "Sadeem/Resources/Catalog/objects.json"

NAKED_EYE_LIMIT = 6.5

# OpenNGC type → Sadeem kind. A type absent here is left out.
OPENNGC_KINDS = {
    "G": "galaxy",
    "OCl": "openCluster",
    "GCl": "globularCluster",
    "Cl+N": "nebula",
    "PN": "planetaryNebula",
    "HII": "nebula",
    "EmN": "nebula",
    "Neb": "nebula",
    "RfN": "nebula",
    "DrkN": "nebula",
    "SNR": "supernovaRemnant",
}

# Designations from OpenNGC's Identifiers column worth searching by; the rest
# (2MASX, SDSS, IRAS, MCG…) are survey numbers no observer types.
ALIAS_CATALOGUES = {
    "C": "Caldwell", "Mel": "Melotte", "Cr": "Collinder", "Sh2": "Sh2",
    "LBN": "LBN", "LDN": "LDN", "B": "Barnard", "UGC": "UGC", "PGC": "PGC",
}

GREEK = {
    "alp": "α", "bet": "β", "gam": "γ", "del": "δ", "eps": "ε", "zet": "ζ",
    "eta": "η", "the": "θ", "iot": "ι", "kap": "κ", "lam": "λ", "mu": "μ",
    "nu": "ν", "xi": "ξ", "omi": "ο", "pi": "π", "rho": "ρ", "sig": "σ",
    "tau": "τ", "ups": "υ", "phi": "φ", "chi": "χ", "psi": "ψ", "ome": "ω",
}

# Sadeem objects made of more than one reference row: every row opens them.
EXTRA_MATCHES = {"caldwell_014": ["NGC 884"]}  # the Double Cluster's second half

# Sadeem objects that are not single points on the sky: never matched.
UNMATCHABLE_KINDS = {"constellation", "asterism", "planet", "planetaryMoon",
                     "moon", "lunarFeature"}


# ---------------------------------------------------------------- parsing

def sexagesimal_degrees(text, hours=False):
    """'05:35:17.3' → degrees (×15 when `hours`); '-05:23:28' → degrees."""
    text = text.strip()
    if not text:
        return None
    sign = -1.0 if text.startswith("-") else 1.0
    parts = [float(p) for p in text.lstrip("+-").split(":")]
    while len(parts) < 3:
        parts.append(0.0)
    value = parts[0] + parts[1] / 60 + parts[2] / 3600
    return sign * value * (15.0 if hours else 1.0)


def designation(name):
    """'NGC7000' → 'NGC 7000', 'IC0434' → 'IC 434', 'NGC0224A' → 'NGC 224A'."""
    match = re.fullmatch(r"([A-Za-z]+)(\d+)(.*)", name)
    if not match:
        return name
    prefix, number, rest = match.groups()
    return f"{prefix} {int(number)}{rest}"


def number_or_none(text):
    text = (text or "").strip()
    return float(text) if text else None


def openngc_aliases(row):
    aliases = []
    if row["M"].strip():
        aliases.append(f"M {int(row['M'])}")
    for identifier in row["Identifiers"].split(","):
        identifier = identifier.strip()
        match = re.fullmatch(r"([A-Za-z0-9]+?)\s?(\d[\w.+-]*)", identifier)
        if not match or match.group(1) not in ALIAS_CATALOGUES:
            continue
        catalogue, number = match.groups()
        if number.isdigit():
            number = number.lstrip("0") or "0"
        aliases.append(f"{ALIAS_CATALOGUES[catalogue]} {number}")
    return aliases


def openngc_rows(rows):
    """Reference rows from OpenNGC, with duplicates folded in as aliases."""
    kept = {}
    duplicates = []
    for row in rows:
        kind = OPENNGC_KINDS.get(row["Type"])
        if row["Type"] == "Dup":
            duplicates.append(row)
            continue
        if kind is None:
            continue
        ra = sexagesimal_degrees(row["RA"], hours=True)
        dec = sexagesimal_degrees(row["Dec"])
        if ra is None or dec is None:
            continue
        v, b = number_or_none(row["V-Mag"]), number_or_none(row["B-Mag"])
        common = [n.strip() for n in row["Common names"].split(",") if n.strip()]
        primary = designation(row["Name"])
        kept[row["Name"]] = {
            "id": "openngc." + row["Name"].lower(),
            "kind": kind,
            "ra": round(ra, 5),
            "dec": round(dec, 5),
            "mag": v if v is not None else b,
            "magBand": "V" if v is not None else ("B" if b is not None else None),
            "major": number_or_none(row["MajAx"]),
            "minor": number_or_none(row["MinAx"]),
            "constellation": row["Const"].strip() or None,
            "name": common[0] if common else primary,
            "aliases": ([primary] if common else []) + common[1:] + openngc_aliases(row),
            "source": "openngc",
        }
    for row in duplicates:
        for column in ("NGC", "IC"):
            target = row[column].strip()
            key = f"{column}{target.zfill(4)}" if target else None
            if key in kept:
                kept[key]["aliases"].append(designation(row["Name"]))
                break
    return list(kept.values())


def star_name(row):
    """The name an observer knows a star by, best first, and its aliases."""
    names = []
    if row["proper"]:
        names.append(row["proper"])
    if row["bayer"] and row["con"]:
        letter = re.match(r"([A-Za-z]+)(-?\d*)", row["bayer"])
        greek = GREEK.get(letter.group(1).lower()) if letter else None
        if greek:
            names.append(f"{greek}{letter.group(2).lstrip('-')} {row['con']}")
            names.append(f"{letter.group(1).capitalize()}{letter.group(2).lstrip('-')} {row['con']}")
    if row["flam"] and row["con"]:
        names.append(f"{row['flam']} {row['con']}")
    for column, label in (("hr", "HR"), ("hd", "HD"), ("hip", "HIP")):
        if row[column]:
            names.append(f"{label} {row[column]}")
    if row["gl"]:
        names.append(row["gl"])
    return (names[0], names[1:]) if names else (None, [])


def hyg_rows(rows):
    kept = []
    for row in rows:
        if row["proper"] == "Sol":
            continue
        magnitude = number_or_none(row["mag"])
        if not row["proper"] and (magnitude is None or magnitude > NAKED_EYE_LIMIT):
            continue
        name, aliases = star_name(row)
        if name is None:
            continue
        kept.append({
            "id": "hyg." + row["id"],
            "kind": "star",
            "ra": round(float(row["ra"]) * 15.0, 5),
            "dec": round(float(row["dec"]), 5),
            "mag": magnitude,
            "magBand": "V" if magnitude is not None else None,
            "major": None,
            "minor": None,
            "constellation": row["con"] or None,
            "name": name,
            "aliases": aliases,
            "source": "hyg",
        })
    return kept


# ---------------------------------------------------------------- matching

def separation_arcmin(ra1, dec1, ra2, dec2):
    r1, d1, r2, d2 = map(math.radians, (ra1, dec1, ra2, dec2))
    cos = math.sin(d1) * math.sin(d2) + math.cos(d1) * math.cos(d2) * math.cos(r1 - r2)
    return math.degrees(math.acos(max(-1.0, min(1.0, cos)))) * 60


def _english_names(record):
    return {n["text"].casefold() for n in record["names"] if n.get("localeIdentifier") == "en"}


def match_to_sadeem(rows, objects):
    """Sets `sadeemID` on each row that is one of Sadeem's own objects.

    By designation first — Messier and Caldwell numbers, and the NGC, IC,
    Melotte and Collinder objects Sadeem names by their number. Then, for a
    star, by its proper name, a position within 1′ whose magnitude agrees to
    one, or within 30′ agreeing to 0.3; for anything else, the nearest row of the same kind within a
    quarter of the object's size (at least 10′). Each Sadeem object claims one
    row, plus any listed in `EXTRA_MATCHES`.
    """
    by_alias = {}
    for row in rows:
        for label in [row["name"], *row["aliases"]]:
            by_alias.setdefault(label.casefold(), row)
    designation_of = {
        "messier": "M {}", "caldwell": "Caldwell {}", "ngc": "NGC {}",
        "ic": "IC {}", "melotte": "Melotte {}", "collinder": "Collinder {}",
    }
    claimed = set()
    stars = [r for r in rows if r["kind"] == "star"]
    for record in objects:
        if record["objectType"] in UNMATCHABLE_KINDS or not record.get("fixedCoordinates"):
            continue
        row = None
        prefix, _, number = record["id"].partition("_")
        if prefix in designation_of and number.isdigit():
            candidate = by_alias.get(designation_of[prefix].format(int(number)).casefold())
            # OpenNGC names an NGC object by its primary name, not an alias.
            if candidate is None and prefix in ("ngc", "ic"):
                candidate = next((r for r in rows if r["id"] == f"openngc.{prefix}{number.zfill(4)}"), None)
            row = candidate
        elif record["objectType"] == "star":
            names = _english_names(record)
            row = next((r for r in stars if r["name"].casefold() in names), None)
            magnitude = record.get("apparentMagnitude")
            if row is None and magnitude is not None:
                close = [r for r in stars if r["mag"] is not None and abs(r["mag"] - magnitude) <= 1.0]
                row = _nearest(record, close, 1.0) or _nearest(
                    record, [r for r in close if abs(r["mag"] - magnitude) <= 0.3], 30.0)
        if row is None and record["objectType"] != "star":
            size = (record.get("angularSize") or {}).get("majorArcMinutes") or 0
            row = _nearest(record, [r for r in rows if r["kind"] == record["objectType"]],
                           max(10.0, size / 4))
        if row is not None and row["id"] not in claimed:
            row["sadeemID"] = record["id"]
            claimed.add(row["id"])
        for label in EXTRA_MATCHES.get(record["id"], []):
            extra = by_alias.get(label.casefold())
            if extra is not None and extra["id"] not in claimed:
                extra["sadeemID"] = record["id"]
                claimed.add(extra["id"])
    return rows


def _nearest(record, candidates, radius_arcmin):
    position = record["fixedCoordinates"]
    best = None
    for row in candidates:
        distance = separation_arcmin(row["ra"], row["dec"], position["rightAscensionDegrees"],
                                     position["declinationDegrees"])
        if distance <= radius_arcmin and (best is None or distance < best[0]):
            best = (distance, row)
    return best[1] if best else None


# ---------------------------------------------------------------- output

COLUMNS = ["id", "kind", "ra", "dec", "mag", "magBand", "major", "minor",
           "constellation", "name", "aliases", "source", "sadeemID"]


def table(rows):
    """Rows as arrays under a column list: a third of the size of objects."""
    rows = sorted(rows, key=lambda r: (r["mag"] is None, r["mag"] if r["mag"] is not None else 0, r["id"]))
    return {
        "version": 1,
        "sources": [
            {"id": "openngc", "title": "OpenNGC", "author": "Mattia Verga",
             "url": "https://github.com/mattiaverga/OpenNGC", "licence": "CC BY-SA 4.0"},
            {"id": "hyg", "title": "HYG Stellar Database 4.4", "author": "David Nash (astronexus)",
             "url": "https://codeberg.org/astronexus/hyg", "licence": "CC BY-SA 4.0"},
        ],
        "columns": COLUMNS,
        "rows": [[row.get(column) for column in COLUMNS] for row in rows],
    }


def build():
    openngc = []
    for name in ("NGC.csv", "addendum.csv"):
        with open(SOURCES / name, newline="", encoding="utf-8") as handle:
            openngc.extend(csv.DictReader(handle, delimiter=";"))
    with gzip.open(SOURCES / "hyg_v44.csv.gz", "rt", newline="", encoding="utf-8") as handle:
        hyg = list(csv.DictReader(handle))
    objects = json.loads(OBJECTS.read_text(encoding="utf-8"))
    rows = match_to_sadeem(openngc_rows(openngc) + hyg_rows(hyg), objects)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(table(rows), ensure_ascii=False, separators=(",", ":")) + "\n",
                      encoding="utf-8")
    return rows


if __name__ == "__main__":
    built = build()
    matched = sum(1 for r in built if r.get("sadeemID"))
    print(f"{len(built)} rows, {matched} of them Sadeem's own, → {OUTPUT.relative_to(ROOT)}")
