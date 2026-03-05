# fp-rekon-stock

Parse **Faktur Pajak PDF** (e-FP DJP) dan append data ke **Google Sheets Register Pembelian**.

> **⚠️ IRIS:** Jangan jalankan script ini sendiri. Delegate ke **Daedalus** via `sessions_spawn agentId: "daedalus"`. Kasih path PDF + tab tujuan, biarkan Daedalus yang exec `fp_rekon.py`.

## Lokasi
`~/.openclaw/workspace/zuma-business-skills/skills/finance/fp-rekon-stock/`

## Requirements
- `pdfplumber` (Python lib)
- `gog` CLI (auto-detected from PATH or Homebrew — no hardcoded path)

## Usage

**Single PDF (auto-detect date for tab name):**
```bash
python3 fp_rekon.py /path/to/faktur.pdf
```

**Custom tab:**
```bash
python3 fp_rekon.py /path/to/faktur.pdf --tab "Februari 2026"
```

**Dry-run (parse only, no upload):**
```bash
python3 fp_rekon.py /path/to/faktur.pdf --dry-run
```

**Batch mode (all PDFs in a folder):**
```bash
python3 fp_rekon.py /path/to/folder/
```

## Output Format (Google Sheets)
Sheet ID Default: `1OEEtXsv3kTnGkgVuKA_Dma-6gpVwYLaLa9g5tOLMSgA`

Columns:
1. **SUPPLIER** (from PDF)
2. **RINCIAN** (Nama Barang)
3. **Qty** (quantity)
4. **Satuan** ("PAIRS")
5. **Tanggal Invoice** (dd/mm/yyyy)
6. **NO INVOICE** (Referensi DS...)
7. **Tgl Faktur Pajak** (dd/mm/yyyy)
8. **No Seri Faktur Pajak**
9. **Harga/Qty** (Unit Price, floor)
10. **DPP** (Dasar Pengenaan Pajak — read from PDF, not calculated)
11. **PPN-M** (PPN Masukan — read from PDF, rate-agnostic: works with 11% or 12%)
12. **Jumlah** (DPP + PPN)
13. **Status:**
    - `'stock'`: Untuk semua pembelian inventory (sepatu, outsole, bahan baku/raw material).
    - `'non-stock'`: Untuk non-inventory (interior, jasa, capex).
14. **Nomor Seri Internal** (filled manually, left empty by script)

## Features

### Duplicate Detection
Before appending, the script checks existing rows in the target tab. Duplicates are detected
by hashing key fields (supplier + rincian + qty + tanggal + no_seri_fp + dpp). Duplicate rows
are skipped with a warning message.

### NPWP Extraction
The script extracts NPWP from the PDF (both 15-digit legacy and 16-digit Coretax format).
NPWP is logged in the audit trail for downstream Coretax reconciliation.

### PPN Rate Validation
After extracting DPP and PPN from the PDF, the script performs a sanity check on the effective
PPN rate. If the rate is not ~11% or ~12%, a warning is printed. This catches bad PDFs or
unusual tax calculations early.

### Batch Mode
Pass a directory path instead of a PDF file to process all PDFs in that folder. Each PDF is
processed independently with its own audit log entry. A summary is printed at the end.

### Audit Trail
Every run (including dry-runs) generates a JSON audit log in `audit_logs/` next to the script.
The log includes: timestamp, PDF path, parsed fields, warnings, rows appended, and dry-run flag.

### Regex Failure Warnings
If any field cannot be extracted from the PDF (supplier, NPWP, tanggal, referensi, DPP, PPN),
the script prints a warning but continues processing. Critical failures (DPP/PPN missing,
no items found) are flagged with 🔴. Non-critical are flagged with ⚠️.

## Changelog

### v2.0.0 (2026-02-27)
- **BREAKING:** Column headers updated to match actual sheet format (Qty/Satuan/Status/Nomor Seri Internal)
- **FIX:** `gog` CLI path now auto-detected (was hardcoded to specific Homebrew version)
- **NEW:** Duplicate detection — prevents same PDF from being appended twice
- **NEW:** NPWP extraction from PDF
- **NEW:** PPN rate sanity check (validates ~11% or ~12%)
- **NEW:** Batch mode — pass a directory to process all PDFs
- **NEW:** Audit trail — JSON log per run in `audit_logs/`
- **NEW:** Regex failure warnings — surfaces extraction issues instead of silently defaulting

### v1.0.0 (2026-02-09)
- Initial release: single PDF parsing + Google Sheets append
