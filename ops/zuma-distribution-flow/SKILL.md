[Uploading SKILL.md…]()
# Flow Distribusi: Surplus & Restock

## Overview

Sistem distribusi ZUMA terdiri dari 2 flow utama:
1. **Restock Flow** — mengisi kekurangan stok di toko
2. **Surplus Flow** — menarik kelebihan stok dari toko berdasarkan kapasitas tier

Kedua flow ini di-trigger otomatis oleh sistem, dengan kontrol eksekusi oleh **Allocation Planner**.

---

## Definisi & Komponen

### Gudang
| Gudang | Isi | Unit Kirim |
|--------|-----|------------|
| **Gudang Box** | Stok dalam kemasan box penuh (12 pairs, all sizes) | Per box |
| **Gudang Protol** | Stok eceran per size/pairs | Per pairs/size |

### Tipe RO (Replenishment Order)
| Tipe | Trigger | Source | Kirim |
|------|---------|--------|-------|
| **RO Box** | Size kosong ≥50% dari assortment artikel | Gudang Box | 1 box (12 pairs, all sizes) |
| **RO Protol** | Size kosong <50% dari assortment artikel | Gudang Protol | Pairs di size yang kosong saja |

### Key Metrics
- **Assortment** = jumlah size yang seharusnya tersedia untuk 1 artikel di toko tersebut
- **% Size Kosong** = (jumlah size yang stoknya 0) / (total assortment) × 100%
- **Tier Capacity %** = persentase ideal stok per tier dari total kapasitas toko
- **Actual Tier %** = persentase stok aktual per tier dari total stok toko
- **TO (Turnover)** = kecepatan jual artikel — semakin rendah, semakin lambat terjual

### Tier Surplus Rules
| Tier | Surplus Check | Alasan |
|------|--------------|--------|
| **T1** | ✅ Ya | Best seller — perlu dijaga proporsinya |
| **T2** | ✅ Ya | Secondary fast moving — perlu dijaga proporsinya |
| **T3** | ✅ Ya | Moderate — perlu dijaga proporsinya |
| **T4** | ❌ Tidak | Promo / clearance — tujuannya menghabiskan stok |
| **T5** | ❌ Tidak | Slow moving — sama seperti T4 |
| **T8** | ❌ Tidak (3 bulan) | New launch — protection period untuk test market |

---

## FLOW 1: RESTOCK

### Trigger
Sistem mendeteksi gap antara stok aktual vs kebutuhan (planogram display + storage allocation).

### Decision Tree

```
SISTEM DETEKSI GAP
        │
        ▼
Hitung % size kosong vs assortment
        │
        ├── ≥50% size kosong ──────► RO BOX
        │                              │
        │                              ▼
        │                        Cek Gudang Box
        │                              │
        │                         ├── Ada ──► Planner approve ──► Kirim box ke toko
        │                         │
        │                         └── Tidak ada ──► Flag (tunggu PO supplier)
        │
        └── <50% size kosong ──────► RO PROTOL (Tiered)
                                       │
                                  STEP 1: Cek Gudang Protol
                                       │
                                  ├── Ada ──► Kirim protol ✅
                                  │
                                  └── Tidak ada
                                       │
                                  STEP 2: Cek surplus toko lain
                                       │
                                  ├── Ada ──► Tarik ke gudang → kirim protol ✅
                                  │
                                  └── Tidak ada
                                       │
                                  STEP 3: Fallback RO Box
                                       ⚠ Wajib pre-plan surplus size yg sudah ada
```

### Restock Rules

1. Prioritas selalu RO Protol jika memenuhi syarat — lebih efisien, tidak bikin surplus baru
2. RO Box adalah last resort untuk kasus protol, kecuali memang ≥50% size kosong
3. Setiap RO Box fallback wajib disertai surplus pre-plan
4. Allocation planner = gatekeeper — sistem recommend, planner approve/reject/modify

---

## FLOW 2: SURPLUS (Tier-Based)

### Konsep Utama

