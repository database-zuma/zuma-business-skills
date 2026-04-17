---
name: agent-ar-mandiri-1
description: "Workflow rekonsiliasi Accounts Receivable (AR) Zuma Indonesia dari Merchant Statement Yokke EDC untuk rekening Bank Mandiri 560 (No. Rek 1420056089898). Gunakan skill ini setiap kali user meng-upload file Yokke (`Yokke_*.xlsx`, `MSR_*`, atau file merchant statement EDC lainnya) dan minta diolah jadi format `Extracting_finance_data`. Trigger juga saat user menyebut keyword seperti `yokke`, `merchant statement EDC`, `extracting finance`, `rekap AR Mandiri`, `settlement EDC`, `MDR`, `Tagihan Admin Nominal`, `mapping MID`, atau minta buatkan keterangan format `Terima Penjualan EDC Mandiri [Toko] [Tgl]`. Skill ini auto-fetch mapping MID → Nama Toko/Cabang dari Google Sheets Master EDC Bank — user tidak perlu upload file Master 560 atau Buku Bank."
---

# Agent AR Mandiri 1 — Rekonsiliasi Yokke EDC ke Format Finance

## Konteks Bisnis

Zuma Indonesia menerima settlement EDC Yokke di rekening Bank Mandiri **1420056089898** (KCP Kuta Raya) untuk toko-toko di wilayah **Bali & Lombok**. Setiap hari Yokke kirim Merchant Statement (MSR) berisi detail semua transaksi EDC card + QRIS pada tanggal tertentu, dengan AMOUNT (gross), MDR Amount (fee), dan NET AMOUNT (yang akan ditransfer).

Skill ini mengolah file Yokke mentah → spreadsheet siap-jurnal dengan Nama Toko & Cabang sudah di-mapping, plus Keterangan sesuai standar penulisan Buku Bank.

## Input

User upload **1 file saja**:

| File | Format | Isi |
|---|---|---|
| `Yokke_*.xlsx` atau `MSR_*` | XLSX dengan CSV-in-cell | Detail transaksi EDC per tanggal |

**Master 560 (MID mapping) — auto-fetch dari Google Sheets, user tidak perlu upload:**

- **Nama workbook**: "Master EDC Bank"
- **URL**: <https://docs.google.com/spreadsheets/d/1zmnWj_tGVRrHMktH3D7Zj1HAIZ3QUlksVocjpw0AywI/edit?gid=1504130740>
- **Document ID**: `1zmnWj_tGVRrHMktH3D7Zj1HAIZ3QUlksVocjpw0AywI`
- **GID sheet Master 560**: `1504130740`
- **Owner**: finance@zuma.id

Kalau user tetap upload file Buku Bank lokal, abaikan — Google Sheets adalah source of truth.

## Output

File `Extracting_finance_data_OUTPUT.xlsx` dengan **1 sheet**: `Yokke Detail`.

Satu baris per transaksi Yokke (tidak diagregat). Kolom:

| Col | Header | Source |
|---|---|---|
| A | Tanggal Transaksi | Yokke `TRXDATE` |
| B | Keterangan | `Terima Penjualan EDC Mandiri {Nama Toko} {tgl ID}` |
| C | MID | Yokke `MID` (11 digit, text format) |
| D | Cabang | Master 560 `Cabang` (Bali/Lombok) |
| E | Tagihan | Yokke `AMOUNT` |
| F | Admin | Yokke `MDR Amount` |
| G | Nominal Setelah Admin | Yokke `NET AMOUNT` |
| H | Nama Toko | Master 560 `Nama Toko di EDC` |
| I | Jumlah_Clean | = NET AMOUNT (numerik, semua CR/positif) |
| J | Tgl Settle | TRXDATE + 1 hari (tanggal Yokke transfer ke rek Mandiri) |
| K | TRXTIME | Yokke `TRXTIME` |
| L | Issuer | Yokke `Issuer Name` (BCA, BRI, Mandiri, Danamon, BSI, Dana, dll) |
| M | Ref Number | Yokke `Refference Number` |

Tambahan: **baris TOTAL** di paling bawah dengan SUM kolom E, F, G, I.

## Workflow

### Step 1: Fetch Master 560 dari Google Sheets

**Cara A — via Google Drive MCP / connector** (preferred di Claude):
```python
# google_drive_fetch document_id=1zmnWj_tGVRrHMktH3D7Zj1HAIZ3QUlksVocjpw0AywI
# target gid=1504130740 (Master 560)
```

