# Planogram Output Specification

> This file contains the full XLSX output specification including sheet layouts,
> column formats, storage allocation tables, summary report metrics, and comparison specs.
> Referenced from SKILL.md Section 1.9 and planogram-algorithm.md Section 2.7.

---

## 1. Planogram Sheet (Output Utama)

```
Buat 1 XLSX file dengan multiple sheets:

SHEET 1: "Planogram -- [Store Name]"
  Layout yang mirror fisik toko.
  
  Untuk setiap display component, buat section:
  
  === BACKWALL 1: Men Jepit (30 hooks) -- Full Box Mode ===
  
  | Hook 1-2      | Hook 3-4      | Hook 5-6      | ... | Hook 29-30     |
  |---------------|---------------|---------------|-----|----------------|
  | Men Classic 25| Men Classic 30| Men Stripe 8  | ... | Men Stripe 14  |
  | T1 | Avg: 50  | T1 | Avg: 45 | T1 | Avg: 39 | ... | T2 | Avg: 15  |
  
  Catatan:
  - Jepit full box = 2 kolom bersebelahan (merged cells atau label span)
  - Fashion full box = 3 kolom bersebelahan
  - Compact mode = jumlah kolom berkurang sesuai mode
  - Color code: T1 = hijau, T8 = biru, T2 = kuning, T3 = abu-abu
  
  === TABLE DISPLAY (4 artikel) ===
  | Slot 1    | Slot 2    | Slot 3     | Slot 4     |
  |-----------|-----------|------------|------------|
  | Men Luca 1| Ladies Luna 2 | Ladies Luna 3 | Men Luca 3 |
  
  === RAK BABY (3 layer, compact mode) ===
  | Layer | Slot A          | Slot B          |
  |-------|-----------------|-----------------|
  | 1     | Baby Classic 5  | Baby Classic 7  |
  | 2     | Baby Velcro 1   | Baby Velcro 3   |
  | 3     | Baby Cocomelon 1| Baby Batman 1   |
```

### Planogram Sheet Format Details

- 1 sheet per display component
- Row 1: Nama display + gender-type
- Row 2: Sub-series grouping (jika applicable)
- Row 3: Hook/slot labels
- Row 4+: Artikel per hook, color-coded by gender-type

Hook span per article type:
- Artikel jepit full box: **2 kolom bersebelahan** (= 1 box = 2 hooks)
- Artikel jepit compact: **1 kolom** (= 1/2 box = 1 hook, sisa 6 pairs ke storage)
- Artikel fashion full box: **3 kolom bersebelahan** (= 1 box = 3 hooks)
- Artikel fashion compact: **2 kolom bersebelahan** (= 2/3 box = 2 hooks, sisa 4 pairs ke storage)

---

## 2. Storage Allocation Table

```
SHEET 2: "Storage Allocation"

| No | KODEMIX | Article Name       | Gender-Type    | Tier | Adj_Avg | Boxes | Pairs | Alasan                    |
|----|---------|-------------------|----------------|------|---------|-------|-------|---------------------------|
| 1  | M1LU01  | Men Luca 1        | Men Fashion    | T1   | 35.2    | 1     | 11    | Table display backup      |
| 2  | L2LN02  | Ladies Luna 2     | Ladies Fashion | T1   | 28.5    | 1     | 11    | Table display backup      |
| 3  | M1CA25  | Men Classic 25    | Men Jepit      | T1   | 50.5    | 2     | 24    | Highest sales, extra stock |
| 4  | L1CA22  | Ladies Classic 22 | Ladies Jepit   | T1   | 42.1    | 2     | 24    | High sales                |
| 5  | M2DA03  | Men Dallas 3      | Men Fashion    | T1   | 20.3    | 0*    | 4     | *Compact mode overflow    |
| ...                                                                                                          |
|    |         |                   |                |      | TOTAL   | 18/20 |       | 90% storage utilization   |
```

### Storage Allocation Table Columns

