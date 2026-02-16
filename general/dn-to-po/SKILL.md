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

## Workflow

### 1. Ask Entity
```
Untuk MBB atau UBB?
```

### 2. Convert (User jawab)
```bash
cd ~/.openclaw/workspace/dn-to-po
PATH="$HOME/homebrew/bin:$PATH" node convert-dn-to-po.js <file_path> <MBB|UBB>
```

### 3. Upload Google Drive
```bash
gog drive upload <output_file> --name "PO-{ENTITY}-dari-{DN_NUMBER}.xlsx" --json
# Get file_id from output
gog drive share <file_id> --email wayan@zuma.id --role writer
gog drive share <file_id> --email database@zuma.id --role writer
gog drive share <file_id> --anyone --role reader
```

### 4. Send to User
```
📄 **PO-{ENTITY}-dari-{DN_NUMBER}**

{DN_NUMBER}
{X} SKU, {Y} pairs
Tanggal: {TANGGAL}

🔗 **Google Sheets:**
{LINK}
```

Attach Excel file + message together.

## Script Location

`~/.openclaw/workspace/dn-to-po/convert-dn-to-po.js`

**Output:** `PO-{ENTITY}-dari-{DN_NUMBER}.xlsx`

## Notes

- No Pemasok & Harga Satuan dikosongkan (manual fill)
- DN number di pojok kanan atas DN file
- Support MBB & UBB entities
