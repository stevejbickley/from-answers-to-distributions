#!/usr/bin/env python3
"""Build an Integrated Values Surveys (IVS) file from EVS and WVS Stata files.

This script is a Python port/guardrail around the official EVS/WVS merge syntax.
It is designed to be *fail-loud*: it validates the source file type, parses the
attached official Stata merge syntax for the 838-variable IVS schema and
structural-missing rules, checks the common dictionary, and writes QC metadata.

Important source-file distinction
---------------------------------
The official merge syntax supplied with this project expects an EVS *Trend File*
covering EVS waves 1-5 (e.g. ZA7503 v3.0.0) plus the WVS Trend File.
ZA7505 v5.0.0 is instead the *Joint EVS/WVS 2017-2022* file. It contains EVS5
and WVS7 only. Appending that whole file to the WVS trend file would duplicate
WVS7 and would still omit EVS1-4. Accordingly:

* Full IVS mode: provide an EVS Trend File. This is the recommended/canonical
  path for recreating IVS 1981-2022.
* Partial mode: if ZA7505 (or a compatible joint 2017-2022 file) is supplied,
  this script can, only with --allow-partial-joint, extract EVS5 cases
  (study==1), discard the embedded WVS7 cases, harmonize EVS5, and append them
  to WVS1-7. The result is explicitly marked PARTIAL because EVS1-4 are absent.

Missing values
--------------
The official Stata syntax converts -1..-5 to Stata extended missings .a..e.
For portability in Python/CSV and to avoid silently losing missing-reason
information, this script keeps the numeric/string codes -1..-5 and applies the
official structural missing codes (-4 = not asked, -3 = not applicable).
Downstream analysis should exclude negative values from substantive responses.

Outputs
-------
* .csv or .csv.gz: memory-safe streaming output (recommended for Python).
* .dta: supported, but requires loading the harmonized data into memory and
  does not reproduce every original Stata value label. Variable labels from
  the common dictionary are retained where possible.
* <output>.manifest.json: provenance, hashes, source classification, warnings.
* <output>.qc_wave_year_counts.csv: row counts by study/common-wave/year.
* <output>.qc_core_missing.csv: basic quality checks for paper-core variables.

Examples
--------
Canonical full IVS (requires EVS Trend File, not ZA7505):

  python merge_evs_wvs_to_ivs.py \
    --evs ZA7503_v3-0-0.dta \
    --wvs Trends_VS_1981_2022_Stata_v4_1.dta \
    --merge-syntax "EVS_WVS_Merge Syntax_stata.do" \
    --dictionary F00011424-Common_EVS_WVS_Dictionary_IVS.xlsx \
    --countries F00011426-EVS_WVS_ParticipatingCountries_June2024.xlsx \
    --output Integrated_values_surveys_1981-2022.csv.gz

Using exactly the currently supplied ZA7505 joint file (PARTIAL only):

  python merge_evs_wvs_to_ivs.py \
    --evs ZA7505_v5-0-0.dta \
    --wvs Trends_VS_1981_2022_Stata_v4_1.dta \
    --merge-syntax "EVS_WVS_Merge Syntax_stata.do" \
    --dictionary F00011424-Common_EVS_WVS_Dictionary_IVS.xlsx \
    --countries F00011426-EVS_WVS_ParticipatingCountries_June2024.xlsx \
    --allow-partial-joint \
    --output IVS_PARTIAL_WVS1-7_EVS5.csv.gz

For the cultural-values paper only (much smaller output): add --core-only.
"""

from __future__ import annotations

import argparse
import collections
import csv
import gzip
import hashlib
import json
import math
import os
import re
import sys
import unicodedata
import zipfile
import xml.etree.ElementTree as ET
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, Iterable, Iterator, List, Mapping, MutableMapping, Optional, Sequence, Tuple

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

PAPER_CORE = [
    "S001", "S002", "S002EVS", "S002VS", "S003", "S009", "S017", "S020",
    "A008", "A165", "E018", "E025", "F063", "F118", "F120", "G006",
    "Y002", "Y003", "A029", "A039", "A040", "A042",
]

