---
name: bst-data-entry
description: "Skill untuk memasukkan data dari foto/gambar Bukti Serah Terima (BST) ke sheet DATA ENTRY di file Excel Update PO Zuma. TRIGGER UTAMA: user mengupload gambar/foto dokumen BST — dokumen kertas bertulisan tangan dengan header 'BUKTI SERAH TERIMA', logo PT. Halimjaya Sakti, tabel berisi kode artikel, warna, jumlah satuan, dan nomor PO. Jika user upload gambar yang terlihat seperti dokumen BST (form serah terima barang, ada kolom Uraian Barang, Jumlah Satuan, Keterangan berisi nomor PO), LANGSUNG gunakan skill ini tanpa bertanya. Trigger juga jika user menyebut 'BST', 'Bukti Serah Terima', 'langsir', 'input BST', 'pake skill bst', 'pake skill bst data entry', atau 'terjemahkan BST ke Excel'. Skill ini membaca tulisan tangan dari foto, mencocokkan kode artikel dengan fuzzy matching, dan menulis data ke format yang benar di sheet DATA ENTRY. File Excel sumbernya: https://docs.google.com/spreadsheets/d/1hJP-hQ79vxO6cj6O0R-VeiAFh5iyO0F-_N3Mpa8TawQ/edit?gid=948056441#gid=948056441"
---

# BST Data Entry Skill

Skill ini mengotomasi proses input data dari foto **Bukti Serah Terima (BST)** PT. Halimjaya Sakti ke sheet **DATA ENTRY** di file Excel **Update PO Zuma**.

## Referensi

Skill ini dilengkapi file referensi. **Baca sebelum mulai bekerja:**

| File | Isi | Kapan Baca |
|------|-----|-----------|
| `references/excel-structure.md` | Struktur lengkap file Excel (sheet, kolom, formula, format, supplier) | **Selalu** — baca pertama kali |
| `references/typo-patterns.md` | Pola koreksi tulisan tangan (kode artikel, nomor PO, qty) | **Selalu** — baca sebelum mencocokkan kode |
| `references/kode_nama.json` | Database 941 kode artikel → nama lengkap (JSON) | Dipakai oleh script lookup |
| `references/po_numbers.json` | Daftar 676 nomor PO yang pernah digunakan (JSON) | Untuk validasi nomor PO |
| `scripts/lookup_kode.py` | Script fuzzy matching kode artikel | Jalankan untuk mencocokkan kode tulisan tangan |

## Alur Kerja

### Step 1: Baca Referensi

```
view references/excel-structure.md
view references/typo-patterns.md
```

### Step 2: Baca Foto BST

Dari foto BST, ekstrak informasi berikut:

**Header BST:**
- **No. BST** — nomor urut (pojok kanan atas)
- **Tanggal** — format DD/MM/YY (pojok kanan atas)
- **Dari bagian** — biasanya "Packing"
- **Ke bagian** — misal "On. A / Zuma"

**Tabel Isi BST (per baris):**

| Kolom BST | Keterangan | Contoh |
|-----------|-----------|--------|
| NO. | Nomor urut | 1, 2, 3... |
| Uraian Barang (kode) | Kode artikel tulisan tangan | M1SPV2162 |
| Uraian Barang (warna) | Nama warna/variant | Cocoa White Tan |
| Satuan | Satuan barang | Box (biasanya dicentang) |
| Jumlah Satuan | Qty, bisa penjumlahan (191+50) | 241 |
| Keterangan | Nomor PO dan progress | PO/DDD/HJS/25/XI/021 (39/44) |

### Step 3: Cocokkan Kode Artikel (Fuzzy Matching)

Jalankan script fuzzy matching untuk setiap kode dari BST:

```bash
python scripts/lookup_kode.py "<kode_tulisan_tangan>" "<warna_hint>"
```

Contoh:
```bash
python scripts/lookup_kode.py M1SPV2162 "Cocoa White Tan"
# Output: 100% [trailing_digit+color] M1SPV216 → MEN STRIPE 16, COCOA WHITE TAN

python scripts/lookup_kode.py LIEAV2102 "Silver Navy"
# Output: 100% [fuzzy+color] L1EAV210 → LADIES ELSA 10, SILVER NAVY
```

Script ini akan:
1. Mencari kecocokan di database 941+ kode artikel
2. Menangani pola typo umum (angka ekstra, huruf mirip)
3. Memberi bonus skor jika warna cocok (cross-check)
4. Mengembalikan top 5 kandidat dengan skor

**Pilih kandidat dengan skor tertinggi.** Jika skor di bawah 80% atau warna tidak cocok, tanyakan ke user.

Jika script tidak tersedia, atau perlu fallback, cari langsung dari file Excel:

```python
import openpyxl, re

def extract_cached(val):
    """Ekstrak nilai cached dari formula Google Sheets."""
    if val and 'COMPUTED_VALUE' in str(val):
        m = re.search(r',\"([^\"]+)\"\)', str(val))
        if m: return m.group(1)
    return str(val) if val else ""

wb = openpyxl.load_workbook('file.xlsx')

# Cari di DATA ENTRY kolom E + F
ws = wb['DATA ENTRY']
for row in range(3, ws.max_row + 1):
    code = str(ws.cell(row=row, column=5).value or "")
    if code == kode_target:
        nama = extract_cached(ws.cell(row=row, column=6).value)
        break

# Atau cari di Master kolom B + D
ws_m = wb['Master']
for row in range(2, ws_m.max_row + 1):
    b = extract_cached(ws_m.cell(row=row, column=2).value)
    if b == kode_target:
        nama = extract_cached(ws_m.cell(row=row, column=4).value)
        break
```

### Step 4: Bersihkan Nomor PO

Baca nomor PO dari kolom Keterangan BST. Bersihkan tulisan tangan (lihat `references/typo-patterns.md`):

| Koreksi Utama | Penjelasan |
|--------------|-----------|
| `(` → `/` | Tanda kurung = garis miring |
| DNN → DDD | Huruf N mirip D |
| HUS → HJS | Huruf U mirip J |
| 2S → 25 | Huruf S mirip 5 |

Validasi PO yang sudah dibersihkan terhadap `references/po_numbers.json` untuk memastikan formatnya benar.

Angka dalam kurung setelah PO (misal `(39/44)`) adalah **progress pengiriman** — **abaikan**, bukan qty.

### Step 5: Hitung Quantity

- Penjumlahan: `191 + 50` → totalkan jadi `241`
- Angka tunggal: gunakan langsung
- Satuan default: Box

### Step 6: Tulis ke Sheet DATA ENTRY

```python
import openpyxl
from datetime import datetime
from copy import copy

wb = openpyxl.load_workbook('Update_PO_Zuma_2026.xlsx')
ws = wb['DATA ENTRY']

# Cari baris data terakhir (kolom A)
last_row = 2
for row in range(3, ws.max_row + 1):
    if ws.cell(row=row, column=1).value is not None:
        last_row = row

start_row = last_row + 1

for i, entry in enumerate(entries):
    r = start_row + i

    # Copy format dari baris terakhir
    for col in range(1, 11):
        ref = ws.cell(row=last_row, column=col)
        cell = ws.cell(row=r, column=col)
        if ref.font: cell.font = copy(ref.font)
        if ref.number_format: cell.number_format = ref.number_format
        if ref.alignment: cell.alignment = copy(ref.alignment)

    ws.cell(row=r, column=1, value=tanggal_bst)              # A: Tanggal (datetime)
    ws.cell(row=r, column=2, value=f'=YEAR(A{r})')           # B: Tahun (formula)
    ws.cell(row=r, column=3, value=f'=TEXT(A{r},"mmmm")')    # C: Month (formula)
    ws.cell(row=r, column=4, value=entry['po'])               # D: Nomor PO (string)
    ws.cell(row=r, column=5, value=entry['kode'])             # E: Kode (string)
    ws.cell(row=r, column=6, value=entry['nama'])             # F: Nama Artikel (string teks)
    ws.cell(row=r, column=7, value=float(entry['qty']))       # G: Qty (float)
    ws.cell(row=r, column=8, value=f'=IFERROR(IF(G{r}>0,"Langsir",""),"")') # H: Keterangan
    ws.cell(row=r, column=9, value=entry['supplier'])         # I: Supplier (string)
    ws.cell(row=r, column=10, value=entry['no_bst'])          # J: No BST (integer)

wb.save('output.xlsx')
```

### Step 7: Recalculate & Verify

```bash
python /mnt/skills/public/xlsx/scripts/recalc.py output.xlsx 60
```

Kemudian verifikasi:

```python
wb2 = openpyxl.load_workbook('output.xlsx', data_only=True)
ws2 = wb2['DATA ENTRY']
for row in range(start_row, start_row + len(entries)):
    print(f"Row {row}:", [ws2.cell(row=row, column=c).value for c in range(1, 11)])
```

**Error yang sudah ada sebelumnya** di sheet lain (`#NAME?`, `#N/A` dari IMPORTRANGE) bisa diabaikan — fokus hanya pada baris baru.

### Step 8: Sajikan Hasil ke User

Tampilkan ringkasan data yang dimasukkan (tabel kode, nama, qty, PO) dan berikan file output.

## Catatan Penting

- **Kolom F**: Isi dengan teks nama artikel (bukan formula IMPORTRANGE, karena tidak berfungsi di luar Google Sheets)
- **Supplier default**: `HJS` untuk BST dari PT. Halimjaya Sakti. Lihat `references/excel-structure.md` untuk daftar supplier lain
- **Jika ragu**: Selalu tanyakan ke user — lebih baik konfirmasi daripada salah input
- **Multiple BST**: Jika user upload beberapa foto BST sekaligus, proses satu per satu dan gabungkan semua entry ke Excel
