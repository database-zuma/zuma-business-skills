# Planogram Display Rules — Detailed Reference

> This file contains detailed display component rules, slot calculations, mixed-hook handling,
> series reference, zone optimization, and edge case handling.
> Referenced from SKILL.md Section 1.3-1.11.

---

## 1. Backwall & Gondola — Detailed Rules

### 1.1 Mixed-Hook Backwall (beberapa store)

Beberapa toko punya 1 backwall fisik yang dibagi menjadi 2+ section dengan gender-type/HPA berbeda. Contoh: Tunjungan Plaza BW-4 kanan = Elsa (fashion, 3 hpa) + Classic (jepit, 2 hpa) di satu unit fisik.

```
Handling:
1. SPLIT menjadi sub-unit logis: BW-4a-Elsa, BW-4a-Classic
2. Setiap sub-unit diperlakukan sebagai backwall terpisah
3. Setiap sub-unit punya hooks, HPA, dan series filter sendiri
4. Dalam XLSX output, buat sheet terpisah per sub-unit
5. Dalam visual output, render sebagai satu blok fisik tapi dengan divider
```

---

## 2. Hook Capacity — Detailed Calculations & Examples

### 2.1 Slot Calculations

```
Backwall dengan 30 hooks:

  JEPIT:
    - Full box mode (2 hook): 30 / 2 = 15 artikel, 0 ke storage
    - Compact mode (1 hook):  30 / 1 = 30 artikel, 6 pairs/artikel ke storage
    - Mix mode: bisa sebagian full, sebagian compact

  FASHION:
    - Full box mode (3 hook): 30 / 3 = 10 artikel, 0 ke storage
    - Compact mode (2 hook):  30 / 2 = 15 artikel, 4 pairs/artikel ke storage
    - Mix mode: bisa sebagian full, sebagian compact
```

### 2.2 Decision Logic untuk Pilih Mode

```
1. Hitung jumlah artikel eligible (T1 + T8 + T2 yang harus masuk display)
2. Hitung slot tersedia di full box mode
3. Jika eligible > slot full box -> SWITCH ke compact mode
4. Jika compact mode masih tidak cukup -> prioritaskan T1 by sales rank
5. Bisa juga MIX: T1 top di full box (supaya display tebal), sisanya compact
6. SELALU hitung storage impact dari compact mode dan validasi terhadap capacity
```

### 2.3 Mix Mode Strategy

```
Contoh: 30 hook fashion, 13 artikel harus masuk
  - Full box semua: 30/3 = 10 slot -> 3 artikel tidak muat
  - Compact semua: 30/2 = 15 slot -> semua muat, tapi 13 x 4 = 52 pairs ke storage
  - Mix optimal:
    * Top 4 T1 -> full box (4 x 3 = 12 hook, tebal di display)
    * Sisa 9 artikel -> compact (9 x 2 = 18 hook)
    * Total: 12 + 18 = 30 hook [OK]
    * Storage impact: hanya 9 x 4 = 36 pairs
```

---

## 3. Rak Baby — Detailed Rules

- Khusus untuk artikel Baby & Kids
- Kapasitas dasar: **6 pairs per layer**, 1 rak bisa punya **2-3 layer**
- Jumlah rak per toko: bervariasi (bisa 0)

**Display mode rak (sama prinsipnya dengan hook):**

| Mode | Pairs per Layer | Artikel per Layer | Sisa ke Storage |
|------|----------------|-------------------|-----------------|
| **Full** | 6 pairs = 1 artikel (1/2 box) | 1 | 6 pairs |
| **Compact** | 3 pairs = 1 artikel | 2 artikel per layer | 9 pairs |

```
Contoh rak 3 layer:
  - Full mode: 3 layer x 1 artikel = 3 artikel, tapi setiap artikel cuma 1/2 box di display
  - Compact mode: 3 layer x 2 artikel = 6 artikel, tapi per artikel cuma 3 pairs di display
  - Mix mode: layer 1-2 full (bestseller), layer 3 compact (variety)
```

**Decision logic sama dengan hook:** jika artikel baby eligible lebih banyak dari slot -> compact mode.

