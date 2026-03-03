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
- Planogram source: DB table `portal.temp_portal_plannogram` (auto-query by store name)
- Store name di planogram DB: [NAMA PERSIS DI DB, e.g. "Zuma Royal Plaza"]
- Store name di stock DB: [PATTERN UNTUK ILIKE, e.g. "zuma royal plaza"]
- Storage capacity: [JUMLAH BOX, 0 jika tidak ada storage]

Output yang diminta:
1. RO Protol list (artikel + ukuran yang perlu dikirim dari WH Protol)
2. RO Box list (artikel yang perlu dikirim 1 box penuh dari WH Box)
3. Surplus Pull list (artikel yang perlu ditarik dari toko, detail per ukuran)
4. Summary + cover page format dokumen resmi (AS ke WH Supervisor)

Format output: Excel (.xlsx) dengan sheet:
- RO Request (cover page + summary + signature block)
- Daftar RO Protol (numbered list, size:qty format)
- Daftar RO Box (numbered list, 1 box per artikel, includes Kode Kecil column for RO App compatibility)
- Daftar Surplus (size-level detail untuk picking)
- Reference (tier analysis + full article status, internal use)

Business rules (TRANSISI — restock dulu, surplus setelah restock masuk):
- TAHAP 0: Identifikasi URGENT surplus (off-planogram) → total pairs jadi budget RO
- RO Box (DEFAULT): 3+ size kosong dari assortment → kirim 1 box penuh (12 pairs, all sizes)
- RO Protol: 1-2 size kosong (gap minor) → kirim pairs di size kosong saja
- RO Box source: WH Pusat Box (DDD + LJBB)
- RO Protol source: WH Pusat Protol (DDD only)
- Total RO pairs ≈ total urgent surplus pairs (swap: barang keluar = barang masuk)
- Jika urgent surplus = 0: RO proceeds tanpa budget cap (uncapped fallback)
- Surplus: hanya cek T1, T2, T3 (skip T4/T5 clearance, T8 protection 3 bulan)
- Surplus sort: avg monthly sales ASC (slowest seller ditarik duluan)
- Restock dulu → surplus ditarik SETELAH restock masuk

Skills yang perlu di-load: zuma-data-analyst-skill, zuma-sku-context, zuma-warehouse-and-stocks
```

### Contoh penggunaan (single store):

```
Generate RO Request mingguan untuk Zuma Royal Plaza.

- Planogram source: DB `portal.temp_portal_plannogram` (auto, filter by store name)
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

Planogram source: DB `portal.temp_portal_plannogram` (auto, filter by store name)
(Semua toko ada di DB yang sama, script filter by store_name ILIKE)

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

Planogram source: DB `portal.temp_portal_plannogram` (auto, filter by store name)

Output: 1 file per toko, format dokumen resmi.
```

---

## Prompt: Custom (Protol Only / Box Only / Surplus Only)

Jika minggu ini hanya butuh salah satu:

```
Generate RO Protol Request saja untuk [NAMA TOKO].
(Minggu ini tidak ada RO Box, hanya protol.)

Store name di planogram DB: [NAMA TOKO]
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
| Planogram data | DB: `portal.temp_portal_plannogram` (auto-query) | WAJIB (harus ada data di DB) |
| Store name (di planogram DB) | `SELECT DISTINCT store_name FROM portal.temp_portal_plannogram` | WAJIB |
| Store name (DB pattern) | Lowercase, untuk ILIKE match di `core.stock_with_product` | WAJIB |
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

> NOTE: Untuk cek toko mana saja yang sudah ada planogramnya di DB:
> ```sql
> SELECT DISTINCT store_name FROM portal.temp_portal_plannogram ORDER BY store_name;
> ```
> Untuk cek store names di stock DB:
> ```sql
> SELECT DISTINCT nama_gudang FROM core.stock_with_product
> WHERE LOWER(nama_gudang) LIKE '%zuma%'
> ORDER BY nama_gudang;
> ```

---

## Catatan Penting

1. **Planogram harus sudah ada di DB** — RO Request bergantung pada `portal.temp_portal_plannogram`. Jika belum ada data, upload planogram ke DB dulu (atau buat pakai `planogram-zuma` skill).

2. **Data stock real-time** — Script query langsung ke DB `core.stock_with_product`. Pastikan data snapshot terbaru sudah ada.

3. **Prioritas** — RO Box adalah DEFAULT (3+ size kosong). RO Protol hanya untuk gap minor (1-2 size). Total RO dibatasi oleh jumlah urgent surplus (pairs IN ≈ pairs OUT).

4. **Ideal Tier Capacity %** — Saat ini diturunkan dari planogram (bukan target resmi). Akan di-update setelah ada angka resmi dari tim Planner.

5. **TO Metric** — Belum distandarkan antara "stock coverage" (stock/sales) vs "turnover rate" (sales/stock). Script output keduanya. Akan distandarkan setelah konfirmasi tim.

---

*Version: 2.0*
*Last Updated: 25 February 2026*
*Default Skill: step3-zuma-ro-surplus-skills (zuma-ro-surplus)*
*Related Skills: planogram-zuma, zuma-data-analyst-skill, zuma-sku-context, zuma-warehouse-and-stocks*
