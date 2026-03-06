---
name: ro-request-prompt
description: Generate RO (Replenishment Order) Request. Use when membuat RO Request mingguan.
user-invocable: true
---

# RO Request Generator

Run the pre-built script. Do NOT write your own code.

## Steps

### 1. Ask user
- Store name (e.g. "Royal Plaza")
- Storage capacity in boxes (default 0)

### 2. Run script
```bash
pip install psycopg2-binary openpyxl 2>/dev/null
python3 ~/.claude/skills/zuma-plano-and-ro/step3-ro-request/build_ro_request.py \
  --store "STORE_NAME" \
  --storage STORAGE_NUMBER
```

### 3. Verify
```bash
python3 -c "
import openpyxl, glob, os
f = glob.glob(os.path.expanduser('~/Desktop/DN PO ENTITAS/RO_Request_*.xlsx'))[-1]
wb = openpyxl.load_workbook(f)
assert len(wb.sheetnames) == 5, f'Expected 5 sheets, got {len(wb.sheetnames)}'
print('OK:', f, wb.sheetnames)
"
```
If not 5 sheets, something went wrong — report the error. Do NOT try to fix or recreate the output.

### 4. Upload to Google Drive
```bash
python3 ~/.claude/skills/zuma-plano-and-ro/step3-ro-request/upload_to_gdrive.py \
  --file "OUTPUT_FILE_PATH" \
  --folder "Zuma RO Requests"
```

### 5. Share link
Copy the `GDRIVE_LINK=` line from upload output and give it to the user. Done.

## Rules
- NEVER write your own openpyxl/Excel code
- NEVER query the database yourself
- NEVER modify the output file after the script creates it
- If the script fails, report the error — do not work around it

*Version: 5.0*