---

## 4. Keranjang Baby

- Khusus untuk artikel Baby & Kids
- Kapasitas: **12 pairs per keranjang** (= 1 artikel)
- Jumlah per toko: **1-4 keranjang** (bisa 0)

---

## 5. Table Display

- **WAJIB** untuk artikel Luca, Luna, Airmove
- Kapasitas: **VARIABLE per toko** -- harus ditanyakan
- Display mode: **1 pair per artikel** (sample display)
- Sisa dari 1 box (11 pairs) masuk ke **storage**

---

## 6. VM Display (Wall/Shelf) + VM Tools

- Alternatif display untuk Luca/Luna/Airmove selain table
- Kapasitas: **1-2 artikel per VM unit** -- VARIABLE, harus ditanyakan
- Availability VM tools beda per toko -- harus ditanyakan
- Display mode: 1-2 pairs per artikel, sisanya ke storage

---

## 7. Shelving Display

- Rak/shelf standalone atau terintegrasi dalam backwall (bukan hook)
- Bisa standalone (unit terpisah di lantai) atau bagian dari backwall (1-2 kolom di BW dikonversi jadi shelf)
- Kapasitas: **VARIABLE per toko** -- biasanya 1-5 artikel per unit
- Display mode: **sample display** (1-2 pairs per artikel ditunjukkan, sisa ke storage)
- Storage impact: **~10 pairs per artikel** (1 box = 12 pairs, display 2, storage 10)
- Biasa dipakai untuk: Airmove, Puffy, atau series lain yang butuh display shelf bukan hook

**Contoh:**
```
Tunjungan Plaza:
  - Airmove Shelving (terintegrasi di BW-1): 3 artikel Airmove
  - Puffy Shelving (terintegrasi di BW-2): 1 artikel Puffy
  - Storage impact: (3+1) x ~10 pairs = ~40 pairs = ~4 box
```

**Rule:** Artikel di shelving TIDAK mengurangi hook count backwall induknya. Shelving dihitung sebagai unit terpisah.

---

## 8. Table Baby

- Meja datar (BUKAN rak bertingkat) khusus untuk display artikel Baby & Kids
- Berbeda dari Rak Baby: Table = flat surface, Rak = multi-layer shelving
- Kapasitas: **VARIABLE per toko** -- biasanya 4-8 artikel
- Display mode: **sample display** (~6 pairs per artikel di meja, sisa ke storage)
- Storage impact: **~6 pairs per artikel** (setengah box)

```
Perbedaan Table Baby vs Rak Baby:
  - TABLE BABY: Meja datar, 1 layer, 4-8 artikel, 6 pairs/artikel di display
  - RAK BABY: Rak bertingkat, 2-3 layer, 1-2 artikel/layer, 6 pairs/layer
  - Toko bisa punya salah satu atau keduanya -- TANYAKAN
```

---

## 9. Luca/Luna/Airmove Special Rules

**CRITICAL RULES:**
```
1. TIDAK BOLEH ditaruh di hook biasa tanpa VM tools
2. HANYA BOLEH di: Table Display ATAU Wall dengan VM Tools
3. 1 box = 12 pairs, tapi yang terpajang hanya 1-2 pairs
4. Sisanya (10-11 pairs) WAJIB masuk storage
5. Implikasi: artikel ini "mahal" dari sisi storage
6. Jika storage terbatas -> batasi jumlah artikel Luca/Luna/Airmove
```

**Storage impact calculation:**
```
Contoh: Toko A punya storage 10 box, assign 3 artikel Luca/Luna/Airmove
  -> 3 box terpakai untuk Luca/Luna/Airmove storage
  -> Sisa 7 box untuk fast moving articles lainnya
```

---

## 10. Ketersediaan Display per Toko

PENTING: Tidak semua toko punya semua tipe display. Contoh:
- Toko A: hanya backwall + gondola (no table, no rak)
- Toko B: backwall + gondola + table + keranjang
- Toko C: gondola + rak + keranjang (no backwall)

**SELALU validasi display apa saja yang tersedia SEBELUM membuat rekomendasi.**

---

