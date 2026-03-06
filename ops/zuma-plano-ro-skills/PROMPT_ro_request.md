---
name: ro-request-prompt
description: Template prompt untuk generate RO (Replenishment Order) Request & Surplus Pull List. Bisa untuk 1 toko atau multi-toko. Use when membuat RO Request mingguan.
user-invocable: true
---

# RO Request Generator — SCRIPT EXECUTION SKILL

## ⛔ CRITICAL: ALWAYS RUN THE SCRIPT — NEVER WRITE YOUR OWN CODE

```
╔══════════════════════════════════════════════════════════════════════╗
║  YOU MUST EXECUTE THE PRE-BUILT PYTHON SCRIPT TO GENERATE OUTPUT.  ║
║  DO NOT write your own openpyxl code.                              ║
║  DO NOT manually construct Excel files.                            ║
║  DO NOT interpret the format specs below as "build instructions".  ║
║                                                                     ║
║  The script handles EVERYTHING:                                     ║
║  ✅ DB queries    ✅ Gap analysis    ✅ RO decisions                ║
║  ✅ Surplus calc  ✅ Excel formatting ✅ 5 sheets                   ║
║  ✅ Styling       ✅ Totals & validation                            ║
╚══════════════════════════════════════════════════════════════════════╝
```

---

## 🔧 STEP-BY-STEP EXECUTION (Follow This Exactly)

### Step 1: Collect Required Inputs from User

| Input | How to Get | Example |
|-------|-----------|---------|
| **Store name** | Ask user OR parse from their request | "Royal Plaza" |
| **Storage capacity** | Ask user (boxes). Default 0 if they don't know | 0 |

### Step 2: Verify Script Exists

```bash
ls -la ~/.claude/skills/zuma-plano-and-ro/step3-ro-request/build_ro_request.py
```

If file not found, STOP and report error. Do NOT attempt to recreate the script.

### Step 3: Install Dependencies (if needed)

```bash
pip install psycopg2-binary openpyxl 2>/dev/null
```

### Step 4: Run the Script

**Single store:**
```bash
python3 ~/.claude/skills/zuma-plano-and-ro/step3-ro-request/build_ro_request.py \
  --store "Royal Plaza" \
  --storage 0
```

**With custom storage:**
```bash
python3 ~/.claude/skills/zuma-plano-and-ro/step3-ro-request/build_ro_request.py \
  --store "Galaxy Mall" \
  --storage 75
```

**With custom output path:**
```bash
python3 ~/.claude/skills/zuma-plano-and-ro/step3-ro-request/build_ro_request.py \
  --store "Matos" \
  --storage 0 \
  --output /Users/database-zuma/Desktop/custom_output.xlsx
```

**CLI Arguments:**

| Arg | Required | Default | Description |
|-----|----------|---------|-------------|
| `--store` | YES | — | Store display name (used as ILIKE pattern) |
| `--storage` | NO | 0 | Storage capacity in boxes |
| `--threshold` | NO | 0.50 | % size kosong threshold for RO Box (≥50% → Box, <50% → Protol) |
| `--output` | NO | `~/Desktop/DN PO ENTITAS/RO_Request_{Store}_{date}.xlsx` | Output file path |

### Step 5: Verify Output

After script completes, verify:

```bash
# Check file exists and has reasonable size (should be 15KB-50KB)
ls -la ~/Desktop/DN\ PO\ ENTITAS/RO_Request_*.xlsx

# Quick validation with Python
python3 -c "
import openpyxl
wb = openpyxl.load_workbook('OUTPUT_PATH_HERE')
sheets = wb.sheetnames
print(f'Sheets: {sheets}')
assert len(sheets) == 5, f'Expected 5 sheets, got {len(sheets)}'
expected = ['RO Request', 'Daftar RO Protol', 'Daftar RO Box', 'Daftar Surplus', 'Reference']
for s in expected:
    assert s in sheets, f'Missing sheet: {s}'
    ws = wb[s]
    print(f'  {s}: {ws.max_row} rows x {ws.max_column} cols')
print('All 5 sheets present')
wb.close()
"
```

**Validation checklist (apply to output):**

| Sheet | Must Have |
|-------|----------|
| RO Request | 23+ rows; REQUEST SUMMARY table with 3 rows (PROTOL, BOX, SURPLUS); INSTRUCTIONS section; SIGNATURES section |
| Daftar RO Protol | Header: No, Article (Kode Mix), Tier, Gender, Series, Sizes Needed, Total Pairs; TOTAL row at end |
| Daftar RO Box | Header: No, Article (Kode Mix), Kode Kecil, Tier, Gender, Series, Box Qty, WH Available; TOTAL BOXES row at end |
| Daftar Surplus | Header: No, Article (Kode Mix), Tier, **Size**, Pairs to Pull (5 columns ONLY — no Gender/Series!); TOTAL PAIRS TO PULL row at end |
| Reference | TIER CAPACITY ANALYSIS section; FULL ARTICLE STATUS section with ~200 rows (not 10, not 685) |

### Step 6: Upload to Google Drive (MANDATORY)

⛔ **Task is NOT complete until user receives GDrive link.** Do NOT skip this step.

```bash
# Upload and auto-share (anyone with link = editor)
# Uses GWS CLI (pre-authenticated) or Google API Python client as fallback
python3 ~/.claude/skills/zuma-plano-and-ro/step3-ro-request/upload_to_gdrive.py \
  --file "OUTPUT_PATH_HERE" \
  --folder "Zuma RO Requests"
```

The script will:
1. Use `gws` CLI (primary, pre-authenticated) or Python Google API (fallback)
2. Find or create folder "Zuma RO Requests" on Google Drive
3. Upload XLSX to that folder
4. Set sharing: **anyone with link = editor**
5. Print the shareable link as `GDRIVE_LINK=<url>` on the last line