# ZA7505 (Joint EVS/WVS 2017-2022) -> official IVS names for fields that are
# not already named with the common IVS variable name.
JOINT_EVS5_ALIASES = {
    "study": "S001",
    "wave": "S002EVS",
    "versn_s": "versn_w",
    "uniqid": "S007_01",
    "intrvwr_id": "S008",
    "cntry": "S003",
    "cntry_AN": "S009",
    "cntrycow": "COW_NUM",
    "year": "S020",
    "fw_start": "S022",
    "fw_end": "S023",
    "cntry_y": "S025",
    "ivlength": "S010",
    "ivstart": "S011A",
    "ivstend": "S011B",
    "ivdate": "S012",
    "lnge_num": "S016",
    "lnge_iso": "S016a",
    "gwght": "S017",
    "wght_eq1000": "S018",
    "respint": "S013",
    "reg_iso": "X048ISO",
    "size_5c": "X049A",
    "E181_EVS5": "E181A",
    "F066_EVS5": "F066",
    "x026_01": "X026_01",
    "X035_EVS5": "X035_2_01",
    "W005_EVS5": "W005_2_01",
    "X047E_EVS5": "X047_EVS",
}

# These are intentionally not mapped in partial mode because their semantics
# differ across source studies or no exact common target can be inferred safely.
JOINT_IGNORED_NONCOMMON = {
    "doi_wvsa", "studytit", "reg_nuts1", "reg_nuts2",
    "E179_WVS7", "F028B_WVS7", "X036E_WVS7", "W006E_WVS7", "X047_WVS7",
}

NS_MAIN = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
NS_REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
NS_PKG_REL = "http://schemas.openxmlformats.org/package/2006/relationships"


@dataclass
class SyntaxRules:
    keep: List[str]
    evs_only_numeric: List[str]      # fill -4 on WVS cases
    evs_only_string: List[str]       # fill "-4" on WVS cases
    wvs_only_numeric: List[str]      # fill -4 on EVS cases
    evs_admin_not_applicable: List[str]  # fill -3 on EVS cases
    evs_indices_not_applicable: List[str] # fill -3 on EVS cases


@dataclass
class QCState:
    rows: int = 0
    source_rows: MutableMapping[str, int] = None
    wave_year_counts: MutableMapping[Tuple[object, object, object], int] = None
    core_total: MutableMapping[str, int] = None
    core_negative: MutableMapping[str, int] = None
    core_na: MutableMapping[str, int] = None
    countries: set = None

    def __post_init__(self):
        self.source_rows = collections.Counter() if self.source_rows is None else self.source_rows
        self.wave_year_counts = collections.Counter() if self.wave_year_counts is None else self.wave_year_counts
        self.core_total = collections.Counter() if self.core_total is None else self.core_total
        self.core_negative = collections.Counter() if self.core_negative is None else self.core_negative
        self.core_na = collections.Counter() if self.core_na is None else self.core_na
        self.countries = set() if self.countries is None else self.countries


# ---------------------------------------------------------------------------
# XLSX reader (stdlib only; avoids requiring an Excel engine)
# ---------------------------------------------------------------------------

def _col_index(cell_ref: str) -> int:
    m = re.match(r"([A-Z]+)", cell_ref)
    if not m:
        raise ValueError(f"Invalid Excel cell reference: {cell_ref}")
    n = 0
    for ch in m.group(1):
        n = n * 26 + (ord(ch) - 64)
    return n


def read_xlsx_sheet(path: Path, sheet_name: str) -> List[List[Optional[str]]]:
    """Read raw cell values from a simple XLSX worksheet using stdlib XML."""
    with zipfile.ZipFile(path) as z:
        shared: List[str] = []
        if "xl/sharedStrings.xml" in z.namelist():
            root = ET.fromstring(z.read("xl/sharedStrings.xml"))
            for si in root.findall(f"{{{NS_MAIN}}}si"):
                shared.append("".join((t.text or "") for t in si.iter(f"{{{NS_MAIN}}}t")))

        wb = ET.fromstring(z.read("xl/workbook.xml"))
        rel = ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
        rels = {r.attrib["Id"]: r.attrib["Target"] for r in rel.findall(f"{{{NS_PKG_REL}}}Relationship")}
        target = None
        sheets = wb.find(f"{{{NS_MAIN}}}sheets")
        if sheets is None:
            raise ValueError(f"No sheets found in {path}")
        for s in sheets:
            if s.attrib.get("name") == sheet_name:
                rid = s.attrib[f"{{{NS_REL}}}id"]
                target = "xl/" + rels[rid]
                break
        if target is None:
            available = [s.attrib.get("name") for s in sheets]
            raise KeyError(f"Sheet {sheet_name!r} not found in {path}; available={available}")

        root = ET.fromstring(z.read(target))
        out: List[List[Optional[str]]] = []
        for row in root.findall(f".//{{{NS_MAIN}}}sheetData/{{{NS_MAIN}}}row"):
            vals: Dict[int, Optional[str]] = {}
            for c in row.findall(f"{{{NS_MAIN}}}c"):
                ci = _col_index(c.attrib["r"])
                typ = c.attrib.get("t")
                v = c.find(f"{{{NS_MAIN}}}v")
                is_node = c.find(f"{{{NS_MAIN}}}is")
                val: Optional[str] = None
                if typ == "s" and v is not None:
                    val = shared[int(v.text)]
                elif typ == "inlineStr" and is_node is not None:
                    val = "".join((t.text or "") for t in is_node.iter(f"{{{NS_MAIN}}}t"))
                elif v is not None:
                    val = v.text
                vals[ci] = val
            if vals:
                out.append([vals.get(i) for i in range(1, max(vals) + 1)])
        return out


