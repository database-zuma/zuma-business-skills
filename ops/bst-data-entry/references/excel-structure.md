# Struktur File Excel: Update PO Zuma 2026

## Sumber File

- **Google Sheets**: https://docs.google.com/spreadsheets/d/1hJP-hQ79vxO6cj6O0R-VeiAFh5iyO0F-_N3Mpa8TawQ/edit?gid=948056441#gid=948056441
- **Sheet target**: `DATA ENTRY`
- **Owner**: Citra Kusuma Dewi <citra@zuma.id>

## Daftar Sheet

| Sheet | Fungsi |
|-------|--------|
| SUMMARY PO ALL TIER | Ringkasan semua PO per tier |
| Summary Lead Time | Ringkasan lead time pengiriman |
| HJS & DAIMATU | Data gabungan supplier HJS & Daimatu |
| PO HJS | Detail PO untuk supplier HJS |
| INDOEVA | Data supplier Indoeva |
| EVA AGUNG | Data supplier Eva Agung |
| **DATA ENTRY** | **Sheet utama input data BST (target)** |
| Hyangdotama | Data supplier Hyangdotama |
| DATA ENTRY NON HJS | Input data untuk supplier non-HJS |
| ERA SUKSES | Data supplier Era Sukses |
| DAIMATU | Data supplier Daimatu |
| Pivot Table 1 | Pivot table analisis |
| EVALUASI 3 BULAN SANDAL JADI | Evaluasi 3 bulan produksi sandal |
| Master | Master data artikel (kode, nama, tipe, variant, ukuran, tier, gender, seri) |
| Master e GUs | Master kode SKU (sumber dari Google Sheets external) |

## Sheet DATA ENTRY — Struktur Detail

### Header (Row 2)

| Kolom | Header | Deskripsi |
|-------|--------|-----------|
| A | Tanggal | Tanggal BST/langsir, format datetime |
| B | Tahun | Formula: `=YEAR(A{row})` |
| C | Month | Formula: `=TEXT(A{row},"mmmm")` |
| D | Nomor PO | Nomor Purchase Order |
| E | Kode | Kode artikel produk |
| F | Nama Artikel | Nama lengkap artikel (biasanya formula VLOOKUP ke Master, atau teks cached) |
| G | Qty | Jumlah satuan (box/pairs) |
| H | Keterangan | Formula: `=IFERROR(IF(G{row}>0,"Langsir",""),"")` |
| I | Supplier | Kode supplier: HJS, INDOEVA, EVA AGUNG, DAIMATU, ERA SUKSES, LJBB |
| J | No BST | Nomor Bukti Serah Terima |
| L | No | (Kolom tambahan, jarang diisi) |

### Formula yang Digunakan

```
Kolom B: =YEAR(A{row})
Kolom C: =TEXT(A{row},"mmmm")
Kolom F: =IFERROR(__xludf.DUMMYFUNCTION("ArrayFormula(...)"), "CACHED_NAME")
Kolom H: =IFERROR(IF(G{row}>0,"Langsir",""),"")
Row 1 G: =SUBTOTAL(9,G3:G12314)  ← total qty
```

**Catatan**: Formula kolom F menggunakan IMPORTRANGE dari Google Sheets external. Di openpyxl, formula ini disimpan sebagai `__xludf.DUMMYFUNCTION` dengan nilai cached. Saat menambah baris baru, cukup isi dengan **teks nama artikel** (bukan formula), karena IMPORTRANGE tidak berfungsi di luar Google Sheets.

### Formatting

- **Font**: Roboto Mono (semua kolom)
- **Tanggal (Kolom A)**: Number format `d" "mmm" "yyyy` (contoh: 3 Mar 2026)
- **Kolom lain**: General format
- **Data dimulai**: Row 3
- **Kapasitas**: Sampai row ~9348 (formula F terisi sampai sini), data aktual bisa kurang

### Cara Menentukan Baris Terakhir

```python
last_row = 2
for row in range(3, ws.max_row + 1):
    if ws.cell(row=row, column=1).value is not None:  # Cek kolom A (Tanggal)
        last_row = row
# Tulis data baru mulai dari last_row + 1
```

## Sheet Master — Referensi Kode Artikel

| Kolom | Header | Contoh |
|-------|--------|--------|
| A | kode_besar | Z2CA01Z21 |
| B | kode | Z2CA01 |
| C | tipe | Jepit |
| D | nama_barang | BABY BOYS CLASSIC 1, STEEL BLUE |
| E | nama_variant | BABY BOYS CLASSIC 1, 21/22, STEEL BLUE |
| F | ukuran | 21/22 |
| G | tier_kodemix | 4 |
| H | gender | BABY |
| I | seri | CLASSIC |
| J | series | CLASSIC |

**Gunakan kolom B (kode) untuk lookup dan kolom D (nama_barang) untuk nama lengkap.**

## Format Nomor PO

| Pola | Contoh | Keterangan |
|------|--------|-----------|
| `PO/DDD/HJS/{YY}/{ROMAWI}/{NUM}` | PO/DDD/HJS/25/XI/021 | Format utama 2025+ untuk HJS |
| `PO/DDD/{YY}/{ROMAWI}/{NUM}` | PO/DDD/23/IV/008 | Format lama 2023-2024 |
| `PO/JASA/DDD/{YY}/{ROMAWI}/{NUM}` | PO/JASA/DDD/25/I/001 | PO Jasa |
| `PO/MBB/HJS/{YY}/{ROMAWI}/{NUM}` | PO/MBB/HJS/25/V/003 | PO MBB |
| `PO/NS/DDD/{YY}/{ROMAWI}/{NUM}` | PO/NS/DDD/25/III/001 | PO NS |
| `PO/LJBB/HJS/{YY}/{ROMAWI}/{NUM}` | PO/LJBB/HJS/25/II/001 | PO LJBB |

**Bulan Romawi**: I=Jan, II=Feb, III=Mar, IV=Apr, V=May, VI=Jun, VII=Jul, VIII=Aug, IX=Sep, X=Oct, XI=Nov, XII=Dec

## Daftar Supplier

| Kode | Nama Lengkap |
|------|-------------|
| HJS | PT. Halimjaya Sakti |
| INDOEVA | Indoeva |
| EVA AGUNG | Eva Agung |
| DAIMATU | Daimatu |
| ERA SUKSES | Era Sukses |
| LJBB | LJBB |