**After upload:**
- Copy the `GDRIVE_LINK=` line from output
- Share the link with the user who requested the RO
- Task complete ONLY when user receives the GDrive link

**If upload fails:**
- Check error message (usually token expired → re-run, it will re-auth)
- If persistent failure → escalate to Wayan (+628983539659) via WhatsApp ONLY
---

## 📋 Multi-Store Execution

For multiple stores, run the script once per store:

```bash
# Example: All Jatim stores
for store in "Royal Plaza" "Tunjungan Plaza" "Galaxy Mall" "Matos" "Pakuwon Mall"; do
  python3 ~/.claude/skills/zuma-plano-and-ro/step3-ro-request/build_ro_request.py \
    --store "$store" --storage 0
  # Upload each output
  python3 ~/.claude/skills/zuma-plano-and-ro/step3-ro-request/upload_to_gdrive.py \
    --file ~/Desktop/DN\ PO\ ENTITAS/RO_Request_${store// /_}_*.xlsx \
    --folder "Zuma RO Requests"
```

Each run generates a separate XLSX file. Upload all files to GDrive.

---

## 🏪 Store Names Reference (Jatim)

| Toko | --store Argument | Storage |
|------|-----------------|---------|
| Royal Plaza | "Royal Plaza" | 0 |
| Tunjungan Plaza | "Tunjungan Plaza" | 0 |
| Galaxy Mall | "Galaxy Mall" | 0 |
| Matos | "Matos" | 0 |
| Pakuwon Mall | "Pakuwon Mall" | 0 |
| Icon Mall Gresik | "Icon Mall Gresik" | 0 |

---

## 🔧 Business Rules (Reference Only — Script Handles These)

These rules are built into `build_ro_request.py`. You do NOT need to implement them manually.

| Rule | Detail |
|------|--------|
| **RO Box** | ≥50% size kosong → Kirim 1 box (12 pairs, all sizes) from Gudang Box |
| **RO Protol** | <50% size kosong → Kirim pairs per size yang kosong saja from Gudang Protol |
| **RO Box Source** | WH Pusat Box (DDD + LJBB) |
| **RO Protol Source** | WH Pusat Protol (DDD only) |
| **Surplus** | Tier over-capacity → tarik artikel dengan TO terendah |
| **Surplus Tier** | T1, T2, T3 only (skip T4/T5 clearance, T8 protection 3 bulan) |
| **Surplus Sort** | avg_monthly_sales ASC (slowest seller ditarik duluan) |

---

## 🚨 Troubleshooting

### Script fails to connect to DB
```
DB_HOST = "76.13.194.120"
DB_PORT = 5432
DB_NAME = "openclaw_ops"
DB_USER = "openclaw_app"
DB_PASS = "Zuma-0psCl4w-2026!"
```
Verify VPS is reachable: `pg_isready -h 76.13.194.120 -p 5432`

### Script outputs empty RO lists
- Check planogram table exists: `portal.planogram_existing_q1_2026`
- Verify store name matches: `SELECT DISTINCT store_name FROM portal.planogram_existing_q1_2026 WHERE store_name ILIKE '%royal plaza%'`

### Script crashes
- Common issue: missing `psycopg2-binary` or `openpyxl` — run `pip install psycopg2-binary openpyxl`

### Output format doesn't match expected
The script produces the correct format automatically. If format is wrong, the **script has a bug** — do NOT fix format by writing your own code. Instead, fix the script itself at `build_ro_request.py`.

---

## ❌ WHAT NOT TO DO (Common Mistakes)

1. ❌ **DO NOT write your own openpyxl code** to create Excel files
2. ❌ **DO NOT manually query the database** and construct sheets
3. ❌ **DO NOT use the format specs above as build instructions** — they are validation criteria only
4. ❌ **DO NOT load xlsx-skill** — the script already handles all Excel formatting
5. ❌ **DO NOT modify column headers, sheet names, or row structure** — the script handles this
6. ❌ **DO NOT "interpret" or "adapt" the script** — just run it as-is with CLI args

---

## ✅ WHAT TO DO (Correct Workflow)

1. ✅ Ask user for store name and storage capacity
2. ✅ Run `build_ro_request.py` with the correct `--store` and `--storage` args
3. ✅ Verify output has 5 sheets with correct structure
4. ✅ Upload to Google Drive and share link
5. ✅ Done!

---

## Catatan Penting

1. **Planogram harus sudah ada** — Script reads from `portal.planogram_existing_q1_2026`. If planogram doesn't exist for the store, create one first using `planogram-zuma` skill.

2. **Data stock real-time** — Script queries `core.stock_with_product`. WH box availability uses `ro_whs_readystock` VIEW. Data snapshot runs at 03:00-05:30 daily via cron.

3. **Script is the source of truth** — All business logic, format, styling, calculations are in the script. If something is wrong, fix the script — don't work around it.

---

## Reference Files (in `step3-ro-request/` directory)

| File | Contents |
|------|----------|
| `build_ro_request.py` | **THE SCRIPT** — run this, don't rewrite it |
| `upload_to_gdrive.py` | **GDrive uploader** — uploads XLSX + sets anyone-with-link=editor |
| `SKILL.md` | Business logic documentation (zuma-distribution-flow) |
| `section-for-planogram.md` | Distribution flow section for planogram integration |

---

*Version: 4.1*
*Last Updated: 6 March 2026*
*Key Change: Added mandatory GDrive upload with anyone-with-link=editor sharing*
*Primary Skill: zuma-distribution-flow (step3-ro-request)*
