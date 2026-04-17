---
name: agent-ar-mandiri-1
description: "Workflow rekonsiliasi Accounts Receivable (AR) Zuma Indonesia untuk rekening Bank Mandiri 560 (No. Rek 1420056089898) yang menerima settlement EDC Yokke. Gunakan skill ini setiap kali user meng-upload Account Statement Mandiri (.xls dengan nama `Acc_Statement_1420056089898_*`), Merchant Statement Yokke (nama file `Yokke_*.xlsx` atau `MSR_*`), atau menyebut `Buku Bank Mandiri 560` / `Master 560`. Juga trigger saat user minta output format `Extracting_finance_data`, minta parsing transaksi EDC per merchant, mapping MID ke Nama Toko/Cabang, atau ekstraksi Tagihan/Admin (MDR)/Nominal Setelah Admin dari Yokke. Trigger walau user hanya menyebut keyword seperti `acc statement`, `yokke bali`, `merchant statement`, `extracting finance`, `settlement EDC Mandiri`, `rekap AR Mandiri`, atau minta buatkan keterangan format `Terima Penjualan EDC Mandiri [Toko] [Tgl]`."
---

# Agent AR Mandiri 1 — Rekonsiliasi EDC Yokke ke Rek Mandiri 560

## Konteks Bisnis

Zuma Indonesia memiliki rekening Bank Mandiri **1420056089898** (KCP Kuta Raya, Bali) sebagai penampung settlement EDC Yokke untuk toko-toko di wilayah **Bali & Lombok**. Alur uang:

1. Customer bayar di toko via EDC card atau QRIS → masuk rekening Yokke `0000029511812`
2. Yokke settle T+1 ke rekening merchant 1420056089898 (agregat per MID per hari, sudah potong MDR)
3. Tim Finance rekonsiliasi: cocokkan Acc_Statement (agregat) dengan Merchant Statement Yokke (detail transaksi)

Output skill ini adalah spreadsheet `Extracting_finance_data` yang menggabungkan kedua sumber, dengan detail Tagihan/MDR/Net dari Yokke dan lookup Nama Toko/Cabang dari Master 560.

## Input Files

User hanya perlu upload 2 file:

| File | Format | Isi |
|---|---|---|
| `Acc_Statement_1420056089898_*.xls` | Binary XLS (Mandiri eStatement) | Semua mutasi rekening periode tertentu |
| `Yokke_*.xlsx` atau `MSR_*` | XLSX dengan CSV-in-cell | Detail transaksi EDC per tanggal (AMOUNT, MDR, NET) |

**Master 560 (MID mapping) — referensi permanen di Google Sheets:**

- **Nama sheet**: "Master EDC Bank"
- **URL**: <https://docs.google.com/spreadsheets/d/1zmnWj_tGVRrHMktH3D7Zj1HAIZ3QUlksVocjpw0AywI/edit?gid=1504130740>
- **Document ID**: `1zmnWj_tGVRrHMktH3D7Zj1HAIZ3QUlksVocjpw0AywI`
- **GID tab Master 560**: `1504130740`
- **Owner**: finance@zuma.id

Skill ini auto-fetch Master 560 dari Google Sheets — user TIDAK perlu upload file Buku Bank lagi. Kalau user upload file `Buku_Bank_Mandiri_560_*.xlsx`, abaikan dan tetap pakai Google Sheets sebagai source of truth (supaya mapping selalu up-to-date).

## Output Format

File `Extracting_finance_data_OUTPUT.xlsx` dengan 2 sheet:

### Sheet 1: `Yokke Detail Apr16` (atau nama sesuai tanggal input)
Dedicated view untuk detail Yokke — satu baris per transaksi individual. Kolom:
`Tanggal Transaksi | Keterangan | MID | Cabang | Tagihan | Admin | Nominal Setelah Admin | Nama Toko | Jumlah_Clean | Tgl Settle | TRXTIME | Issuer | Ref Number`

### Sheet 2: `result` (gabungan Acc_Statement + Yokke)
Semua mutasi Acc_Statement. Baris settlement QRIS yang match dengan Yokke di-*expand* menjadi baris-baris detail Yokke. Kolom:
`Tanggal Transaksi | Keterangan | MID | Cabang | Tagihan | Admin | Nominal Setelah Admin | Nama Toko | Jumlah_Clean | Saldo | Saldo_Clean`

Footer: `Saldo Awal`, `Mutasi Debet`, `Mutasi Kredit`, `Saldo Akhir` (nilai diambil dari summary Acc_Statement).

## Workflow

### Step 1: Fetch Master 560 dari Google Sheets

Master 560 ada di Google Sheets (tidak perlu upload). Ada 2 cara fetch, tergantung environment:

