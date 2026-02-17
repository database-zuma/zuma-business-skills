# Stock Opname Level 2 (SO L2)

> **Skill area:** Inventory Control · Operations  
> **Audience:** Ops team, data analysts, Iris/agents  
> **Last updated:** 2026-02-17

---

## 1. Apa itu Stock Opname Level 2?

Stock Opname Level 2 adalah **daily automated reconciliation** yang membandingkan stok fisik hari ini dengan stok yang *seharusnya* ada berdasarkan pergerakan barang semalam.

### Tujuan
- Mendeteksi **selisih (discrepancy)** antara stok nyata dan stok yang diekspektasikan secara harian
- Memberi sinyal dini untuk: shrinkage (kehilangan), kerusakan, transfer yang tidak tercatat, atau kesalahan input
- Memberikan **visibility per toko × gender group** setiap pagi sebelum operasional dimulai

### Business Context
- Zuma memiliki beberapa toko RETAIL (`zuma*`) yang stoknya dikelola via sistem Accurate (DDD entity)
- Setiap malam, sistem menarik data penjualan kemarin dan transfer barang masuk
- Script dijalankan otomatis ~05:45 WIB setiap hari (setelah sales pull ~05:30 WIB selesai)
- Hasilnya disimpan di `mart.stock_opname_l2_daily` dan tersedia untuk monitoring & analisis

---

## 2. Formula

### Expected Stock
```
expected_stock_qty = prev_stock_qty + mutasi_in - sales_qty
```

- `prev_stock_qty` = stok toko pada snapshot hari sebelumnya (dari mart tabel kemarin)
- `mutasi_in`      = barang masuk dari warehouse ke toko hari kemarin (transfer)
- `sales_qty`      = penjualan hari kemarin

### Selisih (Discrepancy)
```
selisih = stock_qty - expected_stock_qty
```

- `stock_qty` = stok fisik toko hari ini (snapshot pagi)

### Selisih Persen
```
selisih_pct = (selisih / prev_stock_qty) × 100
```

> **Catatan:** Selisih dan selisih_pct hanya dihitung jika `prev_stock_qty IS NOT NULL`.  
> Pada hari pertama data (Day 1), kedua kolom ini NULL — selisih baru bisa dihitung mulai hari ke-2.

---

## 3. Interpretasi Selisih

| `selisih` | Artinya |
|-----------|---------|
| `= 0`     | Stok sesuai ekspektasi — semua tercatat dengan benar |
| `> 0`     | Stok **lebih banyak** dari ekspektasi → kemungkinan: return barang belum tercatat, transfer masuk tanpa dokumen, atau RO yang baru tiba |
| `< 0`     | Stok **lebih sedikit** dari ekspektasi → kemungkinan: shrinkage, kerusakan, barang hilang, atau transfer keluar yang tidak tercatat |

### Contoh
```
prev_stock_qty  = 500
mutasi_in       = 20
sales_qty       = 30
expected        = 500 + 20 - 30 = 490

stock_qty hari ini = 485
selisih            = 485 - 490 = -5    ← ada 5 unit yang "hilang"
selisih_pct        = -5 / 500 × 100   = -1.00%
```

---

## 4. Data Sources

### 4.1 Stock (Stok Fisik)
- **Tabel:** `core.stock_with_product`
- **Snapshot:** Pagi hari (hari ini / `snapshot_date`)
- **Filter:** `nama_gudang` di-JOIN ke `portal.store` (category = 'RETAIL', `zuma*`)
- **Pencocokan gudang:** via `LOWER(nama_gudang) = LOWER(nama_department_old)` (dept_name)

### 4.2 Sales (Penjualan)
- **Tabel:** `core.sales_with_product`
- **Periode:** Kemarin (`transaction_date = yesterday`)
- **Filter:** `source_entity = 'DDD'`, `matched_store_name LIKE 'zuma%'`
- **Pencocokan toko:** via `matched_store_name` (nama_accurate, sudah canonical)

