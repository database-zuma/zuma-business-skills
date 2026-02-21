## 1.11 Distribution Flow TRANSISI: Urgent Surplus → RO Budget-Capped → Surplus Output

Sistem distribusi TRANSISI terdiri dari **3 tahap berurutan** (bukan parallel), di-trigger otomatis oleh sistem dengan kontrol eksekusi oleh **Allocation Planner**. Output akhir adalah **RO Request**.

**Konsep inti**: RO bukan untuk menutup 100% maxstock gap. RO hanya "menukar" barang buruk (off-planogram) dengan barang bagus (on-planogram yang kosong). **Pairs IN ≈ Pairs OUT (urgent surplus only)**. Jika urgent surplus = 0, RO proceeds normally tanpa budget cap.

### 1.11.1 Gudang & Tipe RO — TRANSISI

ZUMA memiliki 2 gudang:
- **Gudang Box**: stok dalam kemasan box penuh (12 pairs, all sizes)
- **Gudang Protol**: stok eceran per size/pairs — juga menerima semua surplus dari toko

Ada 2 tipe RO — **Box adalah DEFAULT**:

| Tipe | Trigger | Source | Kirim |
|------|---------|--------|-------|
| **RO Box** ⭐ DEFAULT | **3+ size kosong** dari assortment | Gudang Box | 1 box (12 pairs, all sizes) |
| **RO Protol** | **1-2 size kosong** (minor gap) | Gudang Protol | Hanya pairs di size yang kosong |

Key metrics:
- **Assortment** = jumlah size yang seharusnya tersedia untuk 1 artikel di toko
- **% Size Kosong** = (jumlah size stok 0) / (total assortment) × 100%
- **Tier Capacity %** = persentase ideal stok per tier dari total kapasitas toko
- **TO (Turnover)** = kecepatan jual artikel — semakin rendah, semakin lambat terjual

### 1.11.2 Urgent Surplus Identification — TRANSISI (TAHAP 0)

Sebelum restock, sistem scan **semua artikel yang ada stok di toko** dan bandingkan dengan **planogram baru**:
- Artikel **tidak ada di planogram baru** tapi **punya stok di toko** = **URGENT surplus** (off-planogram)
- Total pairs urgent surplus = **budget RO** (pairs yang boleh masuk ≈ pairs yang harus keluar)
- Jika urgent surplus = 0 → RO **uncapped** (fallback normal)

### 1.11.3 Restock Flow — TRANSISI (TAHAP 1: Box Default, Budget-Capped)

**Trigger:** Sistem deteksi gap — stok aktual < kebutuhan (planogram display + storage allocation).

**Decision tree:**

```
Hitung jumlah size kosong (count)
│
├─ 3+ size kosong ──► RO BOX ⭐ (DEFAULT)
│   └─ Cek Gudang Box WH Pusat
│       ├─ Ada → Tampil di daftar RO Box → Planner approve → Kirim ✅
│       │         Surplus dari Box = ACCEPTED (ditarik di TAHAP 2)
│       └─ Tidak ada → EXCLUDE dari daftar (tidak ditampilkan)
│
└─ 1-2 size kosong ──► RO PROTOL (Gap Minor)
    └─ Cek Gudang Protol
        ├─ Ada → Kirim protol ke toko ✅
        └─ Tidak ada → Fallback RO Box (surplus = accepted)
```

**Budget capping (if urgent > 0):**
```
Full RO list (uncapped) → cap_ro_to_budget(budget = total_urgent_pairs)
│
Prioritization sort:
├─ 1st: Artikel dengan ≥50% size kosong (paling butuh restock)
└─ 2nd: Best seller (avg_monthly_sales tertinggi)
│
Greedy knapsack: iterate sorted list, add if fits budget, skip if too big (continue, not break)
│
Result: capped RO list where total pairs ≈ urgent surplus pairs
```

