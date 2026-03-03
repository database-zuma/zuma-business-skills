# Troubleshooting — build_ro_request.py

Catatan bug & fix yang pernah terjadi. Referensi untuk debugging di masa depan.

---

## BUG-001: Row Index Offset Setelah Tambah Kolom SQL (2026-03-03)

**Commit fix**: `cbde999`
**Commit penyebab**: `2e0af57`, `d37c98d`

### Gejala

- **Tier = 0 untuk semua artikel** (seharusnya T1–T8)
- **RO Box = 500+ box** (seharusnya puluhan)
- Output Excel: kolom Tier isinya 0 semua, jumlah box tidak masuk akal

### Root Cause

Saat menambah kolom `kode_kecil` ke SQL SELECT sebagai `row[1]`, semua kolom setelahnya bergeser +1 posisi. Tapi Python row parsing hanya sebagian yang di-update — `article` dan `gender` sudah benar, tapi `series`, `tier_raw`, `size_values`, dan `box_val` masih pakai index lama.

**SQL SELECT order setelah perubahan:**
```
row[0] = article_mix
row[1] = kode_kecil    ← BARU (sisipan)
row[2] = article
row[3] = gender
row[4] = series
row[5] = tier
row[6:6+n] = size columns
row[6+n] = box
```

**Python yang SALAH (commit d37c98d):**
```python
article_mix = row[0]   # ✅
kode_kecil  = row[1]   # ✅
article     = row[2]   # ✅
gender      = row[3]   # ✅
series      = row[3]   # ❌ duplikat gender, harusnya row[4]
tier_raw    = row[4]   # ❌ baca series (string), harusnya row[5]
size_values = row[5:5+n] # ❌ geser 1, harusnya row[6:6+n]
box_val     = row[5+n]   # ❌ geser 1, harusnya row[6+n]
```

**Efek domino:**
1. `tier_raw` baca kolom `series` (string seperti "BT") → `to_float("BT")` → 0 → **tier = 0**
2. Tier = 0 artinya semua artikel dianggap tier tidak dikenal → logic filter tier tidak jalan → **semua artikel qualify untuk RO Box**
3. `size_values` baca slice yang geser 1 kolom → total pairs salah → **RO Box count membengkak**

### Fix

Geser 4 baris ke posisi yang benar:

```python
series      = row[4]           # was row[3]
tier_raw    = row[5]           # was row[4]
size_values = row[6:6 + n]     # was row[5:5+n]
box_val     = row[6 + n]       # was row[5+n]
```

### Cara Verifikasi

Jalankan RO Request dan cek output Excel:
- Kolom "Tier" di sheet Daftar RO Box harus berisi T1–T8 (bukan 0)
- Jumlah total box harus puluhan (bukan ratusan)
- Cross-check dengan DB: `SELECT DISTINCT tier FROM portal.planogram_existing_q1_2026 WHERE store_name ILIKE '%royal plaza%'` → harus ada tier 1,2,3,4,5,8

### Pelajaran

**⚠️ ATURAN WAJIB: Saat menambah kolom ke SQL SELECT, SEMUA `row[N]` setelahnya HARUS digeser +1.**

Checklist saat tambah kolom baru:
1. Tambah kolom di SQL query
2. Tambah variabel baru di Python (`kode_kecil = row[N]`)
3. **Geser SEMUA variabel setelahnya** — jangan cuma yang langsung dibawah
4. Cari `row[` di seluruh file untuk pastikan tidak ada yang terlewat
5. Cek juga slicing (`row[X:X+n]`) dan offset (`row[X+n]`) — ini sering terlewat karena bukan pattern `row[digit]` biasa
6. Test dengan 1 toko, verifikasi tier dan box count masuk akal sebelum push

---

*Tambahkan bug baru di bawah dengan format yang sama (BUG-002, dst).*
