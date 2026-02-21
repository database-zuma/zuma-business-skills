# fp-rekon-stock

Parse **Faktur Pajak PDF** (e-FP DJP) dan append data ke **Google Sheets Register Pembelian**.

## Lokasi
`~/.openclaw/workspace/zuma-business-skills/skills/finance/fp-rekon-stock/`

## Requirements
- `pdfplumber` (Python lib)
- `gog` CLI (configured with account `harveywayan@gmail.com`)

## Usage

**Basic (auto-detect date for tab name):**
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

## Output Format (Google Sheets)
Sheet ID Default: `1OEEtXsv3kTnGkgVuKA_Dma-6gpVwYLaLa9g5tOLMSgA`

Columns:
1. **SUPPLIER** (from PDF)
2. **RINCIAN** (Nama Barang)
3. **Satuan** (Qty)
4. **unit** ("PAIRS")
5. **Tanggal Invoice** (dd/mm/yyyy)
6. **NO INVOICE** (Referensi DS...)
7. **Tgl Faktur Pajak** (dd/mm/yyyy)
8. **No Seri Faktur Pajak**
9. **Harga/Qty** (Unit Price, floor)
10. **DPP** (Unit Price * Qty)
11. **PPN-M** (11% of DPP)
12. **Jumlah** (DPP + PPN)
13. **stock** (literal text)
14. (Empty column for Kode Ref)
