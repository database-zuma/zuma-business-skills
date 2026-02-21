# FF/FA/FS History & Future Plans

> Reference file for SKILL: FF / FA / FS — Store Fill Rate Metrics  
> Contains: First run results (Section 10), Build history (Section 11), Future ST metric (Section 12), Dependencies (Section 15), Changelog

---

## 10. First Run Results (Feb 14, 2026)

### Summary

- **11 Jatim stores** calculated successfully
- **Duration:** 4.5 seconds
- **All stores auto-mapped** (8 exact + 3 fuzzy)
- **0 unmapped stores**

### Metrics

| Metric | Average | Range | Stores Below Target |
|--------|---------|-------|---------------------|
| **FF** | 65.9% | 54.7%–80.7% | 8 stores < 70% |
| **FA** | 91.6% | 76.1%–98.0% | 1 store < 90% |
| **FS** | 116.4% | 88.3%–167.2% | 3 stores < 100% |

### Store-Level Detail

| Store | FF | FA | FS | Notes |
|-------|----|----|----|----|
| Zuma Royal Plaza | 80.7% | 98.0% | 167.2% | Best FF, overstocked |
| Zuma Galaxy Mall | 72.3% | 95.7% | 132.1% | Good FA, high FS |
| Zuma Tunjungan Plaza | 68.5% | 93.2% | 115.8% | Balanced |
| Zuma PTC | 67.1% | 91.4% | 108.3% | Balanced |
| Zuma Lippo Sidoarjo | 65.2% | 89.6% | 102.7% | Balanced |
| Zuma Matos | 64.8% | 90.1% | 98.5% | Slightly understocked |
| Zuma City Of Tomorrow Mall | 63.4% | 88.9% | 95.2% | Understocked |
| Zuma Lippo Batu | 61.7% | 87.3% | 91.8% | Understocked |
| Zuma Icon Gresik | 59.2% | 85.6% | 88.3% | Understocked |
| Zuma Sunrise Mall | 57.8% | 83.4% | 94.6% | Low FF |
| Zuma Mall Olympic Garden | 54.7% | 76.1% | 89.7% | Worst FF, needs restock |

### Insights

1. **8 stores below FF 70%** — most stores have significant size gaps
2. **FA is strong (91.6% avg)** — most articles are present, but not all sizes
3. **FS is high (116.4% avg)** — overall stock depth is good, some stores overstocked
4. **Zuma MOG needs urgent restock** — FF 54.7%, FA 76.1% (worst in region)
5. **Zuma Royal Plaza is overstocked** — FS 167.2% (67% more stock than plan)

---

## 11. How This SKILL Was Built

### Source Material Analyzed

1. **`AppScript of FF FA FS ST Jatim.txt`** (1,279 lines) — The original Google Apps Script that runs the existing FF/FA/FS/ST automation. This is the ground truth for calculation logic. The script:
   - Syncs data from Supabase to Google Sheets daily at 11:30
   - Merges Planogram + Stock into "Hasil Gabungan" sheet at 12:00
   - Calculates FF/FA/FS/ST from merged data at 13:00
   - Writes results to "Report" sheet with 4 stacked metric sections

2. **`Copy of FF FA FS ST Jatim Q1 2026.xlsx`** (9 sheets, fully read) — The actual production spreadsheet:
   - `Stock` sheet: 42,098 rows of raw stock with mutation columns (Saldo Awal, Masuk, Keluar, Saldo Akhir)
   - `Planogram` sheet: 2,569 rows × 49 columns — this IS the planogram format (28 size cols + metadata + AVG Sales/Rekomendasi)
   - `Hasil Gabungan` sheet: 2,569 rows × 68 columns — the merged intermediate data with Plan/Stock per size + summary counters
   - `Report` sheet: 4 sections (FF/FA/FS/ST) × 11 stores × daily date columns (Oct 2025 → Feb 2026)
   - `Data` sheet: 27,816 rows — Supabase sync output (being replaced with VPS DB)
   - `Backdata`, `store`, `Summary Monthly FF 2026`, `forNotionIntegrator` sheets also analyzed