**Cara A — via Google Drive MCP / connector** (preferred kalau tersedia):
```python
# Pakai google_drive_search atau google_drive_fetch dengan document_id:
#   1zmnWj_tGVRrHMktH3D7Zj1HAIZ3QUlksVocjpw0AywI
# Kalau tool support spreadsheet read, target sheet dengan gid=1504130740
```

**Cara B — Export sebagai CSV via public URL** (fallback, butuh sheet publik atau OAuth):
```python
import pandas as pd
DOC_ID = "1zmnWj_tGVRrHMktH3D7Zj1HAIZ3QUlksVocjpw0AywI"
GID = "1504130740"
url = f"https://docs.google.com/spreadsheets/d/{DOC_ID}/export?format=csv&gid={GID}"
master = pd.read_csv(url)
```

**Cara C — API langsung** (OpenClaw / production):
Pakai Google Sheets API v4 dengan service account kredensial `finance@zuma.id`:
```
GET https://sheets.googleapis.com/v4/spreadsheets/{DOC_ID}/values/Master 560!A:H
```

Setelah dapat dataframe, build lookup:
```python
master['MID'] = master['MID'].astype(str).str.strip()
mid_map = {r['MID']: {
    'Nama Toko': r['Nama Toko di EDC'],
    'Cabang': r['Cabang'],         # 'Bali' atau 'Lombok'
    'Term ID': r['Term ID']
} for _, r in master.iterrows()}
```

**Kolom yang dipakai dari Master 560**: `MID` (11 digit), `Nama Toko di EDC`, `Cabang`, `Term ID`. Kolom lain (`Nama Departemen`, `Jenis EDC`, `Alamat EDC`, `Alamat Email Terdaftar`) optional — tidak dipakai di pipeline ini.

### Step 2: Parse Yokke Merchant Statement
File Yokke adalah XLSX 1 kolom berisi baris-baris CSV. Struktur:
- Baris 1–5: metadata (MERCHANT STATEMENT, Report Date, Group, dll)
- Baris 6: header CSV (`NMID,MID,Merchant Official,Trading Name,...,AMOUNT,MDR Amount,NET AMOUNT`)
- Baris 7–N: **detail transaksi** (real data, TRXDATE = tanggal transaksi)
- Baris `TOTAL`: grand total (skip)
- Baris `SUMMARY GROUP` dan di bawahnya: **rekap per merchant dengan PAYMENT DATE = settlement date** (skip — bukan detail transaksi)

Parsing:
```python
import csv
from io import StringIO
raw = pd.read_excel(yokke_path, header=None, dtype=str)
rows = []
header_row = next(i for i,r in raw.iterrows() if 'NMID' in str(r[0]))
for i in range(header_row, len(raw)):
    line = raw.iloc[i,0]
    if pd.isna(line) or not str(line).strip(): continue
    for parsed in csv.reader(StringIO(str(line))):
        if parsed and parsed[0].strip(): rows.append(parsed)
yokke_df = pd.DataFrame(rows[1:], columns=rows[0])
# ONLY keep rows where MID is 11-digit (excludes TOTAL and SUMMARY header)
yokke_df = yokke_df[yokke_df['MID'].astype(str).str.match(r'^\d{11}$', na=False)]
```

Convert AMOUNT/MDR/NET: strip comma → float. Parse TRXDATE as `%d-%m-%Y`.

**Filter lagi**: simpan hanya baris dengan AMOUNT > 0 (summary rows punya AMOUNT kosong walau MID 11 digit).

### Step 3: Parse Acc_Statement
XLS Mandiri eStatement — layout 16 kolom, header di row 11, data mulai row 12:

| Col Index | Field |
|---|---|
| 1 | Posting Date (format `DD/MM/YYYY HH:MM:SS`) |
| 4 | Remark |
| 7 | Reference No |
| 9 | Debit |
| 11 | Credit |
| 15 | Balance |

Metadata (Opening Balance, Closing Balance, No of Debit/Credit, Total Amount Debited/Credited) ada di baris-baris terakhir — scan untuk label.

Butuh `xlrd >= 2.0.1`:
```python
pd.read_excel('Acc_Statement_*.xls', header=None, dtype=str)
```

### Step 4: Extract MID dari Remark
Dua pola utama di Remark Acc_Statement:

**Pattern A — EDC Credit Card**: `71916643508/ZUMA KESIMAN/DPS    DR 0000029511812 KR 1420056089898 99106`
```regex
^(\d{11})/
```

**Pattern B — QRIS**: `7191664322999999999111111111111QRZUMA KA DR 0000029511812 KR ...`
(11 digit MID + padding `9+1+` + `QR` + nama toko terpotong)
```regex
^(\d{11})9+1+QR
```

