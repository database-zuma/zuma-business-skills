# coretax-faktur-generator

Generate **Coretax DJP-ready XLSX** (Faktur + DetailFaktur) dari Register Penjualan bulanan.

> **⚠️ IRIS:** Jangan jalankan script ini sendiri. Delegate ke **Daedalus** via `sessions_spawn agentId: "daedalus"`. Kasih path Register XLSX + entity, biarkan Daedalus yang exec `coretax_faktur.py`.

## Lokasi
`~/.openclaw/workspace/zuma-business-skills/skills/finance/coretax-faktur-generator/`

## Requirements
- `openpyxl` (Python lib — sudah ter-install)
- Python 3.9+

## Input
Register Penjualan `[bulan].xlsx` dari Bu Aulia (Accounting).

**Sheet yang dibaca:**

| Sheet | Purpose |
|---|---|
| **[BULAN]** (e.g. JAN, FEB) | Line items — semua transaksi bulan itu |
| **Master Pelanggan** | NPWP 16, NITKU, Alamat per customer |

## Usage

**Standard (DDD entity, all non-retail customers, auto-detect month, auto GDrive upload):**
```bash
python3 coretax_faktur.py "/path/to/Register_Penjualan_Januari_Tax_2026.xlsx"
```

**Specify entity and output dir:**
```bash
python3 coretax_faktur.py "/path/to/Register.xlsx" --entity DDD --output "/path/to/outbox/"
```

**MBB only:**
```bash
python3 coretax_faktur.py "/path/to/Register.xlsx" --mbb-only
```

**Filter specific customers:**
```bash
python3 coretax_faktur.py "/path/to/Register.xlsx" --customers "MAKMUR BESAR BERSAMA" "MITRA BELANJA ANDA"
```

**Dry-run (no output, no upload):**
```bash
python3 coretax_faktur.py "/path/to/Register.xlsx" --dry-run
```

**Skip GDrive upload:**
```bash
python3 coretax_faktur.py "/path/to/Register.xlsx" --no-gdrive
```

## Output
Coretax DJP template `.xlsx` with 2 sheets:

### Faktur (1 row per invoice)
Row 1: `NPWP Penjual | [blank] | {NPWP}`
Row 3: Column headers
Row 4+: Data

| Column | Source |
|---|---|
| Baris | Sequential counter |
| Tanggal Faktur | DD/MM/YYYY from Tanggal |
| Jenis Faktur | "Normal" |
| Kode Transaksi | "04" (DPP Nilai Lain) |
| Referensi | Nomor # (e.g. INV/DDD/2026/I/001) |
| ID TKU Penjual | Entity NPWP + "000000" |
| NPWP/NIK Pembeli | From Master Pelanggan |
| Jenis ID Pembeli | "TIN" |
| Negara Pembeli | "IDN" |
| Nama Pembeli | From Master Pelanggan |
| Alamat Pembeli | From Master Pelanggan |
| ID TKU Pembeli | NPWP 16 + "000000" (NITKU) |

### DetailFaktur (1 row per aggregated line item)
| Column | Source |
|---|---|
| Baris | FK to Faktur.Baris |
| Barang/Jasa | "A" (Barang) |
| Kode Barang Jasa | "640000" (HS code footwear) |
| Nama Barang/Jasa | Article name (stripped size/color, prefixed "SANDAL") |
| Nama Satuan Ukur | "UM.0019" (pairs) |
| Harga Satuan | Harga@ ÷ 1.11 (strip old PPN) |
| Jumlah Barang Jasa | Aggregated qty per article per invoice |
| Total Diskon | Sum of diskon |
| DPP | Harga Satuan × Qty |
| DPP Nilai Lain | 11/12 × DPP |
| Tarif PPN | 12 |
| PPN | 12% × DPP Nilai Lain |
| Tarif PPnBM | 0 |
| PPnBM | 0 |

## Tax Math (Kode Transaksi 04)
```
Harga Satuan = Harga@ / 1.11        (strip old 11% PPN)
DPP          = Harga Satuan × Qty
DPP Nilai Lain = 11/12 × DPP
PPN          = 12% × DPP Nilai Lain  (effectively 11% of DPP)
```

## Entity NPWP Reference
| Entity | NPWP 16 | ID TKU (NPWP+000000) |
|---|---|---|
| DDD | 0803371400624000 | 0803371400624000000000 |
| MBB | 0997550074617000 | 0997550074617000000000 |
| UBB | 0628502825617000 | 0628502825617000000000 |

## Monthly Flow
```
Bu Aulia (Accounting) → Register Penjualan [month].xlsx
    → Wayan tells Iris
    → Iris delegates to Daedalus
    → python3 coretax_faktur.py [register] --entity DDD
    → Output: Coretax_Faktur_[ENTITY]_[MONTH]_[YEAR].xlsx
    → Wayan uploads to DJP Coretax
```
