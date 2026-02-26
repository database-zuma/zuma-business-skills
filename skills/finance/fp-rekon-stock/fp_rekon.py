#!/usr/bin/env python3
"""
fp_rekon.py — Faktur Pajak → Google Sheets Reconciliation
Skill: fp-rekon-stock | Zuma Business Skills

Usage:
    python3 fp_rekon.py <path_pdf>
    python3 fp_rekon.py <path_pdf> --sheet-id SHEET_ID --tab "Februari 2026"
    python3 fp_rekon.py <path_pdf> --dry-run
    python3 fp_rekon.py /path/to/folder/   # batch mode: all PDFs in folder
"""

from __future__ import annotations
from typing import Optional, Tuple
import sys
import os
import re
import json
import hashlib
import shutil
import argparse
import subprocess
from pathlib import Path
from datetime import datetime

try:
    import pdfplumber
except ImportError:
    print("ERROR: pdfplumber not installed. Run: pip3 install pdfplumber")
    sys.exit(1)


# ── Constants ──────────────────────────────────────────────────────────────────


def _find_gog() -> str:
    """Find gog CLI dynamically. Checks PATH first, then known Homebrew paths."""
    # 1. Check if gog is on PATH
    gog_path = shutil.which("gog")
    if gog_path:
        return gog_path
    # 2. Check Homebrew Cellar (any version)
    cellar = Path.home() / "homebrew" / "Cellar" / "gogcli"
    if cellar.exists():
        versions = sorted(cellar.iterdir(), reverse=True)
        for v in versions:
            candidate = v / "bin" / "gog"
            if candidate.exists():
                return str(candidate)
    # 3. Fallback: common paths
    for fallback in ["/usr/local/bin/gog", "/opt/homebrew/bin/gog"]:
        if Path(fallback).exists():
            return fallback
    # 4. Give up with helpful error
    print("ERROR: gog CLI not found. Install via: brew install gogcli")
    print("  Searched: PATH, ~/homebrew/Cellar/gogcli/*/bin/gog, /usr/local/bin/gog")
    sys.exit(1)


GOG = _find_gog()
ACCOUNT = "harveywayan@gmail.com"
DEFAULT_SHEET_ID = "1OEEtXsv3kTnGkgVuKA_Dma-6gpVwYLaLa9g5tOLMSgA"
DEFAULT_UNIT = "PAIRS"

# Audit log location
AUDIT_LOG_DIR = Path(__file__).parent / "audit_logs"

MONTHS_ID = {
    "Januari": 1,
    "Februari": 2,
    "Maret": 3,
    "April": 4,
    "Mei": 5,
    "Juni": 6,
    "Juli": 7,
    "Agustus": 8,
    "September": 9,
    "Oktober": 10,
    "November": 11,
    "Desember": 12,
}

# Updated to match actual Google Sheets column structure (Jan/Feb 2026+)
HEADER_ROW = [
    "SUPPLIER",
    "RINCIAN",
    "Qty",
    "Satuan",
    "Tanggal Invoice",
    "NO INVOICE",
    "Tgl Faktur Pajak",
    "No Seri Faktur Pajak",
    "Harga/Qty",
    "DPP",
    "PPN-M",
    "Jumlah",
    "Status",
    "Nomor Seri Internal",
]


# ── Helpers ────────────────────────────────────────────────────────────────────


def parse_rp(s: str) -> float:
    """Convert Indonesian Rupiah string '40.540,54' → 40540.54"""
    return float(s.replace(".", "").replace(",", "."))


def date_id_to_dmy(date_str: str) -> str:
    """'22 Januari 2026' → '22/01/2026'"""
    parts = date_str.strip().split()
    if len(parts) != 3:
        return date_str
    day, month_id, year = parts
    month = MONTHS_ID.get(month_id, 0)
    if not month:
        return date_str
    return f"{int(day):02d}/{month:02d}/{year}"


def tab_from_date(date_dmy: str) -> str:
    """'22/01/2026' → 'Januari 2026'"""
    parts = date_dmy.split("/")
    if len(parts) != 3:
        return "Sheet1"
    _, month_num, year = parts
    id_months = {v: k for k, v in MONTHS_ID.items()}
    return f"{id_months.get(int(month_num), 'Unknown')} {year}"


def row_hash(row: list) -> str:
    """Generate a dedup hash from key fields: supplier + rincian + qty + tanggal + no_seri_fp + dpp."""
    key = "|".join([row[0], row[1], row[2], row[4], row[7], row[9]])
    return hashlib.md5(key.encode()).hexdigest()


# ── Audit Trail ────────────────────────────────────────────────────────────────