Fallback: `^(\d{11})`. Jika tidak match, MID = None (transaksi non-EDC seperti TRSF E-BANKING, biaya admin, dll — skill ini fokus ke EDC).

### Step 5: Build Yokke Detail Lookup (untuk expand)
Settlement T+1 artinya Yokke TRXDATE + 1 hari = Acc_Statement Posting Date.

```python
yokke_detail = {}  # key = (MID, settlement_date), value = list of Yokke detail rows
for _, r in yokke_df.iterrows():
    settle = r['TRXDATE_parsed'] + pd.Timedelta(days=1)
    key = (r['MID'], settle.date())
    yokke_detail.setdefault(key, []).append({
        'TRXDATE': r['TRXDATE_parsed'], 'TRXTIME': r['TRXTIME'],
        'Issuer': r['Issuer Name'], 'Ref': str(r['Refference Number']).lstrip("'"),
        'AMOUNT': r['AMOUNT_num'], 'MDR': r['MDR_num'], 'NET': r['NET_num'],
    })
```

### Step 6: Iterate Acc_Statement, Expand Matching Rows

Untuk setiap baris Acc_Statement:

1. Extract MID, lookup Cabang & Nama Toko dari `mid_map`
2. Cek apakah baris ini QRIS (`^\d{11}9+1+QR` match) DAN `(MID, posting_date)` ada di `yokke_detail` DAN sum of NET ≈ Credit → **expand**
3. Kalau expand: ganti 1 baris ini dengan N baris Yokke detail, setiap baris punya Tagihan=AMOUNT, Admin=MDR, Nominal=NET individual
4. Kalau tidak: keep 1 baris, Tagihan/Admin/Nominal = None

Running balance pada baris Yokke di-increment per NET supaya totalnya sama dengan Credit aslinya → Saldo Akhir tetap tie-out.

### Step 7: Generate Keterangan
Format standar: `Terima Penjualan EDC Mandiri {Nama Toko} {tanggal transaksi ID}`

Tanggal transaksi = posting date − 1 hari (karena settlement T+1).

Format tanggal Indonesia (tanpa leading zero):
```python
BULAN = {1:'Januari', 2:'Februari', 3:'Maret', 4:'April', 5:'Mei', 6:'Juni',
         7:'Juli', 8:'Agustus', 9:'September', 10:'Oktober', 11:'November', 12:'Desember'}
f"{dt.day} {BULAN[dt.month]}"   # e.g., "31 Maret", "16 April"
```

Contoh output:
- Posting `01/04/2026` → `Terima Penjualan EDC Mandiri Zuma Kesiman 31 Maret`
- Posting `17/04/2026` (Yokke rows) → `Terima Penjualan EDC Mandiri Zuma Gianyar 16 April`

### Step 8: Write Excel Output

Urutan kolom final di sheet `result`:
1. Tanggal Transaksi (date, format `dd/mm/yyyy`)
2. Keterangan (format `Terima Penjualan EDC Mandiri ...`)
3. MID (text `@`, 11 digit)
4. Cabang (`Bali` / `Lombok`)
5. Tagihan (number) — dari Yokke AMOUNT
6. Admin (number) — dari Yokke MDR Amount
7. Nominal Setelah Admin (number) — dari Yokke NET AMOUNT
8. Nama Toko — dari Master 560 `Nama Toko di EDC`
9. Jumlah_Clean (number, + untuk CR, − untuk DB)
10. Saldo (number)
11. Saldo_Clean (number)

Styling (opsional tapi recommended):
- Header row: font Arial bold white, fill dark blue `305496`
- Baris Yokke detail: fill hijau pucat `E8F4D9`
- Baris TOTAL (di sheet Yokke Detail): fill kuning pucat `FCE4A6`
- Number format: `#,##0.00` untuk kolom numerik, `@` untuk MID, `dd/mm/yyyy` untuk tanggal
- Freeze pane di row 2 (`A2`)
- Column width: A=18, B=85, C=14, D=10, E=14, F=12, G=20, H=20, I=16, J=16, K=16

## Reconciliation (WAJIB setelah generate)

Tie-out berikut harus selalu match — kalau tidak, ada bug di parsing:

1. `sum(Jumlah_Clean)` = `Total Amount Credited − Total Amount Debited` (dari footer Acc_Statement)
2. `Saldo baris terakhir` = `Closing Balance` (dari footer Acc_Statement)
3. `Opening Balance + sum(Jumlah_Clean)` = `Closing Balance`
4. `sum(Tagihan Yokke) − sum(Admin Yokke)` = `sum(Nominal Setelah Admin Yokke)`
5. `sum(Yokke NET by MID)` ≈ Credit di Acc_Statement baris settlement yang di-expand (selisih < Rp 1)