## 11. Series Reference List (dari DB, updated Feb 2026)

**CRITICAL: Sebelum membuat planogram, SELALU query distinct series dari DB untuk store target.** List di bawah ini sebagai REFERENSI, bukan sumber kebenaran -- series baru bisa muncul kapan saja.

### Series per Gender-Type

**MEN FASHION:**
AIRMOVE (3), CAMO (4), CLOUD (6), DALLAS (12), GUDETAMA (1), HANZO (3), LEON (3), LOONEY (1), LUCA (8), ONYX (13), POWERMAX (2), ROCKY (5), SLIDE (18), SUMMER (12), XANDER (7), ZORRO (6)

**MEN JEPIT:**
BLACKSERIES (21), CAMO (3), CLASSIC (31), CLASSICEARTH (4), LAYERSOLE (3), PILLOW (20), SOLID (1), STRIPE (17), SUMMER (4), TWOTONE (1)

**LADIES FASHION:**
AYANG (4), CAMO (5), ELSA (14), ELSA SURFERGRIL (4), FLO (10), FREYA (6), GUDETAMA (3), IRIS (4), JOVIEV (3), KIM (5), LOONEY (2), LUNA (7), MERCI (5), PUFFY (10), STITCH (2), STRAPP (6), SUMMER (12), SURFERGRIL (3), TROPICAL (2), WEDGES (12)

**LADIES JEPIT:**
CLASSIC (36), CLASSIC METALIC (9), CLASSICEARTH (5), DOUGH DARLINGS (1), HELLO KITTY (1), LAYERSOLE (1), PILLOW (19), SOLID (3), STRIPE (12), SUMMER (4), TWOTONE (2)

**BABY FASHION:**
COCOMELON (3), DISNEY (4), LOTSO (1), MICKEY (1), MILTON (3), MINNIE (3), OXFORD (3), POOH (3), PRINCESS (4), STITCH (2), TOY STORY (3), VELCRO (6), WBB (3)

**BABY JEPIT:**
BATMAN (2), CLASSIC (12), HELLOKITTY (4), MICKEY (1), MICKEY & FRIENDS (3), WBB (2)

**BOYS FASHION:**
DOVER (1), ONYX (3), SLIDE (3), SPIDER-MAN (3), STITCH (1), VELCRO (3)

**BOYS JEPIT:**
BATMAN (2), CLASSIC (6), DISNEY (3), GUDETAMA (2), MICKEY (5), SPACEJAM (4), STRIPE (6), TOY STORY (2)

**GIRLS FASHION:**
DOVER (1), STITCH (1), VELCRO (3)

**GIRLS JEPIT:**
CLASSIC (7), DISNEY (3), GUDETAMA (2), MINNIE (5), STRIPE (6)

**JUNIOR JEPIT:**
CLASSIC (4)

**KIDS JEPIT:**
LEEVIERRA (3)

### Series Naming Gotchas (FILTER TRAPS)

**CRITICAL WARNING:** Beberapa series punya nama yang overlap. Jika filter pakai exact match "CLASSIC", akan MISS series "CLASSIC METALIC" dan "CLASSICEARTH".

| Parent Series | Sub-variants yang JUGA ADA di DB | Impact jika terlewat |
|---|---|---|
| `CLASSIC` | `CLASSIC METALIC`, `CLASSICEARTH` | Miss T1 articles, CRITICAL |
| `ELSA` | `ELSA SURFERGRIL` | Miss fashion articles |
| `MICKEY` | `MICKEY & FRIENDS` | Miss baby articles |

**SOLUSI:**
```
JANGAN: series_filter = ["CLASSIC"]
LAKUKAN: series_filter = ["CLASSIC", "CLASSIC METALIC", "CLASSICEARTH"]

Atau lebih aman -- query dulu:
SELECT DISTINCT series FROM core.sales_with_product
WHERE matched_store_name = '{store}'
  AND gender = '{gender}' AND tipe = '{tipe}'
  AND series IS NOT NULL
-> Gunakan SEMUA series dari hasil query sebagai filter
```

---

## 12. Zone Optimization (Detail)