Surplus BUKAN asal tarik barang dari toko. Surplus ditentukan berdasarkan **gap antara kapasitas ideal per tier vs stok aktual per tier**. Hanya tier yang over-capacity yang ditarik, dan yang ditarik adalah artikel dengan turnover (TO) terendah di tier tersebut.

### Tier yang Dicek vs Dikecualikan

**Dicek (T1, T2, T3):**
- Tier ini punya target kapasitas ideal (%) dari total kapasitas toko
- Jika actual % > ideal % → tier over-capacity → tarik selisihnya
- Yang ditarik: artikel dengan TO paling rendah / dead stock di tier tersebut

**Dikecualikan:**
- **T4**: Promo / clearance — tujuan menghabiskan stok, jangan ditarik
- **T5**: Slow moving — sama seperti T4, biarkan sampai habis atau di-clearance
- **T8**: New launch — protection period 3 bulan sejak launch untuk test market

### T8 Lifecycle

```
LAUNCH (Bulan ke-0)
    │
    ▼
Protection Period (3 bulan)
- Tidak boleh ditarik sebagai surplus
- Data sales dikumpulkan untuk evaluasi
- Exception: manual override oleh Allocation Planner
  jika toko benar-benar over-capacity parah
    │
    ▼
BULAN KE-4: Reclassification
    │
    ├── Sales bagus ──► Masuk T1/T2/T3 ──► Ikut rules surplus tier barunya
    │
    └── Sales jelek ──► Masuk T4/T5 ──► Exclude dari surplus check
                                          (masuk program clearance)
```

### Surplus Decision Tree

```
SISTEM HITUNG KAPASITAS PER TIER PER TOKO
        │
        ▼
Bandingkan per tier: Actual % vs Ideal Capacity %
        │
        ├── T1: Ideal 30%, Actual 35% ──► Over +5% ──► SURPLUS CANDIDATE
        ├── T2: Ideal 25%, Actual 22% ──► Under     ──► SKIP (butuh restock)
        ├── T3: Ideal 20%, Actual 23% ──► Over +3% ──► SURPLUS CANDIDATE
        ├── T4: ─────────────────────────────────────► SKIP (promo/clearance)
        ├── T5: ─────────────────────────────────────► SKIP (slow moving)
        └── T8: ─────────────────────────────────────► SKIP (protection 3 bln)
        │
        ▼
Untuk tier yang OVER-CAPACITY:
        │
        ▼
Hitung selisih = Actual % - Ideal %
Convert ke jumlah artikel/box
        │
        ▼
Ranking artikel di tier tsb by TO ascending
(TO terendah = dead stock = prioritas tarik pertama)
        │
        ▼
Tarik artikel dgn TO terendah sampai selisih terpenuhi
        │
        ▼
Allocation Planner review & approve list tarik
        │
        ▼
Tarik dari toko ──► Masuk GUDANG PROTOL
        │
        ▼
Sistem cek: ada toko lain yang butuh?
        │
        ├── Ada ──► Kirim protol ke toko yang butuh ✅
        │
        └── Tidak ada ──► Stay di gudang protol
```

### Surplus Calculation Example

```
Contoh: Toko Matos — Total Kapasitas 100 artikel

Tier    Ideal %    Ideal Qty    Actual Qty    Actual %    Status
T1      30%        30           35            35%         Over +5 artikel
T2      25%        25           22            22%         Under -3 artikel
T3      20%        20           23            23%         Over +3 artikel
T4      15%        15           12            12%         (skip - promo)
T5      5%         5            4             4%          (skip - slow moving)
T8      5%         5            4             4%          (skip - protection)

Action:
- T1: Tarik 5 artikel dgn TO terendah → ke gudang protol
- T3: Tarik 3 artikel dgn TO terendah → ke gudang protol
- T2: Butuh restock 3 artikel → masuk restock flow
```

### Surplus Rules

