# Database Column-Level Reference

Reference file for `zuma-database-assistant-skill`. Contains full column definitions for all raw tables, unique constraints, and view output columns.

---

## Sales Tables (`raw.accurate_sales_{ddd,mbb,ubb}`)

All 3 sales tables share this exact structure (20 columns):

| # | Column | Type | Nullable | Default | Description |
|---|--------|------|----------|---------|-------------|
| 1 | `tanggal` | date | NOT NULL | — | Transaction date (YYYY-MM-DD) |
| 2 | `nama_departemen` | text | YES | — | Department/store name from Accurate |
| 3 | `nama_pelanggan` | text | YES | — | Customer name (used for intercompany detection) |
| 4 | `nomor_invoice` | text | YES | — | Invoice number from Accurate |
| 5 | `kode_produk` | text | NOT NULL | — | Product code = `kode_besar` (article+size) |
| 6 | `nama_barang` | text | YES | — | Product name from Accurate |
| 7 | `satuan` | text | YES | — | Unit of measure (usually "PAIR") |
| 8 | `kuantitas` | numeric | NOT NULL | — | Quantity sold |
| 9 | `harga_satuan` | numeric | YES | — | Unit selling price |
| 10 | `total_harga` | numeric | YES | — | Total amount (kuantitas x harga_satuan) |
| 11 | `bpp` | numeric | YES | `0` | Cost of goods (BPP), often 0 from API |
| 12 | `snapshot_date` | date | NOT NULL | — | Date this data was pulled by ETL |
| 13 | `loaded_at` | timestamptz | NOT NULL | `now()` | ETL load timestamp |
| 14 | `load_batch_id` | text | YES | — | Batch identifier for audit trail |
| 15 | `id` | bigint (serial) | NOT NULL | `nextval(...)` | Auto-increment PK |
| 16 | `nama_gudang` | text | YES | — | Warehouse/store name for this line item |
| 17 | `vendor_price` | numeric | YES | — | Vendor/supplier price |
| 18 | `dpp_amount` | numeric | YES | — | DPP (tax base) amount |
| 19 | `tax_amount` | numeric | YES | — | Tax amount |
| 20 | `line_number` | integer | YES | `1` | Line item sequence within same (invoice, product) pair. Handles multi-line invoices where same product appears at different prices. |

### Unique Constraint (all 3 tables)

```
UNIQUE (nomor_invoice, kode_produk, tanggal, snapshot_date, line_number)
```

**Why 5 columns in the constraint:**
- `nomor_invoice + kode_produk + tanggal` — identifies a sale line
- `snapshot_date` — allows overlapping 3-day windows to coexist without conflict
- `line_number` — handles same product appearing multiple times in one invoice at different prices (e.g., Event Wilbex bulk orders)

---

## Stock Tables (`raw.accurate_stock_{ddd,ljbb,mbb,ubb}`)

All 4 stock tables share this structure (10 columns):

| # | Column | Type | Nullable | Default | Description |
|---|--------|------|----------|---------|-------------|
| 1 | `kode_barang` | text | NOT NULL | — | Product code = `kode_besar` |
| 2 | `nama_barang` | text | YES | — | Product name |
| 3 | `nama_gudang` | text | YES | — | Warehouse/store name |
| 4 | `kuantitas` | integer | NOT NULL | — | Stock quantity in pairs |
| 5 | `snapshot_date` | date | NOT NULL | — | Date of snapshot |
| 6 | `loaded_at` | timestamptz | NOT NULL | `now()` | ETL load timestamp |
| 7 | `load_batch_id` | text | YES | — | Batch identifier |
| 8 | `id` | bigint (serial) | NOT NULL | `nextval(...)` | Auto-increment PK |
| 9 | `unit_price` | numeric | YES | — | Unit cost |
| 10 | `vendor_price` | numeric | YES | — | Vendor/supplier price |

**Note:** Stock column is `kode_barang`, NOT `kode_produk` (unlike sales tables). This naming inconsistency is historical.

---

## Other Raw Tables

| Table | Description |
|-------|-------------|
| `raw.iseller_sales` | POS sales from iSeller (evolving structure) |
| `raw.load_history` | ETL audit trail — every data pull logged here |

**`raw.load_history` columns:** `id`, `loaded_at`, `source`, `entity`, `data_type`, `batch_id`, `date_from`, `date_to`, `rows_loaded`, `status`, `error_message`

---

## View Output Columns

### `core.fact_sales_unified` (21 columns)

`source_entity`, `nomor_invoice`, `transaction_date`, `date_key`, `kode_besar`, `matched_kode_besar`, `store_name_raw`, `matched_store_name`, `nama_barang`, `quantity`, `unit_price`, `total_amount`, `cost_of_goods`, `vendor_price`, `dpp_amount`, `tax_amount`, `warehouse_code`, `snapshot_date`, `loaded_at`, `nama_pelanggan`, `line_number`

### `core.fact_stock_unified` (11 columns)

`source_entity`, `snapshot_date`, `date_key`, `kode_besar`, `matched_kode_besar`, `nama_gudang`, `quantity`, `unit_price`, `vendor_price`, `warehouse_code`, `loaded_at`

### Downstream Views

| View | Column Count | Reads From | Adds |
|------|-------------|-----------|------|
| `core.sales_with_product` | 48 cols | `fact_sales_unified` | Product enrichment (kodemix, hpprsp), store enrichment (portal.store), `is_intercompany` flag |
| `core.stock_with_product` | 38 cols | `fact_stock_unified` | Product enrichment, warehouse/capacity enrichment |
| `core.sales_with_store` | — | `fact_sales_unified` | Store enrichment only (legacy, less enriched) |

### Dimension Views

| View | Column Count | Source | Dedup Method |
|------|-------------|--------|-------------|
| `core.dim_product` | 16 cols | `portal.kodemix` + `portal.hpprsp` | `DISTINCT ON (kode_besar)` ordered by `no_urut` |
| `core.dim_store` | 12 cols | `portal.store` | `DISTINCT ON (TRIM(LOWER(nama_accurate)))` |
| `core.dim_warehouse` | 3 cols | Hardcoded | `VALUES ('DDD','MBB','UBB','LJBB')` |
| `core.dim_date` | 11 cols | Generated | Date dimension `generate_series()` |

---

## ETL Script Internals

### `flatten_invoice()` — Line Number Assignment

```python
# Tracks line_number per product code within each invoice
product_line_counter = {}

for item in invoice.get("detailItem", []):
    kode = item_obj.get("no", "")
    product_line_counter[kode] = product_line_counter.get(kode, 0) + 1
    row = {
        ...
        "line_number": product_line_counter[kode],
        ...
    }
```

### Cron Status File Format

```json
{
  "type": "sales_pull",
  "date": "2026-02-13",
  "time": "05:02:00",
  "overall": "success",
  "log_file": "/opt/openclaw/logs/sales_20260213.log"
}
```

**`overall` values:** `success` (all 3 OK), `partial_error` (1-2 failed), `error` (all failed)