# ---------------------------------------------------------------------------
# Provenance / parsing
# ---------------------------------------------------------------------------

def sha256(path: Path, block: int = 8 * 1024 * 1024) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            b = f.read(block)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def _var_tokens(s: str) -> List[str]:
    s = s.replace("///", " ")
    return re.findall(r"\b[A-Za-z_][A-Za-z0-9_]*\b", s)


def parse_merge_syntax(path: Path) -> SyntaxRules:
    text = path.read_text(encoding="utf-8", errors="replace")

    # Final official schema.
    keeps = re.findall(r"(?m)^\s*keep\s+(.+?)\s*$", text)
    if not keeps:
        raise ValueError("Could not find final `keep` command in merge syntax")
    keep = keeps[-1].split()
    if len(keep) < 800:
        raise ValueError(f"Parsed only {len(keep)} IVS variables from keep command; expected ~838")

    def capture(pattern: str, label: str) -> List[str]:
        m = re.search(pattern, text, flags=re.I | re.S)
        if not m:
            raise ValueError(f"Could not parse {label} from merge syntax")
        return _var_tokens(m.group(1))

    evs_only_numeric = capture(
        r"\*\s*\(3\.1\).*?recode\s+(.*?)\s+\(\.\s*=\s*-4\)\s+if\s+S001\s*==\s*2",
        "EVS-only numeric list",
    )
    wvs_only_numeric = capture(
        r"\*\s*\(3\.3\)\s*Variables not included in EVS.*?recode\s+(.*?)\s+\(\.\s*=\s*-4\)\s+if\s+S001\s*==\s*1",
        "WVS-only numeric list",
    )
    evs_admin = capture(
        r"\*\s*\(3\.3\.1\).*?recode\s+(S002.*?S013B)\s+\(\.\s*=\s*-3\)\s+if\s+S001\s*==\s*1",
        "EVS admin not-applicable list",
    )
    evs_indices = capture(
        r"recode\s+(Y003.*?Y024C)\s+\(\.\s*=\s*-3\)\s+if\s*S001\s*==\s*1",
        "EVS index not-applicable list",
    )
    evs_only_string = re.findall(
        r'(?m)^\s*replace\s+([A-Za-z_][A-Za-z0-9_]*)\s*=\s*"-4"\s+if\s+S001\s*==\s*2\s*$',
        text,
    )

    if len(set(x.casefold() for x in keep)) != len(keep):
        raise ValueError("Official keep list contains case-insensitive duplicate variable names")

    return SyntaxRules(
        keep=keep,
        evs_only_numeric=evs_only_numeric,
        evs_only_string=evs_only_string,
        wvs_only_numeric=wvs_only_numeric,
        evs_admin_not_applicable=evs_admin,
        evs_indices_not_applicable=evs_indices,
    )


def read_dictionary(path: Path) -> Tuple[Dict[str, str], Dict[str, str], Dict[str, object]]:
    rows = read_xlsx_sheet(path, "IVS_EVS_and_WVS_Variables")
    if not rows:
        raise ValueError("Common dictionary worksheet is empty")
    var_labels: Dict[str, str] = {}
    canonical: Dict[str, str] = {}
    included = []
    for row in rows[1:]:
        row = row + [None] * (29 - len(row))
        name = (row[2] or "").strip()
        label = (row[3] or "").strip()
        ivs_flag = str(row[28] or "").strip()
        if ivs_flag == "1" and name:
            included.append(name)
            canonical.setdefault(name.casefold(), name)
            if label:
                var_labels.setdefault(name.casefold(), label)
    return canonical, var_labels, {
        "rows_flagged_ivs": len(included),
        "unique_names_casefold": len(set(x.casefold() for x in included)),
        "duplicates_casefold": sorted(k for k, v in collections.Counter(x.casefold() for x in included).items() if v > 1),
    }


