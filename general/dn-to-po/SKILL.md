---
name: dn-to-po
description: Auto-detect Delivery Note (DN) Excel files from DDD and convert to Purchase Order (PO) import format for Accurate Online. Handles DN file detection, entity extraction (MBB/UBB), conversion, Google Drive upload, and standardized delivery (Excel + Google Sheets link). Use when user sends Excel file containing DN data.
---

# DN to PO Converter

Auto-convert Delivery Note (DN) files from DDD to Purchase Order (PO) import format for MBB/UBB entities.

## When to Use

**Trigger:** User sends Excel file (.xlsx)

**Auto-detect DN if:**
- Sheet name contains "Pengiriman Pesanan" OR
- Cell content contains "DELIVERY NOTE" OR
- Cell content contains "DN/DDD/" pattern (DN number)

**If detected:** Proceed with conversion workflow automatically (don't ask user)

## Detection & Extraction

Use Node.js quick check:
```javascript
const XLSX = require('xlsx');
const wb = XLSX.readFile(filePath);
const sheet = wb.Sheets[wb.SheetNames[0]];
const rows = XLSX.utils.sheet_to_json(sheet, { header: 1, defval: '' });

// Check for DN indicators
const isDN = wb.SheetNames.some(s => s.includes('Pengiriman Pesanan')) ||
  rows.some(row => row.some(cell => 
    String(cell).includes('DELIVERY NOTE') || 
    String(cell).match(/DN\/DDD\//)
  ));
```

**Extract from DN:**
- DN Number: Cell pattern `DN/DDD/*/YYYY/*/###` (e.g., DN/DDD/WHB/2026/II/021)
- Entity: Customer name → "CV MAKMUR BESAR BERSAMA" = MBB, "CV UNTUNG BESAR BERSAMA" = UBB
- Date: Date cell near DN number
- Items: Item Kode + Name Article + Qty + Unit (row 22+, columns 1, 7, 22, 31)

## Conversion Workflow

### 1. Run Converter
```bash
cd ~/.openclaw/workspace/dn-to-po
PATH="$HOME/homebrew/bin:$PATH" node convert-dn-to-po.js <file_path> <entity>
```

**Output:** `PO-{ENTITY}-dari-{DN_NUMBER}.xlsx`
- Example: `PO-MBB-dari-DN-DDD-WHB-2026-II-021.xlsx`
- Location: Same folder as input file

### 2. Upload to Google Drive
```bash
~/homebrew/Cellar/gogcli/0.9.0/bin/gog drive upload <output_file> \
  --name "PO-{ENTITY}-dari-{DN_NUMBER}.xlsx" --json

# Extract file_id from JSON output, then share:
gog drive share <file_id> --email wayan@zuma.id --role writer
gog drive share <file_id> --email database@zuma.id --role writer
gog drive share <file_id> --anyone --role reader
```

### 3. Deliver to User

**Format standar (WhatsApp):**
```
📄 **PO-{ENTITY}-dari-{DN_NUMBER}**

{DN_NUMBER}
{X} SKU, {Y} pairs
Tanggal: {TANGGAL}

🔗 **Google Sheets:**
{GSHEET_LINK}
```

**Send together:**
- File Excel (media attachment)
- Google Sheets link (in message)

**Tools:**
```javascript
message({
  action: 'send',
  channel: 'whatsapp',
  target: '<user_phone>',
  message: `📄 **PO-MBB-dari-DN-DDD-WHB-2026-II-021**\n\nDN/DDD/WHB/2026/II/021\n53 SKU, 168 pairs\nTanggal: 13 Feb 2026\n\n🔗 **Google Sheets:**\nhttps://docs.google.com/spreadsheets/d/...`,
  media: '/path/to/PO-MBB-dari-DN-DDD-WHB-2026-II-021.xlsx'
});
```

## Error Handling

**If entity unclear:**
- Check customer name in DN file first
- If still unclear → Ask user: "Ini untuk MBB atau UBB?"

**If conversion fails:**
- Check DN file format (must be Accurate export "Pengiriman Pesanan")
- Verify Node.js installed: `~/homebrew/bin/node --version`
- Check npm deps: `cd ~/.openclaw/workspace/dn-to-po && npm install`

## Script Location

**Converter repo:** `~/.openclaw/workspace/dn-to-po/`
**GitHub:** https://github.com/database-zuma/dn-to-po

**Dependencies:**
- Node.js (v25.6.0+) at `~/homebrew/bin/node`
- npm packages: `xlsx`, `exceljs` (auto-installed via `npm install`)

## Notes

- **No Pemasok & Harga Satuan** dikosongkan (user isi manual di Accurate)
- **Keterangan PO:** Auto-filled with `PO dari {DN_NUMBER}`
- **Filename:** Clean format without timestamp (e.g., `PO-MBB-dari-DN-DDD-WHB-2026-II-021.xlsx`)
- **Multi-entity support:** MBB (CV Makmur Besar Bersama), UBB (CV Untung Besar Bersama)
