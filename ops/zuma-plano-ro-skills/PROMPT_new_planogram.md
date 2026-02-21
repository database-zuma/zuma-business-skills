---
name: PROMPT_new_planogram
description: Template prompt untuk generate planogram toko baru (Step 0 input check + Step 1 article assignment + Step 2 visual floor plan). Use when user asks to create a new planogram, generate planogram for a store, or run the full planogram workflow.
user-invocable: true
---

# Prompt: New Store Planogram (Step 1 + Step 2)

> Copy-paste prompt di bawah ini, ganti bagian `[...]` sesuai kebutuhan.

---

```
Buatkan planogram untuk toko: [NAMA_TOKO_1], [NAMA_TOKO_2], ...
Region: [REGION — contoh: Jatim, Jakarta, Sumatra, Sulawesi, Batam, Bali]

---

## SKILLS TO LOAD

Load these skills in order:
1. `zuma-data-analyst-skill` — for DB connection & sales data query
2. `zuma-sku-context` — for tier system & article categorization
3. `zuma-warehouse-and-stocks` — for storage context
4. `zuma-branch` — for store/branch info
5. `planogram-zuma` — Step 1: planogram article assignment
6. `visualized-planogram-zuma` — Step 2: planogram visual floor plan

---

## STEP 0: INPUT DATA CHECK (DO THIS FIRST)

Sebelum mulai, VALIDASI semua input data di bawah ini sudah tersedia.
Jika ada yang BELUM tersedia → TANYAKAN ke user untuk provide, JANGAN assume atau skip.

### Checklist Input Data:

| # | Data | Status | Cara Dapat |
|---|------|--------|------------|
| 1 | **Sales data 12 bulan terakhir** per artikel (Kode Mix level) per toko | [ ] | Query dari DB `core.sales_with_product` |
| 2 | **Master Artikel + Tier** (Kode Mix, gender, series, article, tier_baru) | [ ] | Query dari DB `core.stock_with_product` atau master table |
| 3 | **Denah Toko / Layout fisik** — jumlah & posisi display components | [ ] | User harus provide (foto/file/deskripsi) |
| 4 | **SPG Insight** — customer flow, hot/cold zone, demand insight | [ ] | Opsional — tanya user apakah ada |
| 5 | **Storage capacity** — berapa box bisa disimpan di backroom | [ ] | User harus provide |
| 6 | **Table/VM Display info** — kapasitas per unit | [ ] | User harus provide |

### Pertanyaan Wajib ke User (jika belum dijawab):

1. Toko mana yang mau dibuatkan planogram? → [SUDAH DIJAWAB DI ATAS]
2. Berapa total display components per toko?
   - Backwall: berapa unit? berapa hooks per unit? gender-type per unit?
   - Gondola: berapa unit? berapa hooks per unit?
   - Rak Baby: berapa unit? berapa layer per rak?
   - Keranjang Baby: berapa unit?
   - Table Display: berapa unit? muat berapa artikel per table?
   - VM Display: berapa unit? ada VM tools?
3. Berapa kapasitas storage (total box di backroom)?
4. Apakah ada artikel Luca/Luna/Airmove di toko ini?
5. Apakah ada SPG insight (customer flow, hot/cold zone)?
6. Apakah ada denah existing (foto/file) yang bisa dijadikan referensi?

**JANGAN LANJUT KE STEP 1 SAMPAI SEMUA DATA WAJIB TERKONFIRMASI.**

---

## STEP 1: PLANOGRAM ARTICLE ASSIGNMENT

Setelah semua input data lengkap, jalankan Step 1 menggunakan `planogram-zuma` skill:

1. Query sales data 12 bulan dari DB (gunakan `zuma-data-analyst-skill`)
2. Hitung adjusted average per artikel per tier
3. Tentukan mode per backwall (Full Box / Compact / Mix) berdasarkan demand vs slot
4. Assign artikel ke setiap display component berdasarkan priority rules
5. Generate output: `PLANOGRAM_[NAMA_TOKO].xlsx`

### Output Step 1:
- XLSX file dengan sheet per backwall + Rak Baby + Storage + Summary + Ranking + Monthly
- Setiap sheet menunjukkan artikel mana di hook/slot mana

### Checkpoint setelah Step 1:
**TANYAKAN ke user:**
> "Step 1 planogram sudah selesai. Output: `PLANOGRAM_[NAMA_TOKO].xlsx`
> Mau review/adjust dulu sebelum lanjut ke Step 2 (visualisasi denah)?
> Atau langsung lanjut?"

**Tunggu jawaban user sebelum lanjut ke Step 2.**

---

## STEP 2: PLANOGRAM VISUAL FLOOR PLAN

Setelah user confirm Step 1 OK, jalankan Step 2 menggunakan `visualized-planogram-zuma` skill:

1. Parse `PLANOGRAM_[NAMA_TOKO].xlsx` dari Step 1
2. Define store layout coordinates (posisi fisik setiap display unit)
   - **PENTING**: Layout config SPESIFIK per toko — buat config baru berdasarkan denah yang user provide
   - Referensi: `ROYAL_PLAZA_LAYOUT` di `visualize_planogram.py` sebagai contoh format
3. Generate BOTH outputs:
   - `VISUAL_PLANOGRAM_[NAMA_TOKO].xlsx` — Excel bird's-eye floor plan (color-coded)
   - `VISUAL_PLANOGRAM_[NAMA_TOKO].txt` — ASCII floor plan

### Visual harus menampilkan per artikel:
- Series name (color-coded)
- Full article name (e.g., "MEN DALLAS 1", "LADIES FLO 1")
- Tier & Average (e.g., "T1 | Avg: 11.8")
- Backwall dimensions (e.g., "8X7", "7X7")

---

## MULTIPLE STORES (jika lebih dari 1 toko)

Jika planogram untuk multiple toko:
- Ulangi Step 0 → Step 1 → checkpoint → Step 2 untuk SETIAP toko
- Setiap toko punya layout config yang BERBEDA
- Sales data di-query per toko (filter by store name)
- JANGAN copy-paste layout dari toko lain — setiap denah unik

---

## OUTPUT FILES (per toko)

| File | Deskripsi |
|------|-----------|
| `PLANOGRAM_[NAMA_TOKO].xlsx` | Step 1 — article assignment per display unit |
| `VISUAL_PLANOGRAM_[NAMA_TOKO].xlsx` | Step 2 — Excel bird's-eye floor plan |
| `VISUAL_PLANOGRAM_[NAMA_TOKO].txt` | Step 2 — ASCII floor plan |

---

## DB CONNECTION (for reference)

Host: 76.13.194.120 | Port: 5432 | DB: openclaw_ops
Key tables: core.sales_with_product, core.stock_with_product
Rules: ALWAYS exclude intercompany transactions

---

## CONTOH TOKO YANG SUDAH SELESAI (referensi)

Royal Plaza (Jatim):
- 4 backwalls: BW-1 Men Jepit (48 hooks), BW-2 Ladies Fashion (56 hooks), BW-3 Men Fashion (56 hooks), BW-4 Baby & Kids (56 hooks)
- 1 Rak Baby (2 layers)
- Storage: 0 box (small store)
- Total: 87/88 slots filled (98.9%)
- Files: PLANOGRAM_Royal_Plaza.xlsx, VISUAL_PLANOGRAM_Royal_Plaza.xlsx, VISUAL_PLANOGRAM_Royal_Plaza.txt
```

---

### Cara Pakai

1. Copy prompt di atas
2. Ganti `[NAMA_TOKO_1]`, `[NAMA_TOKO_2]` dengan nama toko target
3. Ganti `[REGION]` dengan region toko
4. Paste ke chat session baru
5. Agent akan mulai dari Step 0 (validasi input) — siapkan denah toko, info storage, dan display components