### 4.3 Mutasi In (Transfer Barang Masuk)
- **Tabel:** `raw.accurate_item_transfer_ddd`
- **Entity:** DDD (Accurate)
- **Arah transfer:** `from_warehouse LIKE 'warehouse%'` → `to_warehouse LIKE 'zuma%'`
- **Periode:** Kemarin (`trans_date = yesterday`)
- **Pencocokan:** `LOWER(to_warehouse) = sm.dept_name` (dept_name = LOWER nama_department_old)
- **Gender mapping:** via `portal.kodemix` (item_code → kode_besar → gender)

> ⚠️ **Penting:** JOIN ke `store_map` menggunakan `dept_name` (= `LOWER(nama_department_old)`, nama raw warehouse), **bukan** `store_name` (= `LOWER(nama_accurate)`). Keduanya berbeda untuk banyak toko Zuma.

### 4.4 Store Map
- **Tabel:** `portal.store`
- **Filter:** `category = 'RETAIL'`, `nama_accurate LIKE 'zuma%'`
- **Fungsi:** Normalisasi nama warehouse (raw) → nama toko canonical (mart)

### 4.5 Gender Grouping
Gender di-group menjadi dua kategori:
- `'BABY & KIDS'` → mencakup: BABY, BOYS, GIRLS, JUNIOR, KIDS
- Lainnya tetap apa adanya (mis. LADIES, MEN, dll.)

---

## 5. Cara Run Script

### Manual Run (dari VPS)
```bash
ssh root@76.13.194.120
python3 /opt/openclaw/scripts/calculate_so_l2.py
```

### Jadwal Otomatis
- Cron: setiap hari ~05:45 WIB
- Prasyarat: sales pull harus sudah selesai (~05:30 WIB)

### Output Script
Script akan mencetak log seperti:
```
[SO L2] Starting calculation for 2026-02-17
[SO L2] Stock date: 2026-02-17, Sales date: 2026-02-16
[SO L2] Fetched 42 rows
[SO L2] Inserted 42 rows for 7 stores
[SO L2] Total stock: 12,450  |  Total sales (yesterday): 320  |  Mutasi in: 0
[SO L2] Rows with prev_stock: 42  |  Non-zero selisih: 8
[SO L2] Status → /opt/openclaw/logs/so_l2_latest_status.json
```

### Status File (untuk monitoring Atlas)
```
/opt/openclaw/logs/so_l2_latest_status.json
```
Berisi: `snapshot_date`, `sales_date`, `stores`, `rows_inserted`, `total_stock`, `total_sales`, `selisih_nonzero_count`, `calculated_at`, `overall` (success/warning/error).

---

## 6. Skema Tabel `mart.stock_opname_l2_daily`

| Kolom | Tipe | Keterangan |
|-------|------|------------|
| `snapshot_date` | date | Tanggal snapshot stok (hari ini) |
| `store_name` | text | Nama toko canonical (LOWER nama_accurate, e.g. `zuma tanah abang`) |
| `gender_group` | text | Gender group (`BABY & KIDS`, `LADIES`, `MEN`, dll.) |
| `branch` | text | Branch/cabang toko |
| `stock_qty` | int | Stok fisik hari ini |
| `sales_qty` | int | Penjualan kemarin |
| `mutasi_in` | int | Transfer masuk dari warehouse kemarin |
| `prev_stock_qty` | int | Stok snapshot kemarin (NULL = Day 1) |
| `expected_stock_qty` | int | Stok yang diharapkan = prev + mutasi_in - sales |
| `selisih` | int | Selisih = stock_qty - expected_stock_qty |
| `selisih_pct` | numeric | Selisih dalam persen terhadap prev_stock_qty |
| `calculated_at` | timestamp | Waktu upsert terakhir |

**Primary key / unique constraint:** `(snapshot_date, store_name, gender_group)`

---

## 7. SQL Query Templates

### 7.1 Lihat data hari ini
```sql
SELECT *
FROM mart.stock_opname_l2_daily
WHERE snapshot_date = CURRENT_DATE
ORDER BY store_name, gender_group;
```