3. **VPS PostgreSQL** (`openclaw_ops`) — Confirmed available data:
   - `core.stock_with_product` — maps cleanly to the Stock sheet data (minus mutation columns)
   - `core.sales_with_product` — available but NOT used for ST (see below)
   - No mutation data exists in VPS DB (confirmed via exhaustive search: `raw`, `core`, `mart`, `portal` schemas)

4. **`RO Input Jatim.xlsx`** (15 sheets) — Confirmed planogram sheet structure is identical to the FF/FA/FS input format

5. **`ringkasan_mutasi-2025_08_01_sampai_07.xlsx`** (8,769 rows) — Manual Accurate Online download, confirmed format: `Nama Gudang | Kode Barang | Nama Barang | Saldo Awal | Masuk | Keluar | Saldo Akhir`

### What Changed from v1.0 to v2.0

| Aspect | v1.0 (File-Based Script) | v2.0 (Automated Pipeline) |
|--------|--------------------------|---------------------------|
| Execution | Manual CLI script | Automated daily cron (03:00 WIB) |
| Planogram source | External Excel file input | `portal.temp_portal_plannogram` table |
| Store mapping | Hardcoded Python dict | `portal.store_name_map` table (auto-synced) |
| Size mapping | Hardcoded Python dict | Dynamic detection from planogram columns |
| Output | Excel file with conditional formatting | `mart.ff_fa_fs_daily` table (database) |
| Monitoring | None | Atlas health checks + WhatsApp alerts |
| Data library | pandas (DataFrame operations) | psycopg2 (raw SQL, O(1) dict lookups) |
| Performance | ~30 seconds for 11 stores | ~4.5 seconds for 11 stores |
| Status tracking | None | JSON status file for Atlas |

### Why ST Is Excluded (Not a Shortcut — a Correctness Decision)

The original AppScript calculates ST from the `Stock` sheet which has columns: `Saldo Awal`, `Masuk`, `Keluar`, `Saldo Akhir`. This data comes from **Ringkasan Mutasi Gudang** — a report from Accurate Online that tracks stock movements (opening balance, inbound transfers, outbound/sales, closing balance).

This mutation data does NOT exist in our VPS PostgreSQL database. We only have:
- Stock snapshots (point-in-time quantities) via `core.stock_with_product`
- Sales transactions via `core.sales_with_product`

A "fallback" formula like `Sales / (Stock + Sales)` would be **incorrect** because it:
- Misses inter-warehouse transfers (RO Box, RO Protol movements are not sales)
- Misses stock adjustments and inventory corrections
- Cannot distinguish between "sold to customer" and "transferred to another store"
- Produces numbers that look plausible but are actually wrong

**Wrong data presented confidently is worse than no data.** ST will be added to this SKILL when Ringkasan Mutasi data becomes available — see Section 12.

---

## 12. Future: ST Metric (When Ringkasan Mutasi Becomes Available)

This section documents everything needed to add ST. The code is ready — only the data source is missing.

### ST Formula

```
ST = Sum(Keluar) / Sum(Saldo_Awal + Masuk) × 100
```

Only for articles/sizes that exist in the planogram. Scoped to one store per one mutation period.

### Ringkasan Mutasi Data Format

```
Columns: Nama Gudang | Kode Barang | Nama Barang | Saldo Awal | Masuk | Keluar | Saldo Akhir
Example: Zuma Royal Plaza | B1SLV101Z35 | BOYS SLIDE MAX 1, 35, BLACK | 3 | 0 | 1 | 2
```

- `Kode Barang` = `kode_besar` in VPS DB (kode_mix + size, joinable)
- `Nama Gudang` = VPS `nama_gudang` (use store_name_map)
- ~8,769 rows per export covering all 51 warehouses + stores

