---
name: dn-to-po
description: Auto-detect Delivery Note (DN) Excel files and convert to PO format. When user sends Excel file with DN indicators (DELIVERY NOTE, DN/DDD/ pattern, or Pengiriman Pesanan sheet), immediately ask "Untuk MBB atau UBB?" then convert and deliver (Excel + Google Sheets).
---

# DN to PO - Auto Workflow

## Trigger

User sends Excel file (.xlsx) → Check for DN indicators:
- Sheet name: "Pengiriman Pesanan"
- Cell content: "DELIVERY NOTE"
- Cell content: Pattern `DN/DDD/`

**If detected → LANGSUNG TANYA:** "Untuk MBB atau UBB?"

## ⚠️ CRITICAL EXECUTION RULES

### 🔴 MANDATORY — NO EXCEPTIONS

1. **ALWAYS USE `convert-dn-to-po.js` SCRIPT**
   - ❌ NEVER write ad-hoc Python/manual scripts
   - ❌ NEVER create custom Excel formatting
   - ✅ ONLY use: `node convert-dn-to-po.js <file> <entity>`
   
2. **ALWAYS DELIVER: Excel File + Google Sheets Link TOGETHER**
   - ❌ NEVER send Google Sheets link first, then file later
   - ❌ NEVER send file only or link only
   - ✅ MUST: Attach Excel file + caption with link in ONE message

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

### 2. Convert (User jawab) — USE STANDARD SCRIPT
```bash
cd ~/.openclaw/workspace/dn-to-po
PATH="$HOME/homebrew/bin:$PATH" node convert-dn-to-po.js <file_path> <MBB|UBB>
```

**⚠️ Script output:** `~/Desktop/DN PO ENTITAS/PO-{ENTITY}-{YYMMDD}-{NNN}.xlsx`

### 3. Upload to Google Drive
```bash
# Use output filename from script (not custom naming)
OUTPUT_FILE=$(ls -t ~/Desktop/DN\ PO\ ENTITAS/PO-*.xlsx | head -1)
gog drive upload "$OUTPUT_FILE" --name "$(basename "$OUTPUT_FILE")" --json
# Extract file_id from JSON output
gog drive share <file_id> --email wayan@zuma.id --role writer
gog drive share <file_id> --email database@zuma.id --role writer
gog drive share <file_id> --anyone --role reader
```

### 4. Send to User — FILE + LINK TOGETHER
```bash
# Use message tool with BOTH filePath AND caption
message action=send channel=whatsapp target=<user> \
  filePath="$OUTPUT_FILE" \
  message="📄 **PO-{ENTITY}-dari-{DN_NUMBER}**

{DN_NUMBER}
{X} SKU, {Y} pairs
Tanggal: {TANGGAL}

🔗 **Google Sheets:**
{LINK}"
```

**⚠️ CRITICAL:** Excel file attached + caption with Google Sheets link = ONE message delivery

## Script Location

`~/.openclaw/workspace/dn-to-po/convert-dn-to-po.js`

## Output Location ⚠️ MANDATORY

**Folder:** `~/Desktop/DN PO ENTITAS/`
**Format:** `PO-[ENTITY]-[YYMMDD]-[NNN].xlsx`
**Example:** `PO-MBB-260216-001.xlsx`

**RULE:** ALL PO outputs MUST save to this folder (not directly to Desktop)

**Implementation:**
```javascript
const outputDir = path.join(os.homedir(), 'Desktop', 'DN PO ENTITAS');
if (!fs.existsSync(outputDir)) fs.mkdirSync(outputDir, { recursive: true });
const outputPath = path.join(outputDir, outputFileName);
```

## Notes

- No Pemasok & Harga Satuan dikosongkan (manual fill)
- DN number di pojok kanan atas DN file
- Support MBB & UBB entities
- Output folder auto-created if not exists

## ❌ Common Mistakes (DO NOT REPEAT)

### Incident: Bu Aulia (2026-02-16)

**What went wrong:**
1. ❌ Used ad-hoc Python script instead of `convert-dn-to-po.js`
   → Output format didn't match Accurate template
2. ❌ Sent Google Sheets link only, file delivered later when requested
   → User had to ask "Sya minta excel" (inconsistent with standard)

**Result:** User reported "tidak sesuai" (output mismatch + delivery inconsistency)

**Prevention:**
- ✅ ALWAYS use `convert-dn-to-po.js` (no custom scripts)
- ✅ ALWAYS deliver Excel file + Google Sheets link TOGETHER (one message)
- ✅ Follow workflow exactly as documented (no ad-hoc variations)

**If skill not active (gateway restart pending):**
- Still execute workflow manually
- But MUST use standard script + standard delivery format
- Consistency > convenience