**Restock rules TRANSISI:**
1. **RO Box adalah DEFAULT** — 3+ size kosong langsung kirim box
2. RO Protol hanya untuk gap minor (1-2 size kosong)
3. **RO budget = urgent surplus pairs** — total restock ≈ total urgent surplus yang keluar
4. **Prioritas RO**: (1) ≥50% sizes empty first, (2) best sellers. Goal: "size full di artikel best seller"
5. Surplus dari Box = accepted — tidak perlu pre-plan, akan ditarik di TAHAP 2
6. **WH Stock Filter** — Jika WH Pusat stok box = 0 untuk artikel tertentu, artikel **tidak ditampilkan** di daftar RO Box (di-exclude, bukan ditandai "NO")
7. Allocation Planner = gatekeeper — sistem recommend, planner approve/reject/modify

### 1.11.4 Surplus Flow — TRANSISI (TAHAP 2: Dua Kategori)

Surplus sekarang terbagi **dua kategori**:

| Kategori | Definisi | Aksi | Warna di Excel |
|----------|----------|------|----------------|
| **URGENT** (off-planogram) | Artikel tidak di planogram baru tapi punya stok di toko | **HARUS ditarik minggu ini** | 🟠 Orange |
| **REGULAR** (over-capacity) | Artikel on-planogram yang stoknya melebihi kapasitas tier (post-restock) | **Visibility/planning only** | 🟣 Purple |

**URGENT surplus** sudah di-identify di TAHAP 0. **REGULAR surplus** dihitung SETELAH restock masuk.

Untuk REGULAR surplus:
- Stok yang dipakai = **stok POST-restock** (snapshot + RO Box + RO Protol)
- **Off-planogram articles tidak inflate tier count** — tidak ditambahkan ke actual_tier_articles
- Surplus ditentukan berdasarkan **gap antara kapasitas ideal per tier vs stok aktual POST-restock per tier**. Hanya tier over-capacity, artikel TO terendah yang ditarik.

**Tier yang dicek vs dikecualikan:**

| Tier | Surplus Check | Alasan |
|------|--------------|--------|
| T1 | ✅ Ya | Best seller — jaga proporsi |
| T2 | ✅ Ya | Secondary fast moving — jaga proporsi |
| T3 | ✅ Ya | Moderate — jaga proporsi |
| T4 | ❌ Tidak | Promo / clearance — tujuan menghabiskan stok |
| T5 | ❌ Tidak | Slow moving — biarkan habis / clearance |
| T8 | ❌ Tidak (3 bulan) | New launch — protection period test market |

**Surplus decision tree — TRANSISI:**

```
TAHAP 1 SELESAI: Restock (RO Box + RO Protol) sudah dikirim
│
▼
SIMULASI STOK POST-RESTOCK
= Stok snapshot + RO Box (12 pairs all sizes) + RO Protol (pairs per size)
│
▼
Hitung kapasitas per tier per toko (dari stok POST-RESTOCK)
│
Bandingkan per tier: Actual POST-RESTOCK % vs Ideal Capacity %
│
├─ T1: Ideal 30%, Actual 40% → Over +10% → SURPLUS CANDIDATE
│      (lebih tinggi karena Box masuk)
├─ T2: Ideal 25%, Actual 28% → Over +3%  → SURPLUS CANDIDATE
├─ T3: Ideal 20%, Actual 22% → Over +2%  → SURPLUS CANDIDATE
├─ T4: ──────────────────────────────────► SKIP (promo/clearance)
├─ T5: ──────────────────────────────────► SKIP (slow moving)
└─ T8: ──────────────────────────────────► SKIP (protection 3 bln)
│
Untuk tier OVER-CAPACITY (post-restock):
│
1. Hitung selisih = Actual POST-RESTOCK % - Ideal % → convert ke jumlah artikel
2. Ranking artikel di tier tsb by TO ascending (TO terendah = prioritas tarik)
3. Tarik artikel dgn TO terendah sampai selisih terpenuhi
4. Allocation Planner review & approve list tarik
5. Tarik dari toko → masuk GUDANG PROTOL
6. Cek ada toko lain yang butuh?
   ├─ Ada → kirim protol ke toko yang butuh ✅
   └─ Tidak ada → stay di gudang (future demand / markdown / promo)
```

