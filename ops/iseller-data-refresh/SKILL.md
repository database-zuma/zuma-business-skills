---
name: iseller-data-refresh
description: End-to-end iSeller POS data refresh pipeline — download CSVs from Google Drive, forward-fill dates, truncate+reload raw.iseller_2026, refresh all dependent mart tables and materialized views. Use when updating iSeller data, refreshing dashboard data, or re-uploading iSeller CSVs.
user-invocable: false
---

# iSeller Data Refresh Pipeline

Complete pipeline for refreshing iSeller POS data from Google Drive CSV exports through to dashboard-ready materialized views.

**When to use:** User says "update data iSeller", "refresh iSeller", "upload CSV iSeller", or any variant of refreshing POS sales data from iSeller exports.

---

## 1. Data Flow Overview

```
Google Drive (CSV exports)
    │
    ▼ gdown (Python)
~/.openclaw/workspace/iseller_temp/
    │  jan_2026.csv
    │  feb_2026.csv
    │
    ▼ upload_iseller_2026.py (forward fill + truncate + insert)
raw.iseller_2026 (87,623 rows as of Feb 2026)
    │
    ▼ mart.refresh_iseller_marts()
    ├── mart.iseller_daily (729,976 rows)
    └── mart.iseller_txn (478,271 rows)
        │
        ▼ REFRESH MATERIALIZED VIEW
        ├── mart.mv_iseller_summary (729,976 rows) — Dashboard main tabs
        ├── mart.mv_iseller_promo (9,882 rows) — Promo Monitor tab
        └── mart.mv_iseller_txn_agg (32,440 rows) — Promo Monitor Mode B
```

**Dashboard:** https://iseller-dashboard.vercel.app (5-min in-memory cache)

---

## 2. Prerequisites

### 2.1 Tools Required (Mac Mini)

| Tool | Purpose | Install |
|------|---------|---------|
| `gdown` | Download from Google Drive | `pip3 install gdown` |
| `python3` | Run upload script | Pre-installed |
| `psycopg2` | PostgreSQL adapter | `pip3 install psycopg2-binary` |
| `psql` | Direct SQL execution | `/Users/database-zuma/homebrew/Cellar/libpq/18.1_1/bin/psql` |

### 2.2 Database Credentials

| Field | Value |
|-------|-------|
| **Host** | `76.13.194.120` |
| **Port** | `5432` |
| **Database** | `openclaw_ops` |
| **User** | `openclaw_app` |
| **Password** | `Zuma-0psCl4w-2026!` |

### 2.3 Google Drive Source

| Field | Value |
|-------|-------|
| **Folder ID** | `1dS3M4E8PUwR1mlwnOj_hqCFRsyUVE6Qe` |
| **URL** | `https://drive.google.com/drive/folders/1dS3M4E8PUwR1mlwnOj_hqCFRsyUVE6Qe` |
| **Contents** | Monthly CSV exports from iSeller POS (e.g. `raw_iSeller_2026_Jan_v1.csv`, `raw_iSeller_2026_Feb_v1.csv`) |

---

## 3. Step-by-Step Pipeline

### Step 1: Download CSVs from Google Drive

```bash
# Create temp directory
mkdir -p ~/.openclaw/workspace/iseller_temp

# Download entire folder
python3 -c "
import gdown
gdown.download_folder(
    'https://drive.google.com/drive/folders/1dS3M4E8PUwR1mlwnOj_hqCFRsyUVE6Qe',
    output='/Users/database-zuma/Downloads/iseller-2026-raw/',
    quiet=False
)
"
```

**Alternative (single file):**
```bash
# If you have a direct file link:
python3 -c "import gdown; gdown.download('https://drive.google.com/uc?id=FILE_ID', 'output.csv')"
```

### Step 2: Copy & Rename Files to Staging Directory

The upload script expects exactly these filenames:

```bash
cp /Users/database-zuma/Downloads/iseller-2026-raw/raw_iSeller_2026_Jan*.csv \
   ~/.openclaw/workspace/iseller_temp/jan_2026.csv

cp /Users/database-zuma/Downloads/iseller-2026-raw/raw_iSeller_2026_Feb*.csv \
   ~/.openclaw/workspace/iseller_temp/feb_2026.csv
```

**Important:** The upload script reads from these exact paths:
- `~/.openclaw/workspace/iseller_temp/jan_2026.csv`
- `~/.openclaw/workspace/iseller_temp/feb_2026.csv`

As more months are added to the Drive folder, you may need to update the upload script to handle additional files (e.g. `mar_2026.csv`).

### Step 3: Run Upload Script

```bash
cd ~/.openclaw/workspace-metis
python3 upload_iseller_2026.py
```