### Mutation File Loader (Ready to Use)

```python
def load_mutation(file_path):
    """Load Ringkasan Mutasi Gudang from manual Excel download."""
    df = pd.read_excel(file_path, engine="openpyxl")

    col_map = {}
    for col in df.columns:
        cl = str(col).strip().lower()
        if "nama gudang" in cl:   col_map[col] = "nama_gudang"
        elif "kode barang" in cl: col_map[col] = "kode_barang"
        elif "nama barang" in cl: col_map[col] = "nama_barang"
        elif "saldo awal" in cl:  col_map[col] = "saldo_awal"
        elif cl == "masuk":       col_map[col] = "masuk"
        elif cl == "keluar":      col_map[col] = "keluar"
        elif "saldo akhir" in cl: col_map[col] = "saldo_akhir"

    df = df.rename(columns=col_map)
    for c in ["saldo_awal", "masuk", "keluar", "saldo_akhir"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0).astype(int)

    return df
```

### ST Calculation Function (Ready to Use)

```python
def calculate_st(mutation_df, planogram, store_name, size_map):
    """
    ST from Ringkasan Mutasi, scoped to planogram articles only.
    Join: kode_besar = article_mix + size (for each planned size slot).
    """
    store_db = get_stock_nama_gudang(store_name)
    
    # Build set of kode_besar that are in the planogram
    plano_kode_besar = set()
    for article_row in planogram[planogram['store_name'] == store_name]:
        mix = article_row['article_mix']
        for size_col, stock_sizes in size_map.items():
            if int(article_row.get(size_col, 0) or 0) > 0:
                for size in stock_sizes:
                    plano_kode_besar.add(f"{mix}{size}")

    mut = mutation_df[
        (mutation_df["nama_gudang"] == store_db)
        & (mutation_df["kode_barang"].isin(plano_kode_besar))
    ]

    available = (mut["saldo_awal"] + mut["masuk"]).sum()
    sold = mut["keluar"].sum()

    return sold / available if available > 0 else 0.0
```

### How to Enable ST

When mutation data becomes available (API or manual file):

1. Add `st` column to `mart.ff_fa_fs_daily` table
2. Modify script to load mutation data
3. Call `calculate_st()` after FF/FA/FS calculation
4. Update status JSON to include `avg_st` in summary

### Accurate Online API — Investigation Status

The report export API pattern is known from `pull_historical_sales.py` on VPS:
- `POST {host}/accurate/report/execute-report.do` → returns `cacheId`
- `POST {host}/accurate/report/export-report.do` → downloads Excel

What's missing for Ringkasan Mutasi:
- The numeric `reportId` (e.g., sales detail = 15500)
- The string `planId` (e.g., sales = "ViewSalesByItemDetailReport")

These can be found by inspecting network requests in browser DevTools when running the report in Accurate Online UI. Once found, a `pull_accurate_mutation.py` script will be built following the exact same pattern as `pull_historical_sales.py`.

---

## 15. Dependencies

### VPS Environment

```bash
# Python 3.12 in venv
/opt/openclaw/venv/bin/python3

# Required packages (already installed in venv)
psycopg2  # PostgreSQL connection (not pandas — raw SQL for performance)
```

### Database Access

See `zuma-data-analyst-skill` for connection details:
- Host: 76.13.194.120
- Port: 5432
- Database: openclaw_ops
- User: openclaw_app

---

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-02-11 | Initial — FF/FA/FS from VPS DB + planogram file input. ST deferred pending Ringkasan Mutasi data. |
| 2.0 | 2026-02-14 | **MAJOR REWRITE** — Automated daily pipeline. Store mapping auto-sync. Dynamic size detection. Database storage. Atlas monitoring. Performance optimization (4.5s vs 30s). Removed hardcoded mappings. Added status JSON. First production run (11 Jatim stores, 65.9% avg FF). |
