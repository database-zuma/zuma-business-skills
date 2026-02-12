# Investigasi Transaksi Affiliasi (Inter-Company)

**Terakhir diupdate:** 9 Feb 2026
**Status:** Sudah ter-flag di `core.sales_with_product` via kolom `is_intercompany`
**Default:** Semua tabel `mart.*` EXCLUDE transaksi ini. Tabel `core.*` tetap INCLUDE (dengan flag).

---

## Apa Itu Transaksi Affiliasi?

Zuma punya 4 entitas bisnis (DDD, MBB, UBB, LJBB) yang masing-masing punya database Accurate Online sendiri. Kadang, entitas satu "menjual" ke entitas lain di atas kertas — bukan penjualan nyata ke customer, tapi transfer antar entitas untuk keperluan perpajakan.

**Kenapa ini masalah untuk data?**
- Kalau semua entitas dijumlah tanpa filter, revenue jadi **double-counting**
- DDD catat "jual" ke MBB → MBB catat "jual" ke end customer → 1 transaksi dihitung 2x
- Total inflasi revenue: **Rp 15.21 Bn** (dari total Rp 231 Bn = ~6.6%)

---

## Daftar Lengkap Transaksi Affiliasi

Deteksi dilakukan berdasarkan **exact match** kolom `nama_pelanggan` di raw sales tables.

| Source Entity | Nama Pelanggan (exact) | Sebenarnya Entity | Total Rows | Total Pairs | Revenue (Bn) | Invoices |
|---|---|---|---|---|---|---|
| **DDD** | `CV MAKMUR BESAR BERSAMA` | MBB | 45,366 | 163,809 | Rp 9.53 | 778 |
| **DDD** | `CV. UNTUNG BESAR BERSAMA` | UBB | 28,453 | 120,238 | Rp 5.65 | 640 |
| **DDD** | `CV Lancar Jaya Besar Bersama` | LJBB | 158 | 288 | Rp 0.02 | 9 |
| **MBB** | `PT Dream Dare Discover` | DDD | 41 | 87 | Rp 0.01 | 2 |
| **UBB** | `CV. Makmur Besar Bersama` | MBB | 6 | 12 | Rp 0.00 | 1 |
| | | **TOTAL** | **74,024** | **284,434** | **Rp 15.21** | **1,430** |

### Entitas yang TIDAK ditemukan transaksi affiliasi:
- MBB tidak punya transaksi ke UBB atau LJBB
- UBB tidak punya transaksi ke DDD atau LJBB
- LJBB tidak punya tabel sales (hanya entitas penerimaan PO)

---

## Profil Transaksi: Intercompany vs Real

| Metrik | Intercompany | Real Sales | Catatan |
|--------|-------------|------------|---------|
| Total rows | 74,024 | 1,471,280 | 4.8% dari total rows |
| Total pairs | 284,434 | 2,569,610 | 10.0% dari total pairs |
| Revenue | Rp 15.21 Bn | Rp 216.25 Bn | 6.6% dari total revenue |
| ASP (avg selling price) | **Rp 53,469** | **Rp 84,157** | Intercompany dijual jauh lebih murah |
| Avg pairs per invoice | **198.9** | **9.8** | Intercompany = bulk transfer, bukan retail |
| Unique invoices | 1,430 | 263,483 | Sedikit invoice, tapi volume besar |

**Pola khas intercompany:**
- ASP jauh di bawah harga retail (Rp 53K vs Rp 84K)
- Jumlah pairs per invoice sangat besar (~200 pasang vs ~10 pasang)
- Ini konsisten dengan "transfer stok" bukan "jualan ke customer"

---

## Breakdown per Tahun

| Tahun | Revenue Intercompany | Revenue Real | % Fake dari Total |
|-------|---------------------|-------------|-------------------|
| 2022 | Rp 0.00 Bn | Rp 23.65 Bn | 0.0% |
| 2023 | Rp 1.61 Bn | Rp 37.54 Bn | 4.1% |
| 2024 | Rp 2.87 Bn | Rp 59.38 Bn | 4.6% |
| 2025 | Rp 10.54 Bn | Rp 86.99 Bn | **10.8%** |
| 2026 (Jan) | Rp 0.19 Bn | Rp 8.70 Bn | 2.2% |