**What the script does:**
1. Reads both CSV files (89 columns each)
2. **Forward-fills** the `tanggal_pesanan` (Order Date) column — see Section 4
3. Truncates `raw.iseller_2026` (full table replacement)
4. Batch inserts all rows (5,000 per batch via `execute_values()`)
5. Verifies row count, date range, and unique order count

**Expected output:**
```
🚀 MEMULAI UPLOAD DATA ISELLER 2026
📁 Januari 2026: ~45,000 baris
📁 Februari 2026: ~42,000 baris
📦 Total data yang akan di-upload: ~87,000 baris
✅ PROSES SELESAI
📊 Total data di-upload: 87,623 baris
✅ Verifikasi BERHASIL - Jumlah data cocok!
```

**Script location:** `/Users/database-zuma/.openclaw/workspace-metis/upload_iseller_2026.py`

### Step 4: Refresh Mart Tables & Materialized Views

```bash
PGPASSWORD='Zuma-0psCl4w-2026!' /Users/database-zuma/homebrew/Cellar/libpq/18.1_1/bin/psql \
  -h 76.13.194.120 -p 5432 -U openclaw_app -d openclaw_ops \
  -c "
    SELECT mart.refresh_iseller_marts();
    REFRESH MATERIALIZED VIEW mart.mv_iseller_summary;
    REFRESH MATERIALIZED VIEW mart.mv_iseller_promo;
    REFRESH MATERIALIZED VIEW mart.mv_iseller_txn_agg;
  "
```

**What each does:**
| Command | Target | Description |
|---------|--------|-------------|
| `mart.refresh_iseller_marts()` | `mart.iseller_daily`, `mart.iseller_txn` | Processes raw → clean mart tables |
| `REFRESH ... mv_iseller_summary` | `mart.mv_iseller_summary` | Dashboard main tab data |
| `REFRESH ... mv_iseller_promo` | `mart.mv_iseller_promo` | Promo Monitor tab |
| `REFRESH ... mv_iseller_txn_agg` | `mart.mv_iseller_txn_agg` | Promo Monitor Mode B |

> **Note:** The existing `refresh_iseller_data.sh` wrapper script at `~/.openclaw/workspace/scripts/refresh_iseller_data.sh` only refreshes `mv_iseller_summary`. The promo and txn_agg MVs must be refreshed separately or the script should be updated.

### Step 5: Verify

```sql
-- Check all tables have current data
SELECT 'raw.iseller_2026' AS tbl, COUNT(*) AS rows,
       MIN(tanggal_pesanan)::date AS min_date, MAX(tanggal_pesanan)::date AS max_date
FROM raw.iseller_2026
UNION ALL
SELECT 'mart.iseller_daily', COUNT(*), MIN(sale_date), MAX(sale_date) FROM mart.iseller_daily
UNION ALL
SELECT 'mart.iseller_txn', COUNT(*), MIN(sale_date), MAX(sale_date) FROM mart.iseller_txn
UNION ALL
SELECT 'mv_iseller_summary', COUNT(*), MIN(sale_date), MAX(sale_date) FROM mart.mv_iseller_summary
UNION ALL
SELECT 'mv_iseller_promo', COUNT(*), MIN(sale_date), MAX(sale_date) FROM mart.mv_iseller_promo
UNION ALL
SELECT 'mv_iseller_txn_agg', COUNT(*), MIN(sale_date), MAX(sale_date) FROM mart.mv_iseller_txn_agg;
```

**Success criteria:**
- All tables show the same `max_date` (should match the latest date in the CSV)
- `raw.iseller_2026` row count matches upload script output
- 0 NULL dates: `SELECT COUNT(*) FROM raw.iseller_2026 WHERE tanggal_pesanan IS NULL;` → must be 0

---

## 4. Forward Fill — Business Logic

### Why Forward Fill is Needed

iSeller CSV exports only put the date (`Tanggal Pesanan`) on the **first row** of each transaction. Subsequent items in the same transaction have an empty date field:

```
Row 1: date=2026-02-01 06:50:28, order=#265-3372, product=M1BLV210Z42  ← has date
Row 2: date=(empty),             order=#265-3372, product=M1BLV210Z44  ← needs fill
Row 3: date=(empty),             order=#265-3372, product=SHOPBAG001   ← needs fill
Row 4: date=2026-02-01 07:00:26, order=#33-14128, product=M1CAV201Z44  ← new txn, has date
```

### How the Script Handles It

The upload script (`upload_iseller_2026.py`, lines 68-89) tracks `current_date` and `current_order`:
1. If a row has a non-empty `tanggal_pesanan` → parse it, update `current_date`
2. If a row has an empty `tanggal_pesanan` → use `current_date` (carried from previous row)
3. This works because CSV rows are ordered by transaction, so multi-item orders are contiguous