def write_audit_log(
    pdf_path: str,
    parsed: dict,
    tab: str,
    sheet_id: str,
    entry_type: str,
    rows_appended: int,
    dry_run: bool,
):
    """Write a JSON audit log for each run."""
    AUDIT_LOG_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "pdf_file": str(pdf_path),
        "sheet_id": sheet_id,
        "tab": tab,
        "entry_type": entry_type,
        "dry_run": dry_run,
        "supplier": parsed.get("supplier", ""),
        "npwp": parsed.get("npwp", ""),
        "no_seri_fp": parsed.get("no_seri_fp", ""),
        "tanggal": parsed.get("tanggal", ""),
        "referensi": parsed.get("referensi", ""),
        "dpp_total": parsed.get("dpp_total"),
        "ppn_total": parsed.get("ppn_total"),
        "items_count": len(parsed.get("items", [])),
        "rows_appended": rows_appended,
        "warnings": parsed.get("_warnings", []),
    }
    log_file = AUDIT_LOG_DIR / f"{timestamp}_{Path(pdf_path).stem}.json"
    with open(log_file, "w") as f:
        json.dump(log_entry, f, indent=2, ensure_ascii=False)
    print(f"  📝 Audit log: {log_file.name}")


# ── PDF Parsing ────────────────────────────────────────────────────────────────