**Catatan:** Transaksi affiliasi meningkat signifikan di 2025 (10.8% vs 4.6% di 2024). Terutama flow DDD → MBB yang naik drastis di H2 2025.

---

## Breakdown per Tahun per Flow

| Tahun | Flow | Rows | Pairs | Revenue (Bn) | Invoices | Unique Articles |
|-------|------|------|-------|-------------|----------|-----------------|
| 2023 | DDD → UBB | 8,920 | 37,265 | 1.61 | 199 | 169 |
| 2024 | DDD → UBB | 7,748 | 36,584 | 1.65 | 205 | 188 |
| 2024 | DDD → MBB | 11,535 | 21,538 | 1.21 | 225 | 232 |
| 2025 | DDD → MBB | 33,068 | 138,902 | 8.15 | 533 | 297 |
| 2025 | DDD → UBB | 11,677 | 45,905 | 2.36 | 232 | 171 |
| 2025 | DDD → LJBB | 158 | 288 | 0.02 | 9 | 23 |
| 2025 | MBB → DDD | 41 | 87 | 0.01 | 2 | 27 |
| 2025 | UBB → MBB | 6 | 12 | 0.00 | 1 | 1 |
| 2026 | DDD → MBB | 763 | 3,369 | 0.17 | 20 | 82 |
| 2026 | DDD → UBB | 108 | 484 | 0.03 | 4 | 19 |

---

## Trend Bulanan 2025

| Bulan | DDD → MBB (pairs) | DDD → UBB (pairs) | DDD → LJBB | MBB → DDD | UBB → MBB |
|-------|-------------------|-------------------|------------|-----------|-----------|
| Jan | 27,567 | 4,700 | - | - | - |
| Feb | 565 | 4,214 | - | - | - |
| Mar | 3,137 | 6,132 | - | - | - |
| Apr | 4,074 | 4,124 | - | - | - |
| May | 2,275 | 2,208 | - | - | - |
| Jun | 4,473 | 2,444 | 184 | - | - |
| Jul | 7,247 | 4,834 | 104 | - | - |
| Aug | 17,361 | 6,845 | - | - | - |
| Sep | 15,422 | 2,036 | - | - | - |
| Oct | 19,248 | 2,276 | - | 87 | - |
| Nov | 13,760 | 3,208 | - | - | 12 |
| Dec | 23,773 | 2,884 | - | - | - |

**Insight:** DDD → MBB melonjak di Aug-Dec 2025 (peak: Dec 23,773 pairs). Kemungkinan terkait dengan scaling online channel MBB di semester 2.

---

## Top 20 Produk dalam Transaksi Affiliasi