1. Hanya T1, T2, T3 yang dicek — T4/T5 excluded (clearance), T8 excluded (protection 3 bulan)
2. Surplus = actual % - ideal % — hanya tier yang over-capacity yang ditarik
3. Prioritas tarik: TO terendah dulu — dead stock dan slow mover dalam tier itu keluar duluan
4. Semua surplus dari toko masuk gudang protol — ditarik per size, bukan per box utuh
5. Surplus tidak boleh store-to-store langsung — harus lewat gudang
6. Surplus di gudang protol otomatis masuk pool untuk RO Protol toko lain
7. T8 setelah 3 bulan → reclassify berdasarkan actual sales → ikut rules tier barunya
8. Manual override T8 hanya jika extremely over-capacity — case-by-case, bukan otomatis

---

## SIKLUS LENGKAP (Interconnected)

```
┌─────────────────────────────────────────────────────────────┐
│                    ALLOCATION PLANNER                        │
│              (Control & Approve semua flow)                  │
└──────────────┬──────────────────────────────┬───────────────┘
               │                              │
               ▼                              ▼
     ┌──── RESTOCK ────┐           ┌──── SURPLUS ────┐
     │                 │           │   (Tier-Based)   │
     │  Toko butuh     │           │  T1/T2/T3 over-  │
     │  stok           │           │  capacity → tarik │
     │                 │           │  TO rendah dulu   │
     └───────┬─────────┘           └────────┬─────────┘
             │                              │
             ▼                              ▼
     ┌───────────────┐             Tarik ke Gudang Protol
     │ % size kosong │                      │
     │ vs assortment │                      ▼
     └───┬───────┬───┘             ┌─────────────────┐
         │       │                 │  GUDANG PROTOL   │◄── Surplus masuk sini
    ≥50% │       │ <50%            │  (pool per size) │
         │       │                 └────────┬────────┘
         ▼       ▼                          │
    RO BOX    RO PROTOL ◄──────────────────┘
         │       │
         ▼       ▼
   ┌──────────┐  ┌──────────────────────────┐
   │ GUDANG   │  │ Tiered check:            │
   │ BOX      │  │ 1. Gudang Protol         │
   └────┬─────┘  │ 2. Surplus toko lain     │
        │        │ 3. Fallback RO Box       │
        ▼        └───────────┬──────────────┘
   Kirim box            Kirim protol/box
   ke toko              ke toko
        │                    │
        ▼                    ▼
   ┌─────────────────────────────────────┐
   │              TOKO                    │
   │   Display (planogram) + Storage      │
   │                                      │
   │   RO Box fallback surplus ──────────►│──► Kembali ke Surplus Flow
   └─────────────────────────────────────┘
```

---

## Edge Cases

### 1. RO Box fallback → surplus baru
Allocation Planner WAJIB pre-plan: size mana surplus setelah box masuk, kirim ke toko mana. Jika tidak ada demand, stay di storage (jika muat) atau tarik ke gudang.

### 2. T8 Protection Period
3 bulan protection: tidak boleh ditarik. Exception: manual override jika extremely over-capacity (case-by-case, documented). Setelah 3 bulan: reclassify ke tier baru.

### 3. Toko baru / Grand Opening
Full RO Box untuk semua artikel di planogram. Evaluasi surplus setelah 1 bulan. Tier capacity benchmark pakai toko serupa (size/area sama).

### 4. Artikel discontinued
Semua stok → surplus → tarik ke gudang protol. Redistribusi ke toko yang masih jual, atau markdown.

### 5. Gudang protol penuh
Prioritas redistribusi. Jika tidak ada demand → eskalasi ke Planner (markdown/promo/retur supplier).

### 6. Gudang box kosong
Flag ke procurement untuk PO. Sementara cek gudang protol untuk rakit assortment protol.

### 7. Semua tier under-capacity
Restock prioritas berdasarkan sales contribution: T1 → T2 → T3. T4/T5 hanya restock jika masih dalam program promo aktif.

### 8. T8 di toko over-capacity parah
Manual override oleh Planner. Documented: alasan, expected impact. T8 yang ditarik → gudang protol → redistribute ke toko lain yang masih dalam protection period.