**Surplus calculation example — TRANSISI:**

```
Toko Matos — Total Kapasitas 100 artikel
SETELAH restock (10 artikel dapat RO Box, 3 artikel dapat RO Protol)

Tier  Ideal%  IdealQty  Post-Restock Qty  Actual%  Status
T1    30%     30        40                37%      Over +10 → tarik 10 artikel (TO terendah)
T2    25%     25        28                26%      Over +3 → tarik 3 artikel (TO terendah)
T3    20%     20        22                20%      Over +2 → tarik 2 artikel (TO terendah)
T4    15%     15        12                11%      SKIP (promo)
T5    5%      5         4                 4%       SKIP (slow moving)
T8    5%      5         3                 3%       SKIP (protection)

NOTE: Surplus numbers lebih tinggi dari logic lama karena Box sudah masuk.
Ini INTENTIONAL — Box dikirim dulu untuk display lengkap, lalu kelebihan ditarik.
```

**Surplus rules — TRANSISI:**
1. **URGENT surplus = off-planogram articles** — HARUS ditarik, menentukan RO budget
2. **REGULAR surplus dihitung SETELAH restock masuk** — stok = snapshot + RO Box + RO Protol yang dikirim
3. **Off-planogram articles tidak inflate tier count** — hanya on-planogram yang dihitung sebagai actual_tier_articles
4. Hanya T1, T2, T3 yang dicek untuk REGULAR — T4/T5 excluded, T8 excluded (3 bulan)
5. REGULAR surplus = actual POST-RESTOCK % - ideal % — hanya tier over-capacity
6. Prioritas tarik (REGULAR): TO terendah dulu (dead stock keluar pertama)
7. **Surplus dari RO Box = expected behavior** — bukan masalah, ini fitur
8. Semua surplus masuk gudang protol — ditarik per size, bukan per box
9. Tidak boleh store-to-store langsung — harus lewat gudang
10. Surplus di gudang protol otomatis jadi pool supply untuk RO Protol toko lain

### 1.11.5 T8 Lifecycle

```
LAUNCH (Bulan ke-0)
│
▼
Protection Period (Bulan 1-3)
- Tidak boleh ditarik sebagai surplus
- Data sales dikumpulkan untuk evaluasi
- Exception: manual override oleh Planner jika extremely over-capacity (case-by-case, documented)
│
▼
RECLASSIFICATION (Bulan ke-4)
├─ Sales bagus → masuk T1/T2/T3 → ikut rules surplus tier barunya
└─ Sales jelek → masuk T4/T5 → exclude dari surplus (clearance)
```

### 1.11.6 Siklus Lengkap — TRANSISI (Urgent → RO Budget-Capped → Surplus)

```
┌─────────────────────────────────────────────────────────────┐
│                    ALLOCATION PLANNER                        │
│              (Control & Approve semua flow)                  │
└──────────────────────────┬──────────────────────────────────┘
                           │
         ══════════════════════════════════════════
         ║  TAHAP 0: IDENTIFIKASI URGENT SURPLUS  ║
         ══════════════════════════════════════════
                           │
                           ▼
              Scan stok toko vs planogram baru
              Off-planogram = URGENT surplus
              Total urgent pairs = RO BUDGET
                           │
         ══════════════════════════════════════════
         ║  TAHAP 1: RESTOCK (Budget = Urgent)    ║
         ══════════════════════════════════════════
                           │
                           ▼
                  ┌────────────────┐
                  │ Hitung size    │
                  │ kosong per     │
                  │ artikel        │
                  └──┬──────────┬──┘
                     │          │
               3+ size │    1-2 size │
               kosong  │    kosong   │
                     ▼          ▼
              ⭐ RO BOX    RO PROTOL
              (DEFAULT)    (minor gap)
                     │          │
                     └────┬─────┘
                          ▼
              ┌─────────────────────────────┐
              │ CAP RO TO BUDGET            │
              │ 1. ≥50% sizes empty FIRST   │
              │ 2. Best sellers SECOND      │
              │ Total RO ≈ urgent pairs     │
              └────────────┬────────────────┘
                           │
                           ▼
              ┌─────────────────────────────────────┐
              │              TOKO                    │
              │   Restock masuk → display lengkap    │
              │   Pairs IN ≈ Pairs OUT (urgent)     │
              └──────────────────┬──────────────────┘
                                 │
         ══════════════════════════════════════════
         ║  TAHAP 2: SURPLUS (URGENT + REGULAR)   ║
         ══════════════════════════════════════════
                                 │
                    ┌────────────┴────────────┐
                    │                         │
                    ▼                         ▼
        🟠 URGENT SURPLUS          🟣 REGULAR SURPLUS
        (off-planogram)            (on-plano, over-capacity)
        HARUS ditarik              Visibility/planning only
                    │                         │
                    └────────────┬─────────────┘
                                 ▼
              ┌─────────────────┐
              │  GUDANG PROTOL   │◄── Semua surplus masuk sini
              │  (pool per size) │
              └────────┬────────┘
                       │
                       ▼
              Ada toko lain butuh?
              ├── Ya ──► Kirim protol ✅
              └── Tidak ──► Stay di gudang
```

