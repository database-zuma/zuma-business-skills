---
name: dn-to-po
description: Auto-detect Delivery Note (DN) files (PDF or Excel) and convert to Invoice + PO format. When user sends DN file with indicators (DELIVERY NOTE, DN/DDD/ pattern, or Pengiriman Pesanan sheet), immediately ask "Untuk MBB atau UBB?" then convert and deliver 2 files (Invoice for DDD + PO for MBB/UBB). Supports both PDF and Excel formats.
---

# DN to Invoice + PO - Auto Workflow

**⚠️ CRITICAL:** Every DN must generate **2 outputs**:
1. **Invoice (Faktur Penjualan)** → for DDD (seller)
2. **PO (Pesanan Pembelian)** → for MBB/UBB (buyer)

## Trigger

User sends DN file (PDF or Excel) → Check for DN indicators:
- **PDF:** Text contains "DELIVERY NOTE" and "DN/DDD/" pattern
- **Excel (.xlsx):** Sheet name "Pengiriman Pesanan" or cell contains "DELIVERY NOTE"

**If detected → LANGSUNG TANYA:** "Untuk MBB atau UBB?"

**File Format Support:**
- ✅ PDF (text extraction via pdf-parse)
- ✅ Excel (.xlsx) (XLSX library)
- Script auto-detects file extension

## ⚠️ CRITICAL EXECUTION RULES

### 🔴 MANDATORY — NO EXCEPTIONS

1. **ALWAYS USE STANDARD SCRIPTS (2 files required)**
   - ❌ NEVER write ad-hoc Python/manual scripts
   - ❌ NEVER create custom Excel formatting
   - ✅ MUST generate Invoice: `node convert-dn-to-invoice.js <file>`
   - ✅ MUST generate PO: `node convert-dn-to-po.js <file> <entity>`
   - ⚠️ Every DN = 2 outputs (Invoice + PO)
   
2. **ALWAYS DELIVER: Both Files (Invoice + PO) with Links TOGETHER**
   - ❌ NEVER send Google Sheets link first, then file later
   - ❌ NEVER send file only or link only
   - ❌ NEVER send only PO (missing Invoice)
   - ✅ MUST: Send Invoice file + link, then PO file + link
   - ✅ Each file attached + caption with Google Sheets link in ONE message

3. **IRIS EXECUTION ONLY** — Do NOT delegate to VPS
   - Task requires Mac mini tools (Node.js, gog CLI)
   - Ad-hoc user request (not cron job)
   - Execute locally, deliver immediately

**WHY CRITICAL:**
- **Consistency:** Output format must match Accurate import template
- **User expectation:** File + link delivered together (standard workflow)
- **Bu Aulia incident (2026-02-16):** Ad-hoc Python script + link-only delivery = "tidak sesuai"

## Workflow

### 1. Ask Entity
```
Untuk MBB atau UBB?
```

### 2. Convert (User jawab) — USE STANDARD SCRIPTS

**Generate 2 files (MANDATORY):**

```bash
cd ~/.openclaw/workspace/dn-to-po
PATH="$HOME/homebrew/bin:$PATH"

# Step 1: Generate Invoice for DDD
node convert-dn-to-invoice.js <file_path>

# Step 2: Generate PO for MBB/UBB
node convert-dn-to-po.js <file_path> <MBB|UBB>
```

**⚠️ Script outputs:**
- Invoice: `/Users/database-zuma/.openclaw/media/inbound/INV-DDD-dari-{NO_DN}-{TANGGAL}-{JAM}.xlsx`
- PO: `/Users/database-zuma/.openclaw/media/inbound/PO-{ENTITY}-dari-{NO_DN}.xlsx`

**Note:** Both files generated in same directory as input DN file

### 3. Move Files to Output Folder
```bash
# Move both files to DN PO ENTITAS folder
mkdir -p ~/Desktop/DN\ PO\ ENTITAS
mv /Users/database-zuma/.openclaw/media/inbound/INV-DDD-dari-*.xlsx ~/Desktop/DN\ PO\ ENTITAS/
mv /Users/database-zuma/.openclaw/media/inbound/PO-*-dari-*.xlsx ~/Desktop/DN\ PO\ ENTITAS/

# Get latest files
INVOICE_FILE=$(ls -t ~/Desktop/DN\ PO\ ENTITAS/INV-DDD-*.xlsx | head -1)
PO_FILE=$(ls -t ~/Desktop/DN\ PO\ ENTITAS/PO-*.xlsx | head -1)
```