def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract all text from PDF using pdfplumber."""
    full_text = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                full_text.append(text)
    return "\n".join(full_text)


def parse_faktur_pajak(text: str) -> dict:
    """Parse Faktur Pajak fields from extracted PDF text.

    Returns dict with parsed fields + '_warnings' list for any extraction issues.
    """
    result = {}
    warnings = []

    # ── Supplier (Pengusaha Kena Pajak section) ────────────────────────────
    pkp_match = re.search(
        r"Pengusaha Kena Pajak:.*?Nama\s*:\s*([A-Z][A-Z0-9\s&.,'-]+?)(?:\n|Alamat)",
        text,
        re.DOTALL,
    )
    if pkp_match:
        result["supplier"] = pkp_match.group(1).strip()
    else:
        m = re.search(r"^Nama\s*:\s*([A-Z][A-Z0-9\s&.,'-]+?)$", text, re.MULTILINE)
        result["supplier"] = m.group(1).strip() if m else "UNKNOWN"
        if result["supplier"] == "UNKNOWN":
            warnings.append("⚠️ Supplier name not found — defaulting to UNKNOWN")

    # ── NPWP (Seller) ─────────────────────────────────────────────────────
    # Try 16-digit (Coretax) first, then 15-digit (e-Faktur legacy)
    npwp_match = re.search(r"NPWP\s*:\s*(\d[\d.\-]{14,20})", text)
    if npwp_match:
        raw_npwp = re.sub(r"[.\-]", "", npwp_match.group(1))
        result["npwp"] = raw_npwp
    else:
        result["npwp"] = ""
        warnings.append("⚠️ NPWP not found in PDF")

    # ── Nomor Seri Faktur Pajak ────────────────────────────────────────────
    m = re.search(r"Kode dan Nomor Seri Faktur Pajak:\s*(\d+)", text)
    result["no_seri_fp"] = m.group(1).strip() if m else ""
    if not result["no_seri_fp"]:
        warnings.append("⚠️ No Seri Faktur Pajak not found")

    # ── Tanggal (last date occurrence near closing signature) ──────────────
    dates = re.findall(
        r"(\d{1,2}\s+(?:" + "|".join(MONTHS_ID.keys()) + r")\s+\d{4})", text
    )
    if dates:
        result["tanggal_raw"] = dates[-1]
        result["tanggal"] = date_id_to_dmy(dates[-1])
    else:
        result["tanggal_raw"] = ""
        result["tanggal"] = ""
        warnings.append("⚠️ Tanggal Faktur not found")

    # ── Referensi ──────────────────────────────────────────────────────────
    m = re.search(r"Referensi:\s*(DS\d+)", text)
    result["referensi"] = m.group(1).strip() if m else ""
    if not result["referensi"]:
        warnings.append("⚠️ Referensi (DS number) not found")

    # ── DPP total — baca langsung dari PDF (bukan hitung) ─────────────────
    m = re.search(r"Dasar Pengenaan Pajak\s+([\d.,]+)", text)
    dpp_total = int(parse_rp(m.group(1))) if m else None
    result["dpp_total"] = dpp_total
    if dpp_total is None:
        warnings.append("🔴 DPP Total not found — cannot allocate item amounts")

    # ── PPN total — baca langsung dari PDF (bukan hitung) ─────────────────
    # Gunakan "Jumlah PPN " (dengan spasi) agar tidak match "Jumlah PPnBM"
    m = re.search(r"Jumlah PPN\s.*?([\d.,]+)", text)
    ppn_total = int(parse_rp(m.group(1))) if m else None
    result["ppn_total"] = ppn_total
    if ppn_total is None:
        warnings.append("🔴 PPN Total not found — cannot allocate item amounts")

    # ── PPN rate sanity check ─────────────────────────────────────────────
    if dpp_total and ppn_total and dpp_total > 0:
        actual_rate = ppn_total / dpp_total
        if abs(actual_rate - 0.11) > 0.005 and abs(actual_rate - 0.12) > 0.005:
            warnings.append(
                f"⚠️ PPN rate sanity check: {actual_rate:.4f} "
                f"({ppn_total:,}/{dpp_total:,}) — expected ~11% or ~12%"
            )

    # ── Items: parse per-line (Rp harga x qty) ────────────────────────────
    lines = text.splitlines()
    items = []

    for i, line in enumerate(lines):
        rp_match = re.search(r"Rp\s*([\d,.]+)\s*x\s*([\d,.]+)", line)
        if rp_match:
            harga = parse_rp(rp_match.group(1))
            qty = parse_rp(rp_match.group(2))

            # Item name = nearest non-header line above
            item_name = ""
            for j in range(i - 1, max(i - 5, -1), -1):
                candidate = lines[j].strip()
                if candidate and not re.match(
                    r"^(Rp|No\.|Nomor|Alamat|Nama|NPWP|Kode|Faktur|Pembeli|Pengusaha|Harga|Potongan|PPnBM|Jumlah|Sesuai|\d+\s)",
                    candidate,
                ):
                    item_name = candidate
                    break

            items.append(
                {
                    "name": item_name,
                    "harga": harga,
                    "qty": int(qty),
                    "harga_jual": harga * qty,  # subtotal item ini
                    "harga_qty_col": int(harga),  # kolom Harga/Qty di sheet
                    "dpp": 0,
                    "ppn": 0,
                    "jumlah": 0,
                }
            )

    if not items:
        warnings.append(
            "🔴 No items found — check PDF format (expected 'Rp X x Y' pattern)"
        )

    # ── Proportional DPP + PPN allocation per item ─────────────────────────
    # DPP/PPN read from PDF (not calculated) to prevent rounding errors
    # Multi-item: proportional allocation based on harga_jual per item
    if items and dpp_total is not None and ppn_total is not None:
        harga_jual_total = sum(item["harga_jual"] for item in items)
        ppn_rate = ppn_total / dpp_total if dpp_total > 0 else 0

        dpp_remaining = dpp_total
        ppn_remaining = ppn_total

        for idx, item in enumerate(items):
            is_last = idx == len(items) - 1
            if is_last:
                # Last item absorbs remainder → hindari drift rounding
                item["dpp"] = dpp_remaining
                item["ppn"] = ppn_remaining
            else:
                ratio = item["harga_jual"] / harga_jual_total
                item["dpp"] = round(dpp_total * ratio)
                item["ppn"] = round(item["dpp"] * ppn_rate)
                dpp_remaining -= item["dpp"]
                ppn_remaining -= item["ppn"]

            item["jumlah"] = item["dpp"] + item["ppn"]

    result["items"] = items
    result["_warnings"] = warnings
    return result


# ── Google Sheets ──────────────────────────────────────────────────────────────


def gog_run(args: list, capture=True) -> tuple[int, str, str]:
    """Run gog CLI command."""
    cmd = [GOG] + args + ["--account", ACCOUNT]
    r = subprocess.run(cmd, capture_output=capture, text=True)
    return r.returncode, r.stdout, r.stderr


def tab_exists(sheet_id: str, tab: str) -> bool:
    """Check if a tab exists by trying to read A1."""
    code, out, err = gog_run(["sheets", "get", sheet_id, f"'{tab}'!A1"])
    return code == 0


def get_existing_hashes(sheet_id: str, tab: str) -> set[str]:
    """Read existing rows from sheet and compute hashes for dedup.

    Returns set of row_hash values for all existing data rows.
    """
    hashes = set()
    code, out, err = gog_run(["sheets", "get", sheet_id, f"'{tab}'!A:N", "--json"])
    if code != 0:
        return hashes
    try:
        data = json.loads(out)
        rows = data if isinstance(data, list) else data.get("values", [])
        for row in rows[1:]:  # skip header
            if len(row) >= 10 and row[0]:  # has enough columns and supplier
                # Pad row to 14 cols if short
                padded = row + [""] * (14 - len(row))
                hashes.add(row_hash(padded))
    except (json.JSONDecodeError, IndexError, KeyError):
        pass  # If we can't read, skip dedup (will just append)
    return hashes


def append_rows(sheet_id: str, tab: str, rows: list[list]) -> bool:
    """Append rows to a sheet tab using --values-json."""
    values_json = json.dumps(rows)
    code, out, err = gog_run(
        [
            "sheets",
            "append",
            sheet_id,
            f"'{tab}'!A:N",
            "--values-json",
            values_json,
            "--input",
            "USER_ENTERED",
        ]
    )
    if code != 0:
        print(f"ERROR appending rows: {err}")
        return False
    print(f"  ✓ Appended {len(rows)} row(s) to '{tab}'")
    return True


def push_to_sheets(
    parsed: dict,
    sheet_id: str,
    tab: str,
    entry_type: str = "stock",
    dry_run: bool = False,
) -> int:
    """Push parsed FP data to Google Sheets. Returns number of rows appended."""
    rows = []
    for item in parsed["items"]:
        row = [
            parsed["supplier"],  # A: SUPPLIER
            item["name"],  # B: RINCIAN
            str(item["qty"]),  # C: Qty
            DEFAULT_UNIT,  # D: Satuan
            parsed["tanggal"],  # E: Tanggal Invoice
            parsed["referensi"],  # F: NO INVOICE
            parsed["tanggal"],  # G: Tgl Faktur Pajak
            parsed["no_seri_fp"],  # H: No Seri Faktur Pajak
            str(item["harga_qty_col"]),  # I: Harga/Qty
            str(item["dpp"]),  # J: DPP
            str(item["ppn"]),  # K: PPN-M
            str(item["jumlah"]),  # L: Jumlah
            entry_type,  # M: Status (stock/non-stock)
            "",  # N: Nomor Seri Internal (filled manually)
        ]
        rows.append(row)

    print(f"\n📋 Rows to append (tab: '{tab}'):")
    print(
        f"{'SUPPLIER':<25} {'RINCIAN':<35} {'Qty':>5} {'Harga/Qty':>12} {'DPP':>12} {'PPN-M':>10} {'Jumlah':>12}"
    )
    print("-" * 120)
    for row in rows:
        print(
            f"{row[0]:<25} {row[1]:<35} {row[2]:>5} {row[8]:>12} {row[9]:>12} {row[10]:>10} {row[11]:>12}"
        )

    if dry_run:
        print("\n[DRY RUN] Skipping Google Sheets write.")
        return len(rows)

    # ── Duplicate detection ────────────────────────────────────────────────
    print(f"\n🔍 Checking tab '{tab}'...")
    if not tab_exists(sheet_id, tab):
        print(f"  Tab not found. Creating with header row...")
        if not append_rows(sheet_id, tab, [HEADER_ROW]):
            return 0
        # New tab, no existing data to dedup against
        if append_rows(sheet_id, tab, rows):
            return len(rows)
        return 0

    # Tab exists — check for duplicates
    print(f"  🔎 Checking for duplicates...")
    existing_hashes = get_existing_hashes(sheet_id, tab)
    new_rows = []
    skipped = 0
    for row in rows:
        h = row_hash(row)
        if h in existing_hashes:
            skipped += 1
            print(f"  ⏭️  Duplicate skipped: {row[0]} | {row[1]} | qty={row[2]}")
        else:
            new_rows.append(row)
            existing_hashes.add(h)  # prevent intra-batch dupes

    if skipped:
        print(f"  ℹ️  {skipped} duplicate row(s) skipped")

    if not new_rows:
        print(f"  ✅ All rows already exist. Nothing to append.")
        return 0

    if append_rows(sheet_id, tab, new_rows):
        return len(new_rows)
    return 0


# ── Batch Processing ──────────────────────────────────────────────────────────


def find_pdfs(path: Path) -> list[Path]:
    """Find all PDF files in a directory (non-recursive)."""
    if path.is_file() and path.suffix.lower() == ".pdf":
        return [path]
    if path.is_dir():
        pdfs = sorted(path.glob("*.pdf"))
        if not pdfs:
            print(f"⚠️  No PDF files found in {path}")
        return pdfs
    print(f"ERROR: {path} is not a PDF file or directory")
    sys.exit(1)


# ── Main ───────────────────────────────────────────────────────────────────────


def process_single_pdf(
    pdf_path: Path,
    sheet_id: str,
    tab_override: Optional[str],
    entry_type: str,
    dry_run: bool,
) -> Tuple[bool, dict]:
    """Process a single PDF. Returns (success, parsed_data)."""
    print(f"\n{'=' * 80}")
    print(f"📄 Parsing: {pdf_path.name}")
    print(f"{'=' * 80}")

    text = extract_text_from_pdf(str(pdf_path))
    parsed = parse_faktur_pajak(text)

    # ── Print warnings ─────────────────────────────────────────────────────
    if parsed["_warnings"]:
        print(f"\n⚠️  Warnings ({len(parsed['_warnings'])}):")
        for w in parsed["_warnings"]:
            print(f"  {w}")

    # ── Print parsed summary ───────────────────────────────────────────────
    print(f"\n🔎 Parsed Faktur Pajak:")
    print(f"  Supplier     : {parsed['supplier']}")
    print(f"  NPWP         : {parsed['npwp'] or '(not found)'}")
    print(f"  No Seri FP   : {parsed['no_seri_fp'] or '(not found)'}")
    print(f"  Tanggal      : {parsed['tanggal']} ({parsed['tanggal_raw']})")
    print(f"  Referensi    : {parsed['referensi'] or '(not found)'}")
    print(
        f"  DPP Total    : {parsed['dpp_total']:,}"
        if parsed["dpp_total"]
        else "  DPP Total    : -"
    )
    print(
        f"  PPN Total    : {parsed['ppn_total']:,}"
        if parsed["ppn_total"]
        else "  PPN Total    : -"
    )
    if parsed["dpp_total"] and parsed["ppn_total"]:
        rate = parsed["ppn_total"] / parsed["dpp_total"] * 100
        print(f"  PPN Rate     : {rate:.2f}%")
    print(f"  Items        : {len(parsed['items'])}")
    for i, item in enumerate(parsed["items"], 1):
        print(f"    {i}. {item['name']}")
        print(
            f"       qty={item['qty']} | harga={item['harga']:,.2f} | dpp={item['dpp']:,} | ppn={item['ppn']:,} | jumlah={item['jumlah']:,}"
        )

    if not parsed["items"]:
        print("\n⚠️  No items found. Check PDF format.")
        write_audit_log(str(pdf_path), parsed, "", sheet_id, entry_type, 0, dry_run)
        return False, parsed

    tab = tab_override or tab_from_date(parsed["tanggal"])
    print(f"\n📊 Target sheet : {sheet_id}")
    print(f"   Tab          : {tab}")
    print(f"   Type         : {entry_type}")

    rows_appended = push_to_sheets(
        parsed, sheet_id, tab, entry_type=entry_type, dry_run=dry_run
    )

    write_audit_log(
        str(pdf_path), parsed, tab, sheet_id, entry_type, rows_appended, dry_run
    )

    return rows_appended > 0 or dry_run, parsed


def main():
    parser = argparse.ArgumentParser(
        description="Parse Faktur Pajak PDF(s) and push to Google Sheets"
    )
    parser.add_argument("pdf", help="Path to Faktur Pajak PDF or directory of PDFs")
    parser.add_argument("--sheet-id", default=DEFAULT_SHEET_ID, help="Google Sheets ID")
    parser.add_argument(
        "--tab",
        default=None,
        help="Sheet tab name (default: derived from invoice date)",
    )
    parser.add_argument(
        "--type", default="stock", help="Value for Status column (default: stock)"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Parse only, don't write to Sheets"
    )
    args = parser.parse_args()

    pdf_path = Path(args.pdf)
    if not pdf_path.exists():
        print(f"ERROR: Path not found: {pdf_path}")
        sys.exit(1)

    pdfs = find_pdfs(pdf_path)
    if not pdfs:
        sys.exit(1)

    # ── Process PDFs ───────────────────────────────────────────────────────
    total = len(pdfs)
    success = 0
    failed = 0

    if total > 1:
        print(f"\n📁 Batch mode: {total} PDF(s) found in {pdf_path}")

    for pdf in pdfs:
        ok, _ = process_single_pdf(
            pdf, args.sheet_id, args.tab, args.type, args.dry_run
        )
        if ok:
            success += 1
        else:
            failed += 1

    # ── Summary ────────────────────────────────────────────────────────────
    if total > 1:
        print(f"\n{'=' * 80}")
        print(f"📊 Batch Summary: {success}/{total} succeeded, {failed} failed")
        print(f"{'=' * 80}")

    if success > 0:
        print(
            f"\n✅ Done! Sheet: https://docs.google.com/spreadsheets/d/{args.sheet_id}"
        )
    if failed > 0:
        print(f"\n⚠️  {failed} PDF(s) had issues. Check audit logs in: {AUDIT_LOG_DIR}")
        sys.exit(1)


if __name__ == "__main__":
    main()