### 1.11.7 Edge Cases Distribusi — TRANSISI

1. **RO Box → surplus baru (EXPECTED BEHAVIOR)**: Surplus dari Box = normal dan accepted. Tidak perlu pre-plan — surplus dihitung otomatis di TAHAP 2 dan ditarik setelahnya. Planner cukup review list surplus final.
2. **T8 protection override**: Hanya jika extremely over-capacity. Case-by-case, documented, T8 ditarik → gudang protol → redistribute ke toko lain yang masih protection
3. **Toko baru / Grand Opening**: Full RO Box semua artikel planogram. Evaluasi surplus setelah 1 bulan. Benchmark pakai toko serupa
4. **Artikel discontinued**: Semua stok → surplus → gudang protol → redistribusi atau markdown
5. **Gudang protol penuh**: Prioritas redistribusi. Tidak ada demand → eskalasi Planner (markdown/promo/retur)
6. **Gudang box kosong**: Flag procurement untuk PO. Cek gudang protol untuk rakit assortment sementara
7. **Semua tier under-capacity**: Restock prioritas: T1 → T2 → T3 berdasarkan sales contribution
8. **T8 reclassified ke T4/T5**: Masuk clearance, tidak ditarik surplus, biarkan habis atau markdown

### 1.11.8 RO Request Output (Step 3)

Semua logic di atas menghasilkan **RO Request** — dokumen Excel 5 sheet:

| Sheet | Isi | Format |
|-------|-----|--------|
| RO Request | Cover page, summary (protol/box/urgent surplus/regular surplus/total), instructions, signature block | Dokumen resmi AS → WH Supervisor |
| Daftar RO Protol | 1 row per artikel: No, Article, Kode Mix, Tier, Sizes Needed (size:qty), Total Pairs | Grouped by size |
| Daftar RO Box | 1 row per artikel: No, Article, Kode Mix, Tier, Box Qty (always 1), WH Available (YES/NO) | 1 box = 12 pairs all sizes |
| Daftar Surplus | **Dua section**: 🟠 URGENT (off-plano, harus ditarik) + 🟣 REGULAR (over-capacity, visibility only) + Grand Total | Size-level detail |
| Reference | Tier capacity analysis + full article status + off-planogram articles | Internal use (tidak dicetak) |

**Pipeline dependency**: RO Request membutuhkan planogram sebagai input.

```
Pre-Planogram → Planogram (Step 1) → Visual Planogram (Step 2) → RO Request (Step 3)
```

**Script**: `build_ro_{store}.py` — configurable per store via `STORE_NAME`, `STORE_DB_PATTERN`, `STORAGE_CAPACITY`.

**Dependencies**: `pip install psycopg2-binary openpyxl`

Lihat `SKILL.md` (zuma-distribution-flow) untuk dokumentasi lengkap format output, styling, dan script reference.