def read_participation_reference(path: Path) -> Dict[str, object]:
    rows = read_xlsx_sheet(path, "Countries in EVS and WVS")
    if len(rows) < 3:
        raise ValueError("Participating-countries workbook has too few rows")
    h1, h2 = rows[0], rows[1]
    # Identify recent period columns by two-row heading.
    evs_col = wvs_col = None
    current_period = None
    maxc = max(len(h1), len(h2))
    for j in range(maxc):
        p = h1[j] if j < len(h1) else None
        src = h2[j] if j < len(h2) else None
        if p:
            current_period = str(p).strip()
        if current_period == "2017-2022" and str(src or "").strip().upper() == "EVS":
            evs_col = j
        if current_period == "2017-2022" and str(src or "").strip().upper() == "WVS":
            wvs_col = j
    def count_nonempty(j):
        if j is None:
            return None
        return sum(1 for r in rows[2:] if j < len(r) and r[j] not in (None, ""))
    return {
        "recent_period": "2017-2022",
        "expected_recent_evs_countries": count_nonempty(evs_col),
        "expected_recent_wvs_countries": count_nonempty(wvs_col),
    }


def stata_columns(path: Path) -> List[str]:
    with pd.read_stata(path, iterator=True, convert_categoricals=False) as r:
        return list(r.get_chunk(1).columns)


def classify_evs_source(columns: Sequence[str]) -> str:
    cf = {c.casefold() for c in columns}
    if {"study", "wave", "doi_gesis", "doi_wvsa"}.issubset(cf) and "s001" not in cf:
        return "joint_2017_2022"
    if "s001" in cf and ("s002evs" in cf or "s002vs" in cf):
        return "evs_trend"
    # Older EVS Trend variants may carry lower-case s002vs but otherwise common names.
    if "s002vs" in cf and "a008" in cf and "a165" in cf:
        return "evs_trend"
    return "unknown"


def casefold_map(columns: Sequence[str]) -> Dict[str, str]:
    out = {}
    for c in columns:
        k = c.casefold()
        if k in out and out[k] != c:
            raise ValueError(f"Case-insensitive duplicate columns: {out[k]!r} and {c!r}")
        out[k] = c
    return out


# ---------------------------------------------------------------------------
# Harmonization
# ---------------------------------------------------------------------------

def canonicalize_existing(df: pd.DataFrame, targets: Sequence[str]) -> pd.DataFrame:
    target_by_cf = {x.casefold(): x for x in targets}
    ren = {}
    seen_dest = set(df.columns)
    for c in df.columns:
        dest = target_by_cf.get(c.casefold())
        if dest and dest != c and dest not in seen_dest:
            ren[c] = dest
            seen_dest.add(dest)
    return df.rename(columns=ren)


def _ensure_columns(
    df: pd.DataFrame,
    cols: Sequence[str],
    string_cols: Sequence[str] = (),
) -> pd.DataFrame:
    """Add absent schema columns in one operation with stable dtypes.

    The official merge syntax contains a small set of structural string
    variables that receive the literal code ``"-4"``.  Creating every missing
    column first as float/NaN works in current pandas but triggers incompatible-
    dtype warnings and is scheduled to become an error.  Build missing columns
    in a single frame and predeclare those string fields as object instead.
    This also avoids DataFrame fragmentation when materialising the full
    838-variable IVS schema.
    """
    missing = [c for c in cols if c not in df.columns]
    if not missing:
        return df
    string_set = set(string_cols)
    additions = {
        c: (pd.Series(pd.NA, index=df.index, dtype="object")
            if c in string_set
            else pd.Series(np.nan, index=df.index, dtype="float64"))
        for c in missing
    }
    return pd.concat([df, pd.DataFrame(additions, index=df.index)], axis=1)


def _fill_if_na(df: pd.DataFrame, col: str, value) -> None:
    if col in df.columns:
        df[col] = df[col].where(df[col].notna(), value)


def apply_structural_missing(df: pd.DataFrame, rules: SyntaxRules) -> pd.DataFrame:
    """Apply structural -4/-3 rules from the official Stata syntax."""
    if "S001" not in df.columns:
        raise ValueError("S001 is required before applying structural missing rules")

    evs = pd.to_numeric(df["S001"], errors="coerce").eq(1)
    wvs = pd.to_numeric(df["S001"], errors="coerce").eq(2)

    for c in rules.evs_only_numeric:
        if c in df.columns:
            df.loc[wvs & df[c].isna(), c] = -4
    for c in rules.evs_only_string:
        if c in df.columns:
            df.loc[wvs & df[c].isna(), c] = "-4"
    for c in rules.wvs_only_numeric:
        if c in df.columns:
            df.loc[evs & df[c].isna(), c] = -4
    for c in rules.evs_admin_not_applicable:
        if c in df.columns:
            df.loc[evs & df[c].isna(), c] = -3
    for c in rules.evs_indices_not_applicable:
        if c in df.columns:
            df.loc[evs & df[c].isna(), c] = -3
    if "S019" in df.columns:
        df.loc[evs & df["S019"].isna(), "S019"] = 1
    return df