Jika data SPG insight tersedia (customer flow, hot/cold zone), gunakan untuk optimasi penempatan:

### Hot Zone (Area ramai, sering dilalui)
ASSIGN ke sini:
- T1 dengan sales TERTINGGI
- T8 new launch yang butuh discovery/exposure
- Artikel impulse buy (warna cerah, fashion trendy)

### Cold Zone (Area jarang dilalui)
ASSIGN ke sini:
- T1/T2 yang sudah punya loyal buyers (customer akan sengaja cari)
- BUKAN artikel baru yang butuh discovery

### Eye Level (Setinggi mata)
- T1 bestsellers
- T8 new launch

### Lower/Upper Level
- T2, T3
- Artikel basic yang customer sudah familiar

### Cross-validation dengan Sales Data
```
Jika artikel di hot zone punya sales rendah -> kemungkinan salah artikel
Jika artikel di cold zone punya sales tinggi -> kemungkinan artikel kuat, tapi bisa lebih baik lagi di hot zone
-> Rekomendasi: SWAP posisi
```

---

## 13. Storage Allocation Rules (Detail)

### Priority Order:
```
1. PERTAMA: Alokasi untuk Table Display articles (Luca/Luna/Airmove)
   -> Setiap artikel = 1 box di storage (11 pairs backup)

2. KEDUA: Alokasi untuk Compact Mode overflow
   -> Artikel yang di-display dalam compact mode punya sisa pairs yang masuk storage
   -> Jepit compact: 6 pairs per artikel ke storage
   -> Fashion compact: 4 pairs per artikel ke storage
   -> Rak baby compact: 9 pairs per artikel ke storage
   -> INI BUKAN box terpisah -- ini sisa dari box yang sudah di-display
   -> Tapi tetap makan space storage

3. KETIGA: Alokasi tambahan untuk T1 fast moving
   -> Proporsional terhadap sales share
   -> Minimum 1 box per artikel yang dapat storage
   
4. KEEMPAT: Alokasi untuk T8 yang potensial
   -> 1 box per artikel

5. KELIMA: Sisa untuk T2
   -> Jika masih ada capacity
```

### Storage Capacity Calculation:
```
Total storage terpakai = 
  + (jumlah artikel Luca/Luna/Airmove x 1 box)
  + (jumlah artikel compact mode x sisa pairs per artikel)  <- konversi ke box equivalent
  + (alokasi tambahan T1/T8/T2)

PENTING: Compact mode pairs BUKAN full box, tapi tetap makan ruang.
Konversi ke box equivalent: CEIL(total compact pairs / 12)

Contoh:
  - 3 artikel Luca = 3 box
  - 9 artikel fashion compact = 9 x 4 pairs = 36 pairs = 3 box equivalent
  - Total terpakai sebelum alokasi tambahan = 6 box
  - Sisa storage = total capacity - 6
```

### Compact Mode & Storage Tradeoff Decision:
```
SEBELUM memutuskan compact mode, HITUNG DULU:
  1. Berapa artikel yang harus masuk display? (T1 + T8 wajib)
  2. Berapa slot di full box mode?
  3. Jika cukup -> pakai full box, JANGAN compact (hemat storage)
  4. Jika tidak cukup -> hitung storage impact dari compact
  5. Jika storage cukup untuk absorb compact overflow -> GO compact
  6. Jika storage TIDAK cukup -> prioritaskan T1 by rank, sebagian tidak masuk display
     -> Flag sebagai warning di report
```

### Storage Rules:
- T4/T5: **JANGAN** alokasi storage
- T8 di storage TANPA di display: **BOLEH** (untuk rotation purpose)
- Non-T8 di storage TANPA di display: **TIDAK BOLEH**
- Alokasi proporsional:
  ```
  Box untuk artikel X = ROUND(sisa_storage x (sales_X / total_sales_eligible))
  Minimum = 1 box jika eligible
  ```

---

## 14. Gender-Type Assignment ke Display Unit (Detail)

Ketika merekomendasikan gender-type mana masuk ke backwall/gondola mana, pertimbangkan:

```
1. PROPORSI SALES per gender-type
   -> Gender-type dengan sales terbesar dapat display unit terbesar
   
2. CUSTOMER FLOW (dari SPG insight)
   -> Gender-type utama di hot zone / area pertama terlihat
   
3. ADJACENCY
   -> Men Jepit dan Men Fashion idealnya berdekatan
   -> Ladies Jepit dan Ladies Fashion idealnya berdekatan
   -> Baby/Kids bisa di area terpisah (dekat rak & keranjang)
   
4. PINTU MASUK
   -> Gender-type dengan sales tertinggi idealnya paling dekat dengan pintu masuk
   -> Atau T8 new launch untuk maximum exposure
```

---

## 15. Edge Cases & Fallbacks (Detail)

### Slot lebih banyak dari artikel eligible
- Isi dengan T3 untuk variety
- Jika T3 juga habis, BIARKAN kosong (lebih baik kosong daripada isi T4/T5)
- Flag sebagai "available slot" di report

### Artikel T1 lebih banyak dari slot (full box mode)
1. **PERTAMA:** Switch ke compact mode (lihat Section 2) -- ini biasanya cukup menyelesaikan masalah
2. Cek apakah storage cukup untuk absorb compact overflow
3. Jika compact mode + storage cukup -> GO
4. Jika compact mode masih tidak cukup -> prioritas berdasarkan adjusted avg (tertinggi masuk duluan)
5. T1 yang tetap tidak muat -> flag sebagai critical warning
6. Saran: tambah display unit atau redistribute ke toko lain

### Storage penuh tapi butuh lebih
- Prioritas: Luca/Luna/Airmove storage FIRST (karena wajib)
- Lalu T1 berdasarkan sales rank
- Flag overflow di report

### Toko tanpa table display tapi ada artikel Luca/Luna/Airmove yang T1
- Cek apakah ada VM tools
- Jika tidak ada table DAN tidak ada VM tools -> artikel ini TIDAK BISA dipajang di toko ini
- Flag sebagai warning: "T1 Luca/Luna/Airmove tidak bisa display -- butuh table/VM"
- **PENTING:** Luca/Luna/Airmove yang tidak bisa display juga TIDAK BOLEH dimasukkan ke backwall/gondola sebagai fallback. Mereka HARUS di-exclude dari candidate list backwall. (Lihat planogram-algorithm.md Section 2.5.1 exclusion list)

### Toko tanpa storage (storage capacity = 0)
- **Compact mode TIDAK BISA digunakan** -- compact mode menghasilkan overflow pairs yang butuh storage
- **HARUS Full Box Mode only** untuk semua display
- Luca/Luna/Airmove **TIDAK BISA display** bahkan jika ada Table/VM -- karena setiap artikel Luca/Luna/Airmove butuh 1 box di storage untuk backup (11 pairs)
- Replenishment harus langsung dari gudang pusat (WHS/WHJ/WHB)
- Flag: "No storage -- Full Box Mode only, no Luca/Luna/Airmove, no compact mode"

### Jumlah display unit lebih sedikit dari jumlah gender-type
- Ini NORMAL untuk toko kecil (contoh: 4 backwall tapi 8 gender-type)
- Gender-type dengan sales share terkecil TIDAK mendapat display unit
- T1 dari gender-type tanpa display -> TIDAK BISA di-display
- Flag sebagai warning, BUKAN error: "Gender-type X (Y% share) tidak punya display unit"
- Saran: "Pertimbangkan tambah gondola atau realokasi untuk coverage lebih baik"

---

## 16. Baby & Kids Special Handling

Artikel Baby & Kids punya display components khusus (rak & keranjang) selain backwall/gondola.

```
Assignment logic:
1. Rank baby articles by adjusted avg sales
2. Assign ke rak dan keranjang sesuai capacity
   - Rak: gunakan full atau compact mode (lihat Section 3) tergantung jumlah artikel eligible vs slot
   - Keranjang: 12 pairs per keranjang = 1 artikel
3. Sisa baby articles yang tidak muat di rak/keranjang -> bisa masuk gondola/backwall Baby
4. Baby articles di backwall/gondola ikut hook rules standar (full/compact mode, lihat Section 2)
```