| Kode Mix | Article | Series | Gender | Pairs | Revenue (Mio) | ASP |
|----------|---------|--------|--------|-------|-------------|-----|
| M1SP0PV201 | MEN STRIPE 1 | STRIPE | MEN | 9,373 | 556.9 | 57,475 |
| M1AZSPV207 | MEN STRIPE 7 | STRIPE | MEN | 8,889 | 501.8 | 55,710 |
| SJ1ACAV201 | MEN CLASSIC 1 | CLASSIC | MEN | 7,758 | 455.6 | 54,064 |
| MBLACLV203 | MEN BLACK SERIES 3 | BLACKSERIES | MEN | 4,936 | 282.9 | 55,419 |
| M1AZSPV210 | MEN STRIPE 10 | STRIPE | MEN | 4,799 | 271.7 | 54,990 |
| SJ2ACAV201 | LADIES CLASSIC 1 | CLASSIC | LADIES | 4,747 | 280.1 | 55,140 |
| M1SP0PV202 | MEN STRIPE 2 | STRIPE | MEN | 4,531 | 262.9 | 53,909 |
| MBLACLV206 | MEN BLACK SERIES 6 | BLACKSERIES | MEN | 3,878 | 224.2 | 57,812 |
| M1CA2AV224 | MEN CLASSIC 24 | CLASSIC | MEN | 3,619 | 209.6 | 54,829 |
| M1AZSPV208 | MEN STRIPE 8 | STRIPE | MEN | 3,528 | 198.9 | 56,599 |
| M1AZSPV211 | MEN STRIPE 11 | STRIPE | MEN | 3,375 | 192.6 | 53,019 |
| L3CA2AV222 | LADIES CLASSIC 22 | CLASSIC | LADIES | 3,328 | 193.1 | 54,935 |
| M1SP1PV213 | MEN STRIPE 13 | STRIPE | MEN | 3,254 | 192.7 | 59,322 |
| MBLACLV205 | MEN BLACK SERIES 5 | BLACKSERIES | MEN | 3,124 | 185.3 | 57,991 |
| L2AZCAV225 | LADIES CLASSIC 25 | CLASSIC | LADIES | 2,984 | 171.8 | 55,134 |
| L2AZCAV223 | LADIES CLASSIC 23 | CLASSIC | LADIES | 2,974 | 173.9 | 54,919 |
| M1BL0LV208 | MEN BLACK SERIES 8 | BLACKSERIES | MEN | 2,963 | 180.0 | 56,821 |
| M1CA3AV231 | MEN CLASSIC 31 | CLASSIC | MEN | 2,952 | 165.4 | 53,822 |
| M1CA2AV223 | MEN CLASSIC 23 | CLASSIC | MEN | 2,802 | 158.2 | 53,544 |
| M1CA2AV227 | MEN CLASSIC 27 | CLASSIC | MEN | 2,784 | 159.1 | 55,888 |

**Insight:** Produk yang ditransfer antar entitas didominasi best-seller (Classic, Stripe, BlackSeries) — masuk akal karena ini produk volume tinggi yang perlu didistribusikan ke channel online (MBB) dan wholesale (UBB).

---

## Cara Filter di SQL

### Flag yang tersedia

Kolom `is_intercompany` (boolean) sudah ada di `core.sales_with_product`:

```sql
-- Hanya real sales (exclude intercompany)
SELECT * FROM core.sales_with_product WHERE is_intercompany = FALSE;

-- Hanya intercompany (buat investigasi)
SELECT * FROM core.sales_with_product WHERE is_intercompany = TRUE;

-- Semua data (include both)
SELECT * FROM core.sales_with_product;
```

### Logic deteksi (exact match per entity)

```sql
CASE WHEN (
  (source_entity = 'DDD' AND TRIM(LOWER(nama_pelanggan)) IN (
    'cv makmur besar bersama',
    'cv. untung besar bersama',
    'cv lancar jaya besar bersama'
  ))
  OR (source_entity = 'MBB' AND TRIM(LOWER(nama_pelanggan)) IN (
    'pt dream dare discover'
  ))
  OR (source_entity = 'UBB' AND TRIM(LOWER(nama_pelanggan)) IN (
    'cv. makmur besar bersama'
  ))
) THEN TRUE ELSE FALSE END
```

**PENTING:** Gunakan exact full-name match, JANGAN fuzzy/LIKE. Kata seperti "makmur", "bersama", "untung" umum di nama perusahaan Indonesia — fuzzy match bisa salah exclude customer beneran (contoh: PT. Unggul Sukses Makmur = customer wholesale asli).

---

## Rekomendasi untuk Investigasi Lanjutan

1. **Monitor bulanan** — Cek apakah flow intercompany terus naik di 2026
2. **Cross-check dengan MBB** — Apakah 138K pairs yang "dibeli" MBB dari DDD di 2025 muncul sebagai penjualan MBB ke end customer?
3. **Cek harga transfer** — ASP intercompany Rp 53K vs retail Rp 84K, selisih ~37%. Apakah ini harga HPP atau harga khusus?
4. **LJBB flow baru** — DDD → LJBB baru muncul Jun 2025. Monitor apakah ini pola baru.
5. **Kalau ada entitas/nama pelanggan baru** — Update daftar di `SKILL.md` Rule 7 dan file ini.
