# Planogram Worked Examples

> This file contains end-to-end worked examples showing the planogram generation flow.
> Referenced from SKILL.md and planogram-algorithm.md Section 2.8.

---

## Worked Example: Toko Fiktif "Zuma Mini"

> Contoh ini menunjukkan flow end-to-end untuk 1 toko kecil agar logic jelas.

### Setup

```
Denah:
  - BW-1: Backwall, 12 hooks
  - GD-1: Gondola, 8 hooks  
  - KR-1: Keranjang Baby x 1
  - Storage: 5 box

Sales data (adjusted avg, sudah dihitung):
  Men Jepit:     M1CA25 (T1, 40), M1CA30 (T1, 35), M1ST08 (T2, 12), M1BS05 (T3, 5)
  Men Fashion:   M2DA03 (T1, 25), M2CL02 (T8, 15), M2DA05 (T3, 8)
  Ladies Jepit:  L1CA22 (T1, 38), L1CA26 (T1, 30), L1CA29 (T2, 10)
  Ladies Fashion:L2EA10 (T1, 28), L2FO03 (T8, 18), L2EA12 (T2, 9)
  Baby:          K1CA05 (T1, 20), K1VB01 (T8, 12), K1CM01 (T2, 6)
```

### Step A: Gender-Type Sales Share

```
Men Jepit:      40+35+12+5 = 92 (29%)
Ladies Jepit:   38+30+10 = 78 (25%)
Ladies Fashion: 28+18+9 = 55 (17%)
Men Fashion:    25+15+8 = 48 (15%)
Baby:           20+12+6 = 38 (12%)

Note: Tidak ada Luca/Luna/Airmove dan tidak ada Table/VM -> skip step 2.5.0
```

### Step B: Assign Gender-Type ke Display

```
BW-1 (12 hooks, terbesar) -> Men Jepit (29%, rank 1)
GD-1 (8 hooks)            -> Ladies Jepit (25%, rank 2)

Tapi Ladies Fashion (17%) dan Men Fashion (15%) tidak punya display unit!
-> Opsi 1: Split BW-1 menjadi 2 section? [X] Tidak boleh, rule: 1 unit = 1 gender-type
-> Opsi 2: Hanya display 2 gender-type terbesar
-> Opsi 3: Kalau ada SPG insight bilang fashion demand tinggi -> pertimbangkan assign GD-1 ke fashion

Untuk contoh ini: ikuti data -> BW-1 = Men Jepit, GD-1 = Ladies Jepit
FLAG: "Ladies Fashion & Men Fashion tidak punya display unit -- 
       pertimbangkan tambah gondola atau realokasi"
       
KR-1 (keranjang x 1) -> Baby & Kids (otomatis)
```

### Step C: Hitung Slots & Assign Articles

```
BW-1 Men Jepit (12 hooks):
  T1 count: 2 (M1CA25, M1CA30)
  Full box mode: 12/2 = 6 slots -> 2 T1 + sisa 4 slot
  -> M1CA25 (hook 1-2), M1CA30 (hook 3-4)
  -> Fill: M1ST08/T2 (hook 5-6), M1BS05/T3 (hook 7-8)
  -> Remaining 4 hooks (9-12): KOSONG atau bisa diisi jika ada artikel Men Jepit lain
  -> FLAG: "4 hooks available"

GD-1 Ladies Jepit (8 hooks):
  T1 count: 2 (L1CA22, L1CA26)
  Full box mode: 8/2 = 4 slots -> 2 T1 + sisa 2 slot
  -> L1CA22 (hook 1-2), L1CA26 (hook 3-4)
  -> Fill: L1CA29/T2 (hook 5-6)
  -> 1 slot remaining (hook 7-8): KOSONG
  -> FLAG: "2 hooks available"

KR-1 Baby (1 keranjang):
  -> K1CA05 (T1, highest avg) = 12 pairs di keranjang
  -> K1VB01 (T8) dan K1CM01 (T2) tidak muat -> FLAG: "Baby T8 tidak di-display"
```

### Step D: Storage Allocation

```
Storage capacity: 5 box
Compact overflow: 0 (semua full box mode)
Luca/Luna/AM: 0

Storage available: 5 box penuh

Eligible: semua yang di-display (T1 + T8 + T2)
Total adj_avg eligible yang di-display: 40+35+12+5+38+30+10+20 = 190

Allocation:
  M1CA25: MAX(1, ROUND(5 x 40/190)) = MAX(1, 1.05) = 1 box
  M1CA30: MAX(1, ROUND(5 x 35/190)) = MAX(1, 0.92) = 1 box
  L1CA22: MAX(1, ROUND(5 x 38/190)) = MAX(1, 1.00) = 1 box
  L1CA26: MAX(1, ROUND(5 x 30/190)) = MAX(1, 0.79) = 1 box
  K1CA05: sudah 1 box di keranjang (12 pairs) -> bisa tambah 1 box backup
  
  Total: 5 box [OK] pas

  Sisanya (M1ST08/T2, M1BS05/T3, L1CA29/T2) tidak dapat storage tambahan
  karena kapasitas habis -> acceptable, mereka bukan T1
```

### Step E: Final Output Summary

```
Display: 8 artikel terdisplay dari 14 total
Sales coverage: (40+35+12+5+38+30+10+20) / 316 = 60%
Storage: 5/5 box (100%)

Flags:
  CRITICAL: Ladies Fashion & Men Fashion tidak punya display -> revenue loss ~32%
  WARNING: Baby T8 (K1VB01) tidak di-display -> new launch tanpa exposure
  POSITIVE: Semua T1 terdisplay [OK] (untuk gender-type yang punya display)
  
Recommendation:
  -> Tambah minimal 1 gondola untuk Ladies Fashion (17% sales share tanpa display)
  -> Atau realokasi: jika bisa split BW-1 atau tambah 1 unit lagi
```