### Verification

After upload, confirm zero NULL dates:
```sql
SELECT COUNT(*) AS null_dates FROM raw.iseller_2026 WHERE tanggal_pesanan IS NULL;
-- MUST return 0
```

---

## 5. Quick Reference — One-Liner Full Refresh

For when you just need to run the whole pipeline after CSVs are already in place:

```bash
# Full pipeline (assumes CSVs already in iseller_temp/)
cd ~/.openclaw/workspace-metis && python3 upload_iseller_2026.py && \
PGPASSWORD='Zuma-0psCl4w-2026!' /Users/database-zuma/homebrew/Cellar/libpq/18.1_1/bin/psql \
  -h 76.13.194.120 -p 5432 -U openclaw_app -d openclaw_ops \
  -c "SELECT mart.refresh_iseller_marts(); REFRESH MATERIALIZED VIEW mart.mv_iseller_summary; REFRESH MATERIALIZED VIEW mart.mv_iseller_promo; REFRESH MATERIALIZED VIEW mart.mv_iseller_txn_agg;"
```

Or use the wrapper script (after updating it to include all MVs):
```bash
bash ~/.openclaw/workspace/scripts/refresh_iseller_data.sh
```

---

## 6. Adding New Months

When a new month's data becomes available (e.g. March 2026):

1. Download the new CSV from Google Drive (same folder ID)
2. **Option A — Append to existing files:** Replace `feb_2026.csv` with full Jan+Feb+Mar combined file, OR
3. **Option B — Add new file:** Modify `upload_iseller_2026.py` to also read `mar_2026.csv`:
   ```python
   MAR_FILE = os.path.join(WORKSPACE, 'mar_2026.csv')
   # Add processing block similar to JAN_FILE / FEB_FILE in main()
   ```
4. The script always does TRUNCATE + full reload, so all months are re-uploaded each time

---

## 7. Dependency Chain — What Breaks If Raw Data Is Wrong

```
raw.iseller_2026 (source of truth)
    │
    ├── mart.iseller_daily ← wrong dates = wrong daily aggregation
    │       │
    │       ├── mart.mv_iseller_summary ← dashboard shows wrong data
    │       └── mart.mv_iseller_promo ← promo analysis wrong
    │
    └── mart.iseller_txn ← wrong txn grouping
            │
            └── mart.mv_iseller_txn_agg ← promo Mode B wrong
```

**Critical:** If forward fill fails (NULL dates remain), `mart.refresh_iseller_marts()` will still run but produce rows with NULL `sale_date`, making dashboard filters break silently.

---

## 8. Troubleshooting

| Problem | Cause | Fix |
|---------|-------|-----|
| `gdown` fails to download | Google Drive rate limit or auth | Wait 5 min, retry. Or download manually via browser. |
| Upload script says "0 baris" | CSV files not in expected location | Check `~/.openclaw/workspace/iseller_temp/` for `jan_2026.csv` and `feb_2026.csv` |
| NULL dates after upload | Forward fill logic broken or CSV format changed | Check CSV column order — `tanggal_pesanan` must be column 0 |
| `mart.refresh_iseller_marts()` error | Function definition changed or raw table schema mismatch | Check `\df+ mart.refresh_iseller_marts` in psql |
| Dashboard still shows old data | 5-min cache | Hard refresh browser (`Cmd+Shift+R`) or wait 5 minutes |
| Connection refused to DB | VPS down or network issue | `ssh root@76.13.194.120` to verify, retry in 30s |
| Row count mismatch post-upload | Rows with <10 columns skipped by script | Check CSV for malformed rows |

---

## 9. Related Resources

| Resource | Location |
|----------|----------|
| Upload script (Python) | `~/.openclaw/workspace-metis/upload_iseller_2026.py` |
| Refresh wrapper (Bash) | `~/.openclaw/workspace/scripts/refresh_iseller_data.sh` |
| CSV staging directory | `~/.openclaw/workspace/iseller_temp/` |
| Workflow documentation | `~/.openclaw/docs/iseller-data-workflow.md` |
| SOP document | `~/.openclaw/workspace/docs/sop-iseller-upload.md` |
| Dashboard repo | `~/iseller-dashboard/` |
| Database assistant skill | `zuma-business-skills/ops/zuma-database-assistant-skill/SKILL.md` |

---

**Status:** Complete
**Created:** 27 Feb 2026
**Updated:** 27 Feb 2026 — Initial creation with full pipeline, forward fill docs, dependency chain, troubleshooting
**Covers:** Google Drive download, CSV forward fill, truncate+reload to raw.iseller_2026, mart refresh (function + 3 MVs), verification queries, dependency chain, troubleshooting