def harmonize_wvs(df: pd.DataFrame, output_cols: Sequence[str], rules: SyntaxRules) -> pd.DataFrame:
    df = df.copy()
    if "s002" in df.columns and "S002" not in df.columns:
        df = df.rename(columns={"s002": "S002"})
    df = canonicalize_existing(df, output_cols)
    if "S001" not in df.columns:
        df["S001"] = 2
    else:
        # WVS trend input should contain WVS only.
        bad = pd.to_numeric(df["S001"], errors="coerce").dropna().ne(2)
        if bad.any():
            raise ValueError("WVS Trend chunk contains S001 values other than 2")
    df = _ensure_columns(df, output_cols, string_cols=rules.evs_only_string)
    df = apply_structural_missing(df, rules)
    return df[list(output_cols)]


def harmonize_evs_trend(df: pd.DataFrame, output_cols: Sequence[str], rules: SyntaxRules) -> pd.DataFrame:
    df = df.copy()
    ren = {}
    for c in df.columns:
        cf = c.casefold()
        if cf == "s002vs":
            ren[c] = "S002VS"
        elif cf == "s002evs":
            ren[c] = "S002EVS"
        elif cf == "x026_01":
            ren[c] = "X026_01"
    df = df.rename(columns=ren)
    df = canonicalize_existing(df, output_cols)
    if "S001" not in df.columns:
        df["S001"] = 1
    else:
        s = pd.to_numeric(df["S001"], errors="coerce")
        if s.notna().any() and not s.dropna().eq(1).all():
            raise ValueError("EVS Trend chunk contains S001 values other than 1")
    df = _ensure_columns(df, output_cols, string_cols=rules.evs_only_string)
    df = apply_structural_missing(df, rules)
    return df[list(output_cols)]


def _coalesce_series(df: pd.DataFrame, candidates: Sequence[str]) -> Optional[pd.Series]:
    s = None
    for c in candidates:
        if c not in df.columns:
            continue
        if s is None:
            s = df[c].copy()
        else:
            # Treat empty strings as missing for coalescing.
            if s.dtype == object:
                missing = s.isna() | s.astype(str).str.strip().eq("")
            else:
                missing = s.isna()
            s = s.where(~missing, df[c])
    return s


def harmonize_joint_evs5(df: pd.DataFrame, output_cols: Sequence[str], rules: SyntaxRules) -> pd.DataFrame:
    """Extract/harmonize EVS5 only from ZA7505-style joint data."""
    df = df.copy()
    if "study" not in df.columns:
        raise ValueError("Joint EVS/WVS input lacks `study`")
    study = pd.to_numeric(df["study"], errors="coerce")
    df = df.loc[study.eq(1)].copy()  # CRITICAL: exclude embedded WVS7 to prevent duplication.
    if df.empty:
        return pd.DataFrame(columns=output_cols)

    out = pd.DataFrame(index=df.index)
    target_by_cf = {x.casefold(): x for x in output_cols}

    # Direct common-name variables first.
    for c in df.columns:
        dest = target_by_cf.get(c.casefold())
        if dest and dest not in out.columns:
            out[dest] = df[c]

    # Explicit aliases.
    for src, dest_requested in JOINT_EVS5_ALIASES.items():
        if src not in df.columns:
            continue
        dest = target_by_cf.get(dest_requested.casefold())
        if dest:
            out[dest] = df[src]

    # DOI for EVS should prefer the GESIS identifier; WVSA is a fallback only.
    dest_doi = target_by_cf.get("doi")
    if dest_doi:
        s = _coalesce_series(df, ["doi_gesis", "doi_wvsa"])
        if s is not None:
            out[dest_doi] = s

    # Common chronology: EVS5 belongs to the 2017-2022 combined period, aligned
    # with WVS7 in the IVS chronology. We do not overwrite S002EVS (=5).
    if "S002VS" in output_cols:
        out["S002VS"] = 7

    # `study` is 1 for EVS; ensure exactly that after aliases.
    if "S001" in output_cols:
        out["S001"] = 1

    out = _ensure_columns(out, output_cols, string_cols=rules.evs_only_string)
    out = apply_structural_missing(out, rules)
    return out[list(output_cols)]


# ---------------------------------------------------------------------------
# Streaming / output / QC
# ---------------------------------------------------------------------------

def iter_stata(path: Path, columns: Sequence[str], chunksize: int) -> Iterator[pd.DataFrame]:
    cols = list(dict.fromkeys(columns))
    with pd.read_stata(path, iterator=True, convert_categoricals=False, columns=cols) as r:
        while True:
            try:
                chunk = r.get_chunk(chunksize)
            except StopIteration:
                break
            if chunk is None or chunk.empty:
                break
            yield chunk