### 4. Upload Both Files to Google Drive
```bash
# Upload Invoice
gog drive upload "$INVOICE_FILE" --name "$(basename "$INVOICE_FILE")" --json
INVOICE_ID=<extracted_from_json>
gog drive share $INVOICE_ID --email wayan@zuma.id --role writer
gog drive share $INVOICE_ID --email database@zuma.id --role writer
gog drive share $INVOICE_ID --anyone --role reader

# Upload PO
gog drive upload "$PO_FILE" --name "$(basename "$PO_FILE")" --json
PO_ID=<extracted_from_json>
gog drive share $PO_ID --email wayan@zuma.id --role writer
gog drive share $PO_ID --email database@zuma.id --role writer
gog drive share $PO_ID --anyone --role reader
```

### 5. Send to User — BOTH FILES + LINKS TOGETHER
```bash
# Send Invoice first
message action=send channel=whatsapp target=<user> \
  filePath="$INVOICE_FILE" \
  message="📄 **INVOICE (untuk DDD)**
INV-DDD-dari-{DN_NUMBER}

{X} SKU, {Y} pairs
Tanggal: {TANGGAL}

🔗 **Google Sheets:**
{INVOICE_LINK}"

# Then send PO
message action=send channel=whatsapp target=<user> \
  filePath="$PO_FILE" \
  message="📄 **PO (untuk {ENTITY})**
PO-{ENTITY}-dari-{DN_NUMBER}

{X} SKU, {Y} pairs
Tanggal: {TANGGAL}

🔗 **Google Sheets:**
{PO_LINK}"
```

**⚠️ CRITICAL:** Send BOTH files (Invoice + PO) with their respective Google Sheets links

## Script Locations

- `~/.openclaw/workspace/dn-to-po/convert-dn-to-invoice.js` — Generate Invoice (DDD)
- `~/.openclaw/workspace/dn-to-po/convert-dn-to-po.js` — Generate PO (MBB/UBB)
- `~/.openclaw/workspace/dn-to-po/load-harga.js` — Price loader helper
- `~/.openclaw/workspace/dn-to-po/template/Master Harga.xlsx` — Master price list

## Output Location ⚠️ MANDATORY

**Folder:** `~/Desktop/DN PO ENTITAS/`

**Invoice Format:** `INV-DDD-dari-{NO_DN}-{TANGGAL}-{JAM}.xlsx`
**Example:** `INV-DDD-dari-DN-DDD-WHB-2026-II-021-20260216-120345.xlsx`

**PO Format:** `PO-{ENTITY}-dari-{NO_DN}.xlsx`
**Example:** `PO-MBB-dari-DN-DDD-WHB-2026-II-021.xlsx`

**RULE:** ALL outputs MUST be moved to `~/Desktop/DN PO ENTITAS/` after generation

## Notes

- **File Format:** Supports both PDF and Excel (.xlsx)
- **PDF Parser:** `parse-dn-pdf.js` using pdf-parse library (installed)
- **Field Normalization:** PDF parser output normalized to match Excel parser
- **Pricing:** Harga satuan auto-loaded from `Master Harga.xlsx` (sheet MBB/UBB)
- **Column:** Harga After Diskon (price after discount)
- **No Pelanggan (Invoice) & No Pemasok (PO):** Dikosongkan (manual fill in Accurate)
- **DN number:** Recorded in Keterangan field as reference
- **Entity detection:** Auto-detected from customer name in DN
- **Warehouse:** All warehouses supported (exact names from Accurate: "Warehouse Pluit", "Warehouse Bali Gatsu - Box", etc.)
- **Warehouse name:** Exact match dari DN — tidak dimodifikasi (critical for Accurate import)
- **Output folder:** Auto-created if not exists
- **1 DN = 2 files:** Invoice (DDD) + PO (MBB/UBB) — MANDATORY

## ❌ Common Mistakes (DO NOT REPEAT)

### Incident: Bu Aulia (2026-02-16)

**What went wrong:**
1. ❌ Used ad-hoc Python script instead of `convert-dn-to-po.js`
   → Output format didn't match Accurate template
2. ❌ Sent Google Sheets link only, file delivered later when requested
   → User had to ask "Sya minta excel" (inconsistent with standard)
3. ❌ Only generated PO (missing Invoice for DDD)

**Result:** User reported "tidak sesuai" (output mismatch + delivery inconsistency)

**Prevention:**
- ✅ ALWAYS use standard scripts: `convert-dn-to-invoice.js` + `convert-dn-to-po.js`
- ✅ ALWAYS generate BOTH files (Invoice + PO) — never just PO alone
- ✅ ALWAYS deliver Excel file + Google Sheets link TOGETHER (one message per file)
- ✅ Follow workflow exactly as documented (no ad-hoc variations)

**If skill not active (gateway restart pending):**
- Still execute workflow manually
- But MUST use standard scripts + standard delivery format
- MUST generate both Invoice and PO
- Consistency > convenience

### New Rule (2026-02-16 onwards):
**Every DN = 2 outputs (Invoice + PO).** Missing either file = incomplete workflow.
