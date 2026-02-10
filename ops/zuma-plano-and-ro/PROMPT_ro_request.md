---
name: ro-request-prompt
description: Template prompt untuk generate RO (Replenishment Order) Request & Surplus Pull List. Bisa untuk 1 toko atau multi-toko. Use when membuat RO Request mingguan.
user-invocable: true
---

# PROMPT TEMPLATE: Generate RO Request & Surplus Pull List

Gunakan prompt di bawah ini untuk meminta AI generate RO Request mingguan untuk 1 atau lebih toko Zuma.

---

## Prompt: Single Store

```
Generate RO Request mingguan untuk [NAMA TOKO].

Data yang dibutuhkan:
- Planogram source: [PATH KE FILE PLANOGRAM / "RO Input [Region].xlsx"]
- Store name di planogram: [NAMA PERSIS DI PLANOGRAM, e.g. "Zuma Royal Plaza"]
- Store name di DB: [PATTERN UNTUK ILIKE, e.g. "zuma royal plaza"]
- Storage capacity: [JUMLAH BOX, 0 jika tidak ada storage]

Output yang diminta:
1. RO Protol list (artikel + ukuran yang perlu dikirim dari WH Protol)
2. RO Box list (artikel yang perlu dikirim 1 box penuh dari WH Box)
3. Surplus Pull list (artikel yang perlu ditarik dari toko, detail per ukuran)
4. Summary + cover page format dokumen resmi (AS ke WH Supervisor)

Format output: Excel (.xlsx) dengan sheet:
- RO Request (cover page + summary + signature block)
- Daftar RO Protol (numbered list, size:qty format)
- Daftar RO Box (numbered list, 1 box per artikel)
- Daftar Surplus (size-level detail untuk picking)
- Reference (tier analysis + full article status, internal use)

Business rules:
- RO Protol: size kosong <50% dari assortment
- RO Box: size kosong >=50% dari assortment
- RO Box source: WH Pusat Box (DDD + LJBB)
- RO Protol source: WH Pusat Protol (DDD only)
- Surplus: hanya cek T1, T2, T3 (skip T4/T5 clearance, T8 protection 3 bulan)
- Surplus sort: avg monthly sales ASC (slowest seller ditarik duluan)
- Restock + surplus happen same day

Skills yang perlu di-load: zuma-data-ops, zuma-sku-context, zuma-warehouse-and-stocks
```

### Contoh penggunaan (single store):

```
Generate RO Request mingguan untuk Zuma Royal Plaza.

- Planogram source: "RO Input Jatim.xlsx" sheet "Planogram"
- Store name di DB: "zuma royal plaza"
- Storage capacity: 0 boxes (tidak ada storage)

Output format dokumen resmi, semua 5 sheet.
```

---

## Prompt: Multi-Store (1 Region)

```
Generate RO Request mingguan untuk semua toko di region [NAMA REGION].

Daftar toko:
1. [NAMA TOKO 1] - Storage: [X] boxes
2. [NAMA TOKO 2] - Storage: [X] boxes
3. [NAMA TOKO 3] - Storage: [X] boxes
...

Planogram source: "RO Input [Region].xlsx" sheet "Planogram"
(Semua toko ada di file planogram yang sama, filter by store name)

Output:
- 1 Excel file PER TOKO: RO_REQUEST_[StoreName].xlsx
- Masing-masing file punya 5 sheet (cover, protol, box, surplus, reference)
- Format dokumen resmi (cover page + signature block)

ATAU:

- 1 Excel file GABUNGAN: RO_REQUEST_[Region]_[Date].xlsx
  - 1 sheet "RINGKASAN" semua toko (tabel: toko | protol count | box count | surplus count)
  - Per toko: 4 sheet (protol, box, surplus, reference)
```

### Contoh penggunaan (multi-store):

```
Generate RO Request mingguan untuk semua toko Jatim:

1. Zuma Royal Plaza - Storage: 0 boxes
2. Zuma Tunjungan Plaza - Storage: 15 boxes
3. Zuma Galaxy Mall - Storage: 20 boxes
4. Zuma Matos - Storage: 10 boxes

Planogram source: "RO Input Jatim.xlsx" sheet "Planogram"

Output: 1 file per toko, format dokumen resmi.
```

---

## Prompt: Custom (Protol Only / Box Only / Surplus Only)

Jika minggu ini hanya butuh salah satu:

```
Generate RO Protol Request saja untuk [NAMA TOKO].
(Minggu ini tidak ada RO Box, hanya protol.)

Planogram source: [FILE]
Store DB pattern: [PATTERN]
Storage: [X]
```

```
Generate Surplus Pull List saja untuk [NAMA TOKO].
(Hanya tarik surplus, tidak ada restock minggu ini.)
```

---

## Info yang Harus Disiapkan Sebelum Generate

| Data | Sumber | Wajib? |
|------|--------|--------|
| Planogram file | Tim Planner / "RO Input [Region].xlsx" | WAJIB |
| Store name (persis di planogram) | Lihat kolom pertama di sheet Planogram | WAJIB |
| Store name (DB pattern) | Lowercase, untuk ILIKE match di DB | WAJIB |
| Storage capacity (boxes) | Tanya BM / AS toko | WAJIB |
| DB access | openclaw_ops (76.13.194.120) | WAJIB |

### Store Names Reference (Jatim)

| Toko | Di Planogram | DB Pattern |
|------|--------------|------------|
| Royal Plaza | Zuma Royal Plaza | zuma royal plaza |
| Tunjungan Plaza | Zuma Tunjungan Plaza | zuma tunjungan plaza |
| Galaxy Mall | Zuma Galaxy Mall | zuma galaxy mall |
| Matos | Zuma Matos | zuma matos |
| Pakuwon Mall | Zuma Pakuwon Mall | zuma pakuwon mall |

> NOTE: Untuk region lain (Jakarta, Sumatra, dll), cek file "RO Input [Region].xlsx" atau query DB:
> ```sql
> SELECT DISTINCT nama_gudang FROM core.stock_with_product
> WHERE LOWER(nama_gudang) LIKE '%zuma%'
> ORDER BY nama_gudang;
> ```

---

## Catatan Penting

1. **Planogram harus sudah ada** — RO Request bergantung pada target planogram per artikel per ukuran. Jika belum ada planogram, buat dulu pakai `SKILL_planogram_zuma_v3.md`.

2. **Data stock real-time** — Script query langsung ke DB `core.stock_with_product`. Pastikan data snapshot terbaru sudah ada.

3. **Prioritas** — RO Protol selalu prioritas. RO Box hanya jika >=50% ukuran kosong. Ada minggu dimana RO Request cuma isi Protol saja tanpa Box.

4. **Ideal Tier Capacity %** — Saat ini diturunkan dari planogram (bukan target resmi). Akan di-update setelah ada angka resmi dari tim Planner.

5. **TO Metric** — Belum distandarkan antara "stock coverage" (stock/sales) vs "turnover rate" (sales/stock). Script output keduanya. Akan distandarkan setelah konfirmasi tim.

---

*Version: 1.0*
*Last Updated: 10 February 2026*
*Related Skills: zuma-distribution-flow/SKILL.md, SKILL_planogram_zuma_v3.md*