### 7.2 Lihat selisih terbesar (hari ini)
```sql
SELECT
    snapshot_date,
    store_name,
    gender_group,
    branch,
    prev_stock_qty,
    sales_qty,
    mutasi_in,
    expected_stock_qty,
    stock_qty,
    selisih,
    selisih_pct
FROM mart.stock_opname_l2_daily
WHERE snapshot_date = CURRENT_DATE
  AND selisih IS NOT NULL
ORDER BY ABS(selisih) DESC
LIMIT 20;
```

### 7.3 Summary per toko (hari ini)
```sql
SELECT
    store_name,
    branch,
    SUM(stock_qty)          AS total_stock,
    SUM(sales_qty)          AS total_sales,
    SUM(mutasi_in)          AS total_mutasi_in,
    SUM(expected_stock_qty) AS total_expected,
    SUM(selisih)            AS total_selisih,
    ROUND(
        SUM(selisih)::numeric / NULLIF(SUM(prev_stock_qty), 0) * 100, 2
    )                       AS selisih_pct_agg
FROM mart.stock_opname_l2_daily
WHERE snapshot_date = CURRENT_DATE
GROUP BY store_name, branch
ORDER BY ABS(SUM(selisih)) DESC NULLS LAST;
```

### 7.4 Trend selisih 7 hari terakhir (per toko × gender)
```sql
SELECT
    snapshot_date,
    store_name,
    gender_group,
    selisih,
    selisih_pct
FROM mart.stock_opname_l2_daily
WHERE snapshot_date >= CURRENT_DATE - INTERVAL '7 days'
  AND store_name = 'zuma tanah abang'   -- ganti sesuai toko
ORDER BY store_name, gender_group, snapshot_date;
```

### 7.5 Filter toko dengan selisih negatif (indikasi kehilangan)
```sql
SELECT
    snapshot_date,
    store_name,
    gender_group,
    selisih,
    selisih_pct
FROM mart.stock_opname_l2_daily
WHERE snapshot_date = CURRENT_DATE
  AND selisih < 0
ORDER BY selisih ASC;
```

---

## 8. Alur Data (Flow Diagram)

```
[Accurate DDD]
    │
    ├─ core.stock_with_product       ← Stok pagi ini (snapshot_date)
    ├─ core.sales_with_product       ← Penjualan kemarin (DDD, zuma*)
    └─ raw.accurate_item_transfer_ddd ← Transfer WH → Store kemarin
              │
              ▼
    calculate_so_l2.py (05:45 WIB)
              │
              ├─ JOIN portal.store       (store map: dept_name ↔ store_name)
              ├─ JOIN portal.kodemix     (item_code → gender)
              └─ JOIN mart.so_l2_daily   (prev_stock_qty dari kemarin)
              │
              ▼
    mart.stock_opname_l2_daily  ←── UPSERT (ON CONFLICT UPDATE)
              │
              └─ so_l2_latest_status.json  (monitoring Atlas)
```

---

## 9. Catatan & Edge Cases

| Situasi | Behaviour |
|---------|-----------|
| Day 1 (belum ada prev_stock) | `selisih` dan `selisih_pct` = NULL |
| Toko tidak ada penjualan kemarin | `sales_qty = 0` (COALESCE) |
| Tidak ada transfer kemarin | `mutasi_in = 0` (COALESCE) |
| `prev_stock_qty = 0` | `selisih_pct = NULL` (hindari division by zero) |
| Script error | Status file menulis `overall: error` + pesan error |
| Tidak ada data | Status file menulis `overall: warning` + `No data returned` |

---

## 10. Referensi

- **Script VPS:** `/opt/openclaw/scripts/calculate_so_l2.py`
- **Status file:** `/opt/openclaw/logs/so_l2_latest_status.json`
- **Mart table:** `mart.stock_opname_l2_daily`
- **Raw transfer:** `raw.accurate_item_transfer_ddd`
- **Store mapping:** `portal.store` (category = RETAIL)
- **Gender mapping:** `portal.kodemix`
