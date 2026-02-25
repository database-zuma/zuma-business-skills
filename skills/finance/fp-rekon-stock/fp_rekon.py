#!/usr/bin/env python3
"""
fp_rekon.py — Faktur Pajak → Google Sheets Reconciliation
Skill: fp-rekon-stock | Zuma Business Skills

Usage:
    python3 fp_rekon.py <path_pdf>
    python3 fp_rekon.py <path_pdf> --sheet-id SHEET_ID --tab "Februari 2026"
    python3 fp_rekon.py <path_pdf> --dry-run
"""

import sys
import re
import json
import argparse
import subprocess
from pathlib import Path

try:
    import pdfplumber
except ImportError:
    print("ERROR: pdfplumber not installed. Run: pip3 install pdfplumber")
    sys.exit(1)

# ── Constants ──────────────────────────────────────────────────────────────────
GOG = str(Path.home() / "homebrew/Cellar/gogcli/0.9.0/bin/gog")
ACCOUNT = "harveywayan@gmail.com"
DEFAULT_SHEET_ID = "1OEEtXsv3kTnGkgVuKA_Dma-6gpVwYLaLa9g5tOLMSgA"
DEFAULT_UNIT = "PAIRS"

MONTHS_ID = {
    "Januari": 1, "Februari": 2, "Maret": 3, "April": 4,
    "Mei": 5, "Juni": 6, "Juli": 7, "Agustus": 8,
    "September": 9, "Oktober": 10, "November": 11, "Desember": 12,
}