**Cara B — CSV export URL** (fallback, butuh sheet publik):
```python
import pandas as pd
DOC_ID = "1zmnWj_tGVRrHMktH3D7Zj1HAIZ3QUlksVocjpw0AywI"
GID = "1504130740"
url = f"https://docs.google.com/spreadsheets/d/{DOC_ID}/export?format=csv&gid={GID}"
master = pd.read_csv(url)
```

**Cara C — Google Sheets API v4** (OpenClaw production):
```python
from google.oauth2 import service_account
from googleapiclient.discovery import build
creds = service_account.Credentials.from_service_account_file(
    'service-account.json',
    scopes=['https://www.googleapis.com/auth/spreadsheets.readonly'])
service = build('sheets', 'v4', credentials=creds)
result = service.spreadsheets().values().get(
    spreadsheetId='1zmnWj_tGVRrHMktH3D7Zj1HAIZ3QUlksVocjpw0AywI',
    range='Master 560!A:H').execute()
# convert result['values'] ke dataframe
```

Setelah dapat dataframe, build lookup dict:
```python
master['MID'] = master['MID'].astype(str).str.strip()
mid_map = {r['MID']: {
    'Nama Toko': r['Nama Toko di EDC'],
    'Cabang': r['Cabang']         # 'Bali' atau 'Lombok'
} for _, r in master.iterrows()}
```

Kolom yang dipakai: `MID`, `Nama Toko di EDC`, `Cabang`. Selain itu (Nama Departemen, Jenis EDC, Term ID, Alamat EDC, Email) optional.

### Step 2: Parse Yokke Merchant Statement

File Yokke berbentuk XLSX dengan **satu kolom** yang berisi baris-baris CSV (unik, bukan XLSX tabular biasa). Struktur:

- Baris 1–5: metadata (`MERCHANT STATEMENT`, `Report Date`, `Group`, `Group Name`, `DETAIL`)
- Baris 6: header CSV: `NMID,MID,Merchant Official,Trading Name,Bank Account,Bank Account Name,TRXDATE,TRXTIME,Issuer Name,TID,Refference Number,Reff ID/Invoice No,AMOUNT,MDR Amount,NET AMOUNT`
- Baris 7–N: **detail transaksi** (yang kita butuhkan)
- Baris `TOTAL,,,,,,,,,,,,"X","Y","Z"`: grand total — skip
- Baris `SUMMARY GROUP,,,,...`: separator — skip
- Baris berikutnya: header summary (`NMID,MID,...,PAYMENT DATE,TOTAL AMOUNT,TOTAL MDR,TOTAL NET AMOUNT`)
- Baris-baris summary per merchant dengan `PAYMENT DATE` = settlement date — skip
- Baris `TOTAL` terakhir — skip

Parsing:
```python
import pandas as pd, csv
from io import StringIO

raw = pd.read_excel(yokke_path, header=None, dtype=str)
header_row = next(i for i, r in raw.iterrows() if 'NMID' in str(r[0]))

rows = []
for i in range(header_row, len(raw)):
    line = raw.iloc[i, 0]
    if pd.isna(line) or not str(line).strip(): continue
    for parsed in csv.reader(StringIO(str(line))):
        if parsed and parsed[0].strip():
            rows.append(parsed)

yokke_df = pd.DataFrame(rows[1:], columns=rows[0])

# Filter 1: hanya baris dengan MID 11 digit (buang TOTAL rows)
yokke_df = yokke_df[yokke_df['MID'].astype(str).str.match(r'^\d{11}$', na=False)]

def to_float(s):
    s = str(s).replace(',', '').strip()
    return float(s) if s else 0.0

yokke_df['AMOUNT_num'] = yokke_df['AMOUNT'].apply(to_float)
yokke_df['MDR_num']    = yokke_df['MDR Amount'].apply(to_float)
yokke_df['NET_num']    = yokke_df['NET AMOUNT'].apply(to_float)

# Filter 2: buang baris summary group (kolom AMOUNT kosong karena offset)
yokke_df = yokke_df[yokke_df['AMOUNT_num'] > 0].copy()

# Parse date
yokke_df['TRXDATE_parsed'] = pd.to_datetime(yokke_df['TRXDATE'], format='%d-%m-%Y')
```

### Step 3: Enrich dengan Master 560 & Format Output