def update_qc(qc: QCState, df: pd.DataFrame, source: str) -> None:
    n = len(df)
    qc.rows += n
    qc.source_rows[source] += n
    if "S003" in df.columns:
        qc.countries.update(pd.to_numeric(df["S003"], errors="coerce").dropna().tolist())
    if all(c in df.columns for c in ["S001", "S002VS", "S020"]):
        sub = df[["S001", "S002VS", "S020"]].copy()
        for tup, cnt in sub.value_counts(dropna=False).items():
            qc.wave_year_counts[tuple(tup)] += int(cnt)
    for c in PAPER_CORE:
        if c not in df.columns:
            continue
        s = df[c]
        qc.core_total[c] += len(s)
        qc.core_na[c] += int(s.isna().sum())
        num = pd.to_numeric(s, errors="coerce")
        qc.core_negative[c] += int(num.lt(0).sum())


def output_kind(path: Path) -> str:
    name = path.name.lower()
    if name.endswith(".csv.gz") or name.endswith(".csv"):
        return "csv"
    if name.endswith(".dta"):
        return "dta"
    raise ValueError("Output must end in .csv, .csv.gz, or .dta")


def _open_csv_output(path: Path):
    if path.name.lower().endswith(".gz"):
        return gzip.open(path, "wt", encoding="utf-8", newline="")
    return path.open("w", encoding="utf-8", newline="")


def write_qc_files(output: Path, qc: QCState, manifest: Dict[str, object]) -> None:
    stem = str(output)
    manifest_path = Path(stem + ".manifest.json")
    wave_path = Path(stem + ".qc_wave_year_counts.csv")
    missing_path = Path(stem + ".qc_core_missing.csv")

    manifest.update({
        "output_rows": qc.rows,
        "source_rows": dict(qc.source_rows),
        "unique_country_codes_S003": len(qc.countries),
    })
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False, default=str), encoding="utf-8")

    with wave_path.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["S001", "S002VS", "S020", "n"])
        for (s001, wave, year), n in sorted(qc.wave_year_counts.items(), key=lambda x: tuple(str(v) for v in x[0])):
            w.writerow([s001, wave, year, n])

    with missing_path.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["variable", "n", "n_na", "n_negative_missing_codes", "share_na", "share_negative"])
        for c in PAPER_CORE:
            n = qc.core_total.get(c, 0)
            na = qc.core_na.get(c, 0)
            neg = qc.core_negative.get(c, 0)
            w.writerow([c, n, na, neg, (na / n if n else None), (neg / n if n else None)])


def dataframe_variable_labels(output_cols: Sequence[str], labels_cf: Mapping[str, str]) -> Dict[str, str]:
    out = {}
    for c in output_cols:
        lab = labels_cf.get(c.casefold())
        if lab:
            # Stata variable labels max at 80 chars in pandas writer.
            out[c] = lab[:80]
    return out


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def parse_args(argv=None):
    p = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter, description=__doc__)
    p.add_argument("--evs", required=True, type=Path, help="EVS Trend .dta (canonical), or ZA7505 joint .dta with --allow-partial-joint")
    p.add_argument("--wvs", required=True, type=Path, help="WVS Trend .dta")
    p.add_argument("--merge-syntax", required=True, type=Path, help="Official EVS_WVS_Merge Syntax_stata.do")
    p.add_argument("--dictionary", type=Path, help="Common EVS/WVS Dictionary IVS .xlsx; used for schema validation/labels")
    p.add_argument("--countries", type=Path, help="Participating-countries .xlsx; used for recent-wave QC")
    p.add_argument("--output", required=True, type=Path, help="Output .csv, .csv.gz, or .dta")
    p.add_argument("--allow-partial-joint", action="store_true", help="Allow ZA7505 joint file by extracting EVS5 only; output is incomplete IVS")
    p.add_argument("--core-only", action="store_true", help="Write only variables required by the cultural-values replication")
    p.add_argument("--chunksize", type=int, default=25000, help="Rows per streaming chunk (default 25000)")
    p.add_argument("--overwrite", action="store_true")
    return p.parse_args(argv)