HEADER_ROW = [
    "SUPPLIER", "RINCIAN", "Satuan", "unit",
    "Tanggal Invoice", "NO INVOICE",
    "Tgl Faktur Pajak", "No Seri Faktur Pajak",
    "Harga/Qty", "DPP", "PPN-M", "Jumlah", "stock", ""
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
    """Parse Faktur Pajak fields from extracted PDF text."""
    result = {}

    # ── Supplier (Pengusaha Kena Pajak section) ────────────────────────────
    pkp_match = re.search(
        r"Pengusaha Kena Pajak:.*?Nama\s*:\s*([A-Z][A-Z0-9\s&.,'-]+?)(?:\n|Alamat)",
        text, re.DOTALL
    )
    if pkp_match:
        result["supplier"] = pkp_match.group(1).strip()
    else:
        m = re.search(r"^Nama\s*:\s*([A-Z][A-Z0-9\s&.,'-]+?)$", text, re.MULTILINE)
        result["supplier"] = m.group(1).strip() if m else "UNKNOWN"

    # ── Nomor Seri Faktur Pajak ────────────────────────────────────────────
    m = re.search(r"Kode dan Nomor Seri Faktur Pajak:\s*(\d+)", text)
    result["no_seri_fp"] = m.group(1).strip() if m else ""

    # ── Tanggal (last date occurrence near closing signature) ──────────────
    dates = re.findall(r"(\d{1,2}\s+(?:" + "|".join(MONTHS_ID.keys()) + r")\s+\d{4})", text)
    if dates:
        result["tanggal_raw"] = dates[-1]
        result["tanggal"] = date_id_to_dmy(dates[-1])
    else:
        result["tanggal_raw"] = ""
        result["tanggal"] = ""

    # ── Referensi ──────────────────────────────────────────────────────────
    m = re.search(r"Referensi:\s*(DS\d+)", text)
    result["referensi"] = m.group(1).strip() if m else ""

    # ── DPP total — baca langsung dari PDF (bukan hitung) ─────────────────
    m = re.search(r"Dasar Pengenaan Pajak\s+([\d.,]+)", text)
    dpp_total = int(parse_rp(m.group(1))) if m else None
    result["dpp_total"] = dpp_total

    # ── PPN total — baca langsung dari PDF (bukan hitung) ─────────────────
    # Gunakan "Jumlah PPN " (dengan spasi) agar tidak match "Jumlah PPnBM"
    m = re.search(r"Jumlah PPN\s.*?([\d.,]+)", text)
    ppn_total = int(parse_rp(m.group(1))) if m else None
    result["ppn_total"] = ppn_total

    # ── Items: parse per-line (Rp harga x qty) ────────────────────────────
    lines = text.splitlines()
    items = []

    for i, line in enumerate(lines):
        rp_match = re.search(r"Rp\s*([\d,.]+)\s*x\s*([\d,.]+)", line)
        if rp_match:
            harga = parse_rp(rp_match.group(1))
            qty   = parse_rp(rp_match.group(2))

            # Item name = nearest non-header line above
            item_name = ""
            for j in range(i - 1, max(i - 5, -1), -1):
                candidate = lines[j].strip()
                if candidate and not re.match(
                    r"^(Rp|No\.|Nomor|Alamat|Nama|NPWP|Kode|Faktur|Pembeli|Pengusaha|Harga|Potongan|PPnBM|Jumlah|Sesuai|\d+\s)",
                    candidate
                ):
                    item_name = candidate
                    break

            items.append({
                "name":        item_name,
                "harga":       harga,
                "qty":         int(qty),
                "harga_jual":  harga * qty,   # subtotal item ini
                "harga_qty_col": int(harga),  # kolom Harga/Qty di sheet
                "dpp":   0,
                "ppn":   0,
                "jumlah": 0,
            })

    # ── Proportional DPP + PPN allocation per item ─────────────────────────
    # Fix Issue 1 & 2: baca DPP/PPN dari PDF, bukan kalkulasi 11%
    # Fix multi-item: alokasi proporsional berdasarkan harga_jual tiap item
    if items and dpp_total is not None and ppn_total is not None:
        harga_jual_total = sum(item["harga_jual"] for item in items)
        ppn_rate = ppn_total / dpp_total if dpp_total > 0 else 0

        dpp_remaining = dpp_total
        ppn_remaining = ppn_total

        for idx, item in enumerate(items):
            is_last = (idx == len(items) - 1)
            if is_last:
                # Last item absorbs remainder → hindari drift rounding
                item["dpp"] = dpp_remaining
                item["ppn"] = ppn_remaining
            else:
                ratio        = item["harga_jual"] / harga_jual_total
                item["dpp"]  = round(dpp_total * ratio)
                item["ppn"]  = round(item["dpp"] * ppn_rate)
                dpp_remaining -= item["dpp"]
                ppn_remaining -= item["ppn"]

            item["jumlah"] = item["dpp"] + item["ppn"]

    result["items"] = items
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


def append_rows(sheet_id: str, tab: str, rows: list[list]) -> bool:
    """Append rows to a sheet tab using --values-json."""
    values_json = json.dumps(rows)
    code, out, err = gog_run([
        "sheets", "append", sheet_id, f"'{tab}'!A:N",
        "--values-json", values_json,
        "--input", "USER_ENTERED",
    ])
    if code != 0:
        print(f"ERROR appending rows: {err}")
        return False
    print(f"  ✓ Appended {len(rows)} row(s) to '{tab}'")
    return True


def push_to_sheets(parsed: dict, sheet_id: str, tab: str, entry_type: str = "stock", dry_run: bool = False):
    """Push parsed FP data to Google Sheets."""
    rows = []
    for item in parsed["items"]:
        row = [
            parsed["supplier"],           # SUPPLIER
            item["name"],                  # RINCIAN
            str(item["qty"]),              # Satuan
            DEFAULT_UNIT,                  # unit
            parsed["tanggal"],             # Tanggal Invoice
            parsed["referensi"],           # NO INVOICE
            parsed["tanggal"],             # Tgl Faktur Pajak
            parsed["no_seri_fp"],          # No Seri Faktur Pajak
            str(item["harga_qty_col"]),    # Harga/Qty
            str(item["dpp"]),              # DPP
            str(item["ppn"]),              # PPN-M
            str(item["jumlah"]),           # Jumlah
            entry_type,                    # stock
            "",                            # (kosong)
        ]
        rows.append(row)

    print(f"\n📋 Rows to append (tab: '{tab}'):")
    print(f"{'SUPPLIER':<25} {'RINCIAN':<35} {'Qty':>5} {'Harga/Qty':>12} {'DPP':>12} {'PPN-M':>10} {'Jumlah':>12}")
    print("-" * 120)
    for row in rows:
        print(f"{row[0]:<25} {row[1]:<35} {row[2]:>5} {row[8]:>12} {row[9]:>12} {row[10]:>10} {row[11]:>12}")

    if dry_run:
        print("\n[DRY RUN] Skipping Google Sheets write.")
        return True

    print(f"\n🔍 Checking tab '{tab}'...")
    if not tab_exists(sheet_id, tab):
        print(f"  Tab not found. Creating with header row...")
        if not append_rows(sheet_id, tab, [HEADER_ROW]):
            return False

    return append_rows(sheet_id, tab, rows)


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Parse Faktur Pajak PDF and push to Google Sheets"
    )
    parser.add_argument("pdf", help="Path to Faktur Pajak PDF")
    parser.add_argument("--sheet-id", default=DEFAULT_SHEET_ID, help="Google Sheets ID")
    parser.add_argument("--tab", default=None, help='Sheet tab name (default: derived from invoice date)')
    parser.add_argument("--type", default="stock", help='Value for the "stock" column (default: stock)')
    parser.add_argument("--dry-run", action="store_true", help="Parse only, don't write to Sheets")
    args = parser.parse_args()

    pdf_path = Path(args.pdf)
    if not pdf_path.exists():
        print(f"ERROR: PDF not found: {pdf_path}")
        sys.exit(1)

    print(f"📄 Parsing: {pdf_path.name}")
    text = extract_text_from_pdf(str(pdf_path))
    parsed = parse_faktur_pajak(text)

    print(f"\n🔎 Parsed Faktur Pajak:")
    print(f"  Supplier     : {parsed['supplier']}")
    print(f"  No Seri FP   : {parsed['no_seri_fp']}")
    print(f"  Tanggal      : {parsed['tanggal']} ({parsed['tanggal_raw']})")
    print(f"  Referensi    : {parsed['referensi']}")
    print(f"  DPP Total    : {parsed['dpp_total']:,}" if parsed['dpp_total'] else "  DPP Total    : -")
    print(f"  PPN Total    : {parsed['ppn_total']:,}" if parsed['ppn_total'] else "  PPN Total    : -")
    print(f"  Items        : {len(parsed['items'])}")
    for i, item in enumerate(parsed["items"], 1):
        print(f"    {i}. {item['name']}")
        print(f"       qty={item['qty']} | harga={item['harga']:,.2f} | dpp={item['dpp']:,} | ppn={item['ppn']:,} | jumlah={item['jumlah']:,}")

    if not parsed["items"]:
        print("\n⚠️  No items found. Check PDF format.")
        sys.exit(1)

    tab = args.tab or tab_from_date(parsed["tanggal"])
    print(f"\n📊 Target sheet : {args.sheet_id}")
    print(f"   Tab          : {tab}")
    print(f"   Type         : {args.type}")

    ok = push_to_sheets(parsed, args.sheet_id, tab, entry_type=args.type, dry_run=args.dry_run)

    if ok:
        print(f"\n✅ Done! Sheet: https://docs.google.com/spreadsheets/d/{args.sheet_id}")
    else:
        print("\n❌ Failed to push to Google Sheets.")
        sys.exit(1)


if __name__ == "__main__":
    main()