```python
BULAN = {1:'Januari', 2:'Februari', 3:'Maret', 4:'April', 5:'Mei', 6:'Juni',
         7:'Juli', 8:'Agustus', 9:'September', 10:'Oktober', 11:'November', 12:'Desember'}

out = []
for _, r in yokke_df.iterrows():
    mid = r['MID']
    info = mid_map.get(mid, {})
    nama_toko = info.get('Nama Toko') or r['Trading Name'].title()
    cabang = info.get('Cabang', '')
    tgl_trx = r['TRXDATE_parsed']
    tgl_id = f"{tgl_trx.day} {BULAN[tgl_trx.month]}"
    ket = f"Terima Penjualan EDC Mandiri {nama_toko} {tgl_id}"

    out.append({
        'Tanggal Transaksi': tgl_trx,
        'Keterangan': ket,
        'MID': mid,
        'Cabang': cabang,
        'Tagihan': r['AMOUNT_num'],
        'Admin': r['MDR_num'],
        'Nominal Setelah Admin': r['NET_num'],
        'Nama Toko': nama_toko,
        'Jumlah_Clean': r['NET_num'],
        'Tgl Settle': tgl_trx + pd.Timedelta(days=1),
        'TRXTIME': r['TRXTIME'],
        'Issuer': r['Issuer Name'],
        'Ref Number': str(r['Refference Number']).lstrip("'"),
    })

out_df = pd.DataFrame(out).sort_values(['MID', 'TRXTIME']).reset_index(drop=True)
```

### Step 4: Write Excel dengan Styling

```python
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment

wb = Workbook()
ws = wb.active
ws.title = 'Yokke Detail'

# Title baris 1
report_date = out_df['Tanggal Transaksi'].iloc[0].strftime('%d/%m/%Y')
title = f"DETAIL TRANSAKSI YOKKE {report_date} (Settle di rekening H+1)"
ws.cell(1, 1, title).font = Font(bold=True, size=13, color='FFFFFF')
ws.cell(1, 1).fill = PatternFill('solid', start_color='1F4E79')
ws.cell(1, 1).alignment = Alignment(horizontal='center')
ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=13)

# Header row 2
headers = list(out_df.columns)
for c, h in enumerate(headers, 1):
    cell = ws.cell(2, c, h)
    cell.font = Font(name='Arial', bold=True, color='FFFFFF')
    cell.fill = PatternFill('solid', start_color='305496')
    cell.alignment = Alignment(horizontal='center', wrap_text=True)

# Data rows
yokke_fill = PatternFill('solid', start_color='E8F4D9')
for i, r in out_df.iterrows():
    for c, h in enumerate(headers, 1):
        cell = ws.cell(i + 3, c, r[h])
        cell.font = Font(name='Arial', size=10)
        cell.fill = yokke_fill
        if h in ('Tagihan', 'Admin', 'Nominal Setelah Admin', 'Jumlah_Clean'):
            cell.number_format = '#,##0.00'
        elif h == 'MID':
            cell.number_format = '@'
        elif h in ('Tanggal Transaksi', 'Tgl Settle'):
            cell.number_format = 'dd/mm/yyyy'

# TOTAL row
n = len(out_df)
total_row = n + 3
ws.cell(total_row, 1, 'TOTAL').font = Font(bold=True)
for col_letter, col_idx in [('E', 5), ('F', 6), ('G', 7), ('I', 9)]:
    ws.cell(total_row, col_idx, f"=SUM({col_letter}3:{col_letter}{total_row-1})")
    ws.cell(total_row, col_idx).font = Font(bold=True)
    ws.cell(total_row, col_idx).number_format = '#,##0.00'
for c in range(1, 14):
    ws.cell(total_row, c).fill = PatternFill('solid', start_color='FCE4A6')

# Column widths
widths = {'A':14,'B':55,'C':14,'D':10,'E':16,'F':12,'G':20,
          'H':22,'I':16,'J':12,'K':10,'L':12,'M':18}
for col, w in widths.items():
    ws.column_dimensions[col].width = w
ws.freeze_panes = 'A3'

wb.save(output_path)
```

Lalu recalc formulas supaya TOTAL keluar nilai. Kalau runtime tidak ada LibreOffice, compute manual dan hardcode TOTAL.

## Reconciliation

Tie-out wajib sebelum return file ke user:

1. `sum(Tagihan) − sum(Admin)` = `sum(Nominal Setelah Admin)` — exact, tanpa selisih
2. `sum(Tagihan)` di baris TOTAL output = `TOTAL AMOUNT` di baris TOTAL file Yokke asli
3. `sum(Admin)` output = `TOTAL MDR` Yokke
4. `sum(Nominal)` output = `TOTAL NET AMOUNT` Yokke
5. `count(detail row)` output = count detail row Yokke (sebelum summary group)