| Column | Keterangan |
|--------|-----------|
| No | Nomor urut |
| KODEMIX | Kode artikel |
| Article Name | Nama lengkap artikel |
| Gender-Type | Gender-type assignment (Men Jepit, Ladies Fashion, etc.) |
| Tier | Tier baru (T1/T2/T3/T8) |
| Adj_Avg | Adjusted average sales per bulan |
| Boxes | Jumlah box dialokasikan (0* = compact overflow saja) |
| Pairs | Total pairs di storage |
| Alasan | Justifikasi alokasi |

---

## 3. Summary Report

```
SHEET 3: "Summary Report"

=== DISPLAY UTILIZATION ===
Total hooks/slots available : 120
Total hooks/slots used      : 112
Utilization                 : 93%
Empty slots                 : 8 (available for expansion)

=== SALES COVERAGE ===
Total adjusted avg (semua artikel toko ini) : 1,200 pairs/bulan
Adjusted avg dari artikel di display        : 1,080 pairs/bulan
Sales coverage                              : 90%

=== TIER DISTRIBUTION DI DISPLAY ===
| Tier | Count | % of Display | Notes                    |
|------|-------|-------------|--------------------------|
| T1   | 28    | 65%         | All T1 displayed [OK]    |
| T8   | 5     | 12%         | 5 of 6 T8 displayed      |
| T2   | 8     | 19%         | Filler                   |
| T3   | 2     | 5%          | Variety filler            |

=== STORAGE UTILIZATION ===
Total capacity  : 20 box
Used            : 18 box
Remaining       : 2 box
Breakdown:
  - Luca/Luna/Airmove backup : 4 box
  - Compact mode overflow    : 3 box (36 pairs equivalent)
  - T1 fast moving backup    : 9 box
  - T8 rotation stock        : 2 box

=== FLAGS & WARNINGS ===
CRITICAL:
  - (none)

WARNING:
  - T8 "Men Onyx Z 12" tidak masuk display (slot penuh, rank 6 of 5 available)
  - Storage 90% -- mendekati penuh

POSITIVE:
  - Semua T1 terdisplay [OK]
  - Tidak ada T4/T5 di display [OK]
  - Sales coverage 90% [OK]
```

### Summary Report Required Sections

Wajib sertakan:
- Total artikel di display vs total slot capacity (utilization %)
- Sales coverage: % dari total sales yang tercakup oleh artikel di display
- Tier distribution di display (berapa T1/T2/T3/T8)
- Storage utilization vs capacity
- **Flags/Warnings:**
  - T1 yang TIDAK masuk display (critical issue)
  - T4/T5 yang MASIH di display (perlu dikeluarkan)
  - Slot kosong yang bisa diisi
  - Storage overflow risk

---

## 4. Comparison vs Existing (Opsional)

```
SHEET 4: "Changes vs Current" (hanya jika data planogram existing tersedia)

=== ARTIKEL BARU MASUK DISPLAY ===
| KODEMIX | Article         | Tier | Adj_Avg | Masuk ke       | Alasan              |
|---------|----------------|------|---------|----------------|---------------------|
| M1ON04  | Men Onyx 4     | T8   | 22.0    | BW-1 hook 25-26| New launch, exposure |

=== ARTIKEL KELUAR DARI DISPLAY ===
| KODEMIX | Article         | Tier | Adj_Avg | Sebelumnya di  | Alasan              |
|---------|----------------|------|---------|----------------|---------------------|
| M1CA23  | Men Classic 23 | T4   | 2.1     | BW-1 hook 25-26| Slow moving, replace |

=== ARTIKEL PINDAH POSISI ===
| KODEMIX | Article         | From          | To            | Alasan              |
|---------|----------------|---------------|---------------|---------------------|
| M1CA25  | Men Classic 25 | BW-1 hook 15  | BW-1 hook 1-2 | Top seller -> hot zone|

=== EXPECTED IMPACT ===
Artikel ditambah ke display: +X% estimated sales uplift (based on historical display-to-sales correlation)
Artikel dipindah ke hot zone: +Y% estimated uplift for those articles
```

### Comparison Report Contents

- Artikel BARU masuk display
- Artikel KELUAR dari display
- Artikel PINDAH posisi
- Expected sales impact estimate