Kalau salah satu failed → print warning, JANGAN silent.

## Edge Cases & Gotchas

- **Yokke file hanya berisi sebagian tanggal**: normal. Baris Acc_Statement di tanggal yang tidak ada di Yokke akan punya Tagihan/Admin/Nominal kosong. JANGAN fabrikasi data.
- **MID di Yokke 11 digit, di Acc_Statement juga 11 digit** — match langsung, tidak perlu truncate.
- **Ada baris `SUMMARY GROUP` di Yokke dengan PAYMENT DATE = settlement date**. Baris ini punya MID 11 digit TAPI kolom AMOUNT/MDR/NET kosong — pastikan di-filter (gunakan AMOUNT > 0).
- **Format Remark berubah di hari berbeda**: Apr 1–16 suffix `DR 0000029511812 KR 1420056089898 99106`, Apr 17+ suffix `CC Merchant Paymt SA DR 000002...`. Regex MID tetap sama (11 digit di awal).
- **CC Merchant settlement (non-QRIS)** pada settlement date biasanya TIDAK ada di Yokke file yang user kasih — Yokke file sering hanya cover QRIS. Jangan paksa match; biarkan Tagihan/Admin kosong.
- **Baris tanpa MID** (TRSF E-BANKING, BA JASA BCA VA, pajak otomatis, dll): tetap dimasukkan ke output, kolom MID/Cabang/Nama Toko kosong, Keterangan = Remark asli dari Acc_Statement.
- **Nama bulan dalam Bahasa Indonesia**, bukan Inggris. "Maret" bukan "March".
- **Tanggal tanpa leading zero**: "1 April" bukan "01 April" (match gaya LBH sheet Buku Bank).

## Contoh Lengkap Keluaran

Input: Acc_Statement Apr 01–17 2026 + Yokke Bali 16 April

```
Row | Tanggal    | Keterangan                                         | MID         | Cabang | Tagihan   | Admin  | Nominal   | Nama Toko        | Jumlah_C  | Saldo
----+------------+----------------------------------------------------+-------------+--------+-----------+--------+-----------+------------------+-----------+----------------
2   | 01/04/2026 | Terima Penjualan EDC Mandiri Zuma Kesiman 31 Maret | 71916643508 | Bali   |           |        |           | Zuma Kesiman     | 118,800   | 670,989,255.53
3   | 01/04/2026 | Terima Penjualan EDC Mandiri Zuma Level 21 31 Maret| 71916643887 | Bali   |           |        |           | Zuma Level 21    | 198,701   | 671,187,956.53
...
170 | 17/04/2026 | Terima Penjualan EDC Mandiri Zuma Gianyar 16 April | 71916642985 | Bali   | 120,000   | 840    | 119,160   | Zuma Gianyar     | 119,160   | 797,138,759.53
171 | 17/04/2026 | Terima Penjualan EDC Mandiri Zuma Gianyar 16 April | 71916642985 | Bali   | 119,000   | 833    | 118,167   | Zuma Gianyar     | 118,167   | 797,256,926.53
...
```

Footer:
```
Saldo Awal    : 670,870,455.53
Mutasi Debet  : 0.00                0
Mutasi Kredit : 133,416,640.00      176
Saldo Akhir   : 804,287,095.53
```

## Dependencies

- `pandas`, `openpyxl` (XLSX read/write)
- `xlrd >= 2.0.1` (untuk `.xls` Mandiri eStatement) → `pip install xlrd --break-system-packages`
- Python 3.10+

## Saat User Minta Variasi

- **"tambahkan data hari X"** → minta file Yokke untuk tanggal X, rerun pipeline. Baris yang sebelumnya kosong akan terisi otomatis.
- **"bagaimana cek keseragaman dengan Buku Bank 560 LBH"** → sheet `LBH Apr` / `LBH Mar` dst biasanya ada di workbook yang sama di Google Drive (cari di folder finance@zuma.id). Format mirip tapi sudah termasuk jurnal akuntansi (SIR/SI faktur, COA 110.12). Gunakan sebagai cross-check bukan input primer.
- **"ganti Cabang jadi kode numerik"** → user mungkin merujuk template lama yang pakai 411/960/998 (kode jenis transaksi bank lain, bukan cabang). Konfirmasi dulu sebelum ganti — default pakai Bali/Lombok dari Master 560.
- **"export per toko"** → tambahkan sheet per toko (pivot by Nama Toko), atau filter sheet `result` berdasarkan MID.
- **"MID baru belum kedetect"** → kemungkinan toko baru belum ada di Master EDC Bank. Suruh user update Google Sheets dulu (tambah row baru dengan MID + Nama Toko + Cabang), lalu rerun skill — data otomatis ter-sync karena skill fetch live dari Sheets.