def main(argv=None) -> int:
    a = parse_args(argv)
    for path in [a.evs, a.wvs, a.merge_syntax]:
        if not path.exists():
            raise FileNotFoundError(path)
    if a.dictionary and not a.dictionary.exists():
        raise FileNotFoundError(a.dictionary)
    if a.countries and not a.countries.exists():
        raise FileNotFoundError(a.countries)
    if a.output.exists() and not a.overwrite:
        raise FileExistsError(f"Output already exists: {a.output}. Use --overwrite to replace it.")
    a.output.parent.mkdir(parents=True, exist_ok=True)

    rules = parse_merge_syntax(a.merge_syntax)
    canonical_keep = {c.casefold(): c for c in rules.keep}
    output_cols = [canonical_keep.get(c.casefold(), c) for c in PAPER_CORE] if a.core_only else list(rules.keep)
    # Keep order and de-duplicate core aliases.
    output_cols = list(dict.fromkeys(output_cols))

    dictionary_info = None
    labels_cf: Dict[str, str] = {}
    warnings: List[str] = []
    if a.dictionary:
        dict_canonical, labels_cf, dictionary_info = read_dictionary(a.dictionary)
        keep_cf = {c.casefold() for c in rules.keep}
        dict_cf = set(dict_canonical)
        missing = sorted(keep_cf - dict_cf)
        extra = sorted(dict_cf - keep_cf)
        # The supplied common dictionary has a duplicate studyno row and no versn_w row;
        # these are documented rather than silently treated as fatal.
        if extra:
            raise ValueError(f"Dictionary contains IVS variables not in official keep list: {extra[:20]}")
        unexpected_missing = [x for x in missing if x != "versn_w"]
        if unexpected_missing:
            raise ValueError(f"Official keep variables missing from dictionary: {unexpected_missing[:20]}")
        if "versn_w" in missing:
            warnings.append("Common dictionary validation: official keep list includes versn_w, which is not separately flagged IVS in the supplied dictionary.")

    participation = read_participation_reference(a.countries) if a.countries else None

    evs_cols = stata_columns(a.evs)
    wvs_cols = stata_columns(a.wvs)
    evs_type = classify_evs_source(evs_cols)
    if evs_type == "unknown":
        raise ValueError(
            "Could not classify EVS input. The canonical source should be an EVS Trend File; "
            "ZA7505-style joint files are also recognized in guarded partial mode."
        )
    if evs_type == "joint_2017_2022" and not a.allow_partial_joint:
        raise ValueError(
            "The supplied EVS file is a Joint EVS/WVS 2017-2022 file (ZA7505-style), not the EVS Trend File expected by the official merge syntax. "
            "It contains EVS5 + WVS7 only. Appending it wholesale would duplicate WVS7 and omit EVS1-4. "
            "For a full IVS, supply the EVS Trend File (e.g. ZA7503-compatible). If you intentionally want WVS1-7 + EVS5 only, rerun with --allow-partial-joint."
        )

    if evs_type == "joint_2017_2022":
        warnings.append(
            "PARTIAL DATASET: EVS input is Joint EVS/WVS 2017-2022. Only study==1 (EVS5) is retained; embedded WVS7 is discarded to prevent duplication. EVS1-4 are absent."
        )

    # Validate WVS signature.
    wcf = casefold_map(wvs_cols)
    for req in ["S001", "S002VS", "S003", "S020", "A008"]:
        if req.casefold() not in wcf:
            raise ValueError(f"WVS input missing required variable {req}")

    manifest: Dict[str, object] = {
        "script": Path(__file__).name,
        "python": sys.version,
        "pandas": pd.__version__,
        "evs_source_type": evs_type,
        "partial": evs_type == "joint_2017_2022",
        "core_only": a.core_only,
        "schema_columns": len(output_cols),
        "official_keep_columns": len(rules.keep),
        "warnings": warnings,
        "input_files": {
            "evs": {"path": str(a.evs), "sha256": sha256(a.evs), "columns": len(evs_cols)},
            "wvs": {"path": str(a.wvs), "sha256": sha256(a.wvs), "columns": len(wvs_cols)},
            "merge_syntax": {"path": str(a.merge_syntax), "sha256": sha256(a.merge_syntax)},
        },
        "dictionary_validation": dictionary_info,
        "participation_reference": participation,
        "missing_value_policy": "Preserve -1..-5 codes; apply official structural -4/-3 rules; do not convert to Stata .a-.e.",
    }
    if a.dictionary:
        manifest["input_files"]["dictionary"] = {"path": str(a.dictionary), "sha256": sha256(a.dictionary)}
    if a.countries:
        manifest["input_files"]["countries"] = {"path": str(a.countries), "sha256": sha256(a.countries)}

    # Source columns needed. Reading only required columns materially reduces memory in --core-only mode.
    out_cf = {c.casefold() for c in output_cols}
    wvs_read = [c for c in wvs_cols if c.casefold() in out_cf or c.casefold() == "s002"]
    if "S001" not in wvs_read and "S001" in wvs_cols:
        wvs_read.append("S001")

    if evs_type == "evs_trend":
        evs_read = [c for c in evs_cols if c.casefold() in out_cf]
        # Need source-specific lower-case names/case variants.
        for c in evs_cols:
            if c.casefold() in {"s001", "s002vs", "s002evs", "x026_01"} and c not in evs_read:
                evs_read.append(c)
    else:
        alias_sources = set(JOINT_EVS5_ALIASES) | {"doi_gesis", "doi_wvsa", "study"}
        evs_read = [c for c in evs_cols if c.casefold() in out_cf or c in alias_sources]

    qc = QCState()
    kind = output_kind(a.output)

    def transformed_evs() -> Iterator[pd.DataFrame]:
        for chunk in iter_stata(a.evs, evs_read, a.chunksize):
            if evs_type == "evs_trend":
                x = harmonize_evs_trend(chunk, output_cols, rules)
            else:
                x = harmonize_joint_evs5(chunk, output_cols, rules)
            if not x.empty:
                yield x

    def transformed_wvs() -> Iterator[pd.DataFrame]:
        for chunk in iter_stata(a.wvs, wvs_read, a.chunksize):
            x = harmonize_wvs(chunk, output_cols, rules)
            yield x

    if kind == "csv":
        with _open_csv_output(a.output) as f:
            first = True
            # Match official Stata append order: EVS first, WVS second.
            for source, gen in [("EVS", transformed_evs()), ("WVS", transformed_wvs())]:
                for x in gen:
                    update_qc(qc, x, source)
                    x.to_csv(f, index=False, header=first)
                    first = False
    else:
        # DTA is necessarily in-memory with pandas' writer.
        warnings.append("DTA output uses pandas writer and requires the complete harmonized table in memory; original source value-label sets are not fully reproduced.")
        parts = []
        for source, gen in [("EVS", transformed_evs()), ("WVS", transformed_wvs())]:
            for x in gen:
                update_qc(qc, x, source)
                parts.append(x)
        merged = pd.concat(parts, ignore_index=True)
        # Stata writer cannot accept arbitrary object mixtures; normalize object columns to strings.
        for c in merged.select_dtypes(include=["object"]).columns:
            merged[c] = merged[c].where(merged[c].notna(), None)
        merged.to_stata(
            a.output,
            write_index=False,
            version=118,
            variable_labels=dataframe_variable_labels(output_cols, labels_cf),
        )

    # High-value assertions.
    if qc.source_rows.get("WVS", 0) <= 0 or qc.source_rows.get("EVS", 0) <= 0:
        raise RuntimeError(f"Merge produced no cases for one source: {dict(qc.source_rows)}")

    # For the supplied joint reference, the participation workbook says 36 EVS5 and 66 WVS7 countries.
    # Verify the source files directly when those reference counts are available.
    if participation and evs_type == "joint_2017_2022":
        try:
            j = pd.read_stata(a.evs, columns=["study", "cntry"], convert_categoricals=False)
            evs5_n = j.loc[pd.to_numeric(j["study"], errors="coerce").eq(1), "cntry"].nunique(dropna=True)
            wvs7_n_joint = j.loc[pd.to_numeric(j["study"], errors="coerce").eq(2), "cntry"].nunique(dropna=True)
            exp_e = participation.get("expected_recent_evs_countries")
            exp_w = participation.get("expected_recent_wvs_countries")
            manifest["recent_wave_source_check"] = {
                "joint_file_evs5_unique_countries": int(evs5_n),
                "joint_file_wvs7_unique_countries": int(wvs7_n_joint),
                "reference_evs5_countries": exp_e,
                "reference_wvs7_countries": exp_w,
                "matches_reference": (exp_e in (None, evs5_n)) and (exp_w in (None, wvs7_n_joint)),
            }
            if exp_e is not None and evs5_n != exp_e:
                warnings.append(f"EVS5 country count {evs5_n} does not match participation reference {exp_e}.")
            if exp_w is not None and wvs7_n_joint != exp_w:
                warnings.append(f"Joint-file WVS7 country count {wvs7_n_joint} does not match participation reference {exp_w}.")
        except Exception as e:
            warnings.append(f"Recent-wave participation cross-check could not be completed: {e}")

    manifest["warnings"] = warnings
    write_qc_files(a.output, qc, manifest)

    print(f"Wrote {a.output}")
    print(f"Rows: {qc.rows:,} (EVS={qc.source_rows.get('EVS',0):,}; WVS={qc.source_rows.get('WVS',0):,})")
    print(f"Columns: {len(output_cols)}")
    print(f"EVS input type: {evs_type}")
    if warnings:
        print("Warnings:")
        for w in warnings:
            print(" -", w)
    print("QC manifest:", str(a.output) + ".manifest.json")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        raise