Kalau ada selisih → print warning per-MID delta. JANGAN silent.

## Edge Cases & Gotchas

- **Baris SUMMARY GROUP punya MID 11 digit juga** (bukan detail!) — tapi `AMOUNT` kosong karena ada kolom `PAYMENT DATE` di offset berbeda. Filter dengan `AMOUNT_num > 0` untuk buang summary ini.
- **MID di Yokke 11 digit**, sama format dengan Master 560 — lookup langsung tanpa transformasi.
- **MID tidak ditemukan di Master 560**: fallback ke `Trading Name` dari Yokke (title-case). Print warning supaya user tahu perlu update Master EDC Bank di Google Sheets.
- **Issuer Name bisa apa saja**: BCA, BRI, BNI, Mandiri, Danamon, BSI, Dana, BCA Digital, "PT. Bank S..." (truncated), dll. Jangan hard-code whitelist.
- **TRXTIME format `HHMMSS`** (6 digit, tanpa separator). Contoh `092523` = 09:25:23. Biarkan as-is di output.
- **Refference Number diawali `'`** (leading apostrophe — trick Excel supaya dibaca text). Strip dengan `.lstrip("'")`.
- **Nama bulan Bahasa Indonesia**, bukan Inggris. "Maret" bukan "March".
- **Tanggal tanpa leading zero** di Keterangan: "1 April" bukan "01 April".

## Contoh Output

Input: `Yokke_Bali_16_April.xlsx` (25 transaksi tgl 16 April 2026)

```
Row | Tanggal    | Keterangan                                         | MID         | Cabang | Tagihan   | Admin  | Nominal   | Nama Toko      | Jumlah_C | TRXTIME | Issuer  | Ref Number
----+------------+----------------------------------------------------+-------------+--------+-----------+--------+-----------+----------------+----------+---------+---------+--------------
3   | 16/04/2026 | Terima Penjualan EDC Mandiri Zuma Gianyar 16 April | 71916642985 | Bali   | 120,000   | 840    | 119,160   | Zuma Gianyar   | 119,160  | 092523  | Mandiri | 610609865578
4   | 16/04/2026 | Terima Penjualan EDC Mandiri Zuma Gianyar 16 April | 71916642985 | Bali   | 119,000   | 833    | 118,167   | Zuma Gianyar   | 118,167  | 092804  | Danamon | 610609885986
5   | 16/04/2026 | Terima Penjualan EDC Mandiri Zuma Gianyar 16 April | 71916642985 | Bali   | 579,000   | 4,053  | 574,947   | Zuma Gianyar   | 574,947  | 105623  | BRI     | 610610686286
...
27  | 16/04/2026 | Terima Penjualan EDC Mandiri Zuma Mataram 16 April | 71916645598 | Lombok | 120,000   | 840    | 119,160   | Zuma Mataram   | 119,160  | 193929  | Dana    | ...
28  | TOTAL      |                                                    |             |        | 5,704,000 | 39,928 | 5,664,072 |                | 5,664,072|         |         |
```

## Dependencies

- `pandas`, `openpyxl` (XLSX read/write)
- Untuk fetch Google Sheets: `google-api-python-client` + `google-auth` (Cara C), atau akses internet ke `docs.google.com` (Cara B)
- Python 3.10+

## Saat User Minta Variasi

- **"upload Yokke beberapa hari sekaligus"** → loop per file, concat dataframes, satu sheet gabungan. Kolom `Tanggal Transaksi` membedakan hari. Tambahkan subtotal per tanggal kalau perlu.
- **"MID baru belum kedetect"** → user update Google Sheets `Master EDC Bank` (tambah row: MID + Nama Toko di EDC + Cabang). Rerun skill — sync otomatis.
- **"bandingkan dengan settlement bank / Acc_Statement"** → di luar scope skill ini. Minta upload Acc_Statement Mandiri + pakai skill terpisah untuk reconciliation T+1.
- **"export per toko"** → group by `MID`, simpan per toko di sheet terpisah atau file terpisah.
- **"total per cabang"** → groupby `Cabang`, sum Tagihan/Admin/Nominal. Tambah sheet `Summary by Cabang`.
- **"summary per issuer"** → groupby `Issuer`, count + sum. Berguna untuk analisa payment method mix (QRIS vs credit card).
