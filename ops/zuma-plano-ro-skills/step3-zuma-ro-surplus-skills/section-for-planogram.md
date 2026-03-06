## 1.11 Distribution Flow: Restock & Surplus → RO Request

Sistem distribusi terdiri dari 2 flow utama, keduanya di-trigger otomatis oleh sistem dengan kontrol eksekusi oleh **Allocation Planner**. Output akhir dari flow ini adalah **RO Request** — dokumen resmi mingguan yang diserahkan dari Area Supervisor ke Warehouse Supervisor.

### 1.11.1 Gudang & Tipe RO

ZUMA memiliki 2 gudang:
- **Gudang Box**: stok dalam kemasan box penuh (12 pairs, all sizes)
- **Gudang Protol**: stok eceran per size/pairs — juga menerima semua surplus dari toko

Ada 2 tipe Replenishment Order (RO):

| Tipe | Trigger | Source | Kirim |
|------|---------|--------|-------|
| **RO Box** | Size kosong ≥50% dari assortment artikel | Gudang Box | 1 box (12 pairs, all sizes) |
| **RO Protol** | Size kosong <50% dari assortment artikel | Gudang Protol | Hanya pairs di size yang kosong |

Key metrics:
- **Assortment** = jumlah size yang seharusnya tersedia untuk 1 artikel di toko
- **% Size Kosong** = (jumlah size stok 0) / (total assortment) × 100%
- **Tier Capacity %** = persentase ideal stok per tier dari total kapasitas toko
- **TO (Turnover)** = kecepatan jual artikel — semakin rendah, semakin lambat terjual

### 1.11.2 Restock Flow

**Trigger:** Sistem deteksi gap — stok aktual < kebutuhan (planogram display + storage allocation).

**Decision tree:**

```
Hitung % size kosong vs assortment
│
├─ ≥50% size kosong ──► RO BOX
│   └─ Cek Gudang Box
│       ├─ Ada → Allocation Planner approve → Kirim box ke toko ✅
│       └─ Tidak ada → Flag ke Planner (tunggu PO supplier)
│
└─ <50% size kosong ──► RO PROTOL (Tiered Fallback)
    │
    STEP 1: Cek Gudang Protol
    ├─ Ada → Kirim protol ke toko ✅
    └─ Tidak ada ↓
    │
    STEP 2: Cek surplus toko lain di size tersebut
    ├─ Ada → Tarik ke gudang protol → kirim protol ke toko yang butuh ✅
    └─ Tidak ada ↓
    │
    STEP 3: Fallback RO Box
    └─ Allocation Planner approve DENGAN FLAG:
       ⚠ "Size yang sudah ada di toko akan surplus setelah box masuk.
          WAJIB pre-plan redistribusi untuk size surplus tersebut."
       → Kirim box ke toko ✅
       → Pre-plan: size surplus kirim ke toko mana, atau stay di storage jika muat
```

**Restock rules:**
1. Prioritas selalu RO Protol — lebih efisien, tidak bikin surplus baru
2. RO Box hanya jika memang ≥50% size kosong, atau sebagai fallback terakhir
3. Setiap RO Box fallback WAJIB disertai surplus pre-plan — Planner harus sudah tahu size mana akan surplus dan destinasinya SEBELUM approve kirim
4. Allocation Planner = gatekeeper — sistem recommend, planner approve/reject/modify

**Penjelasan "surplus pre-plan":**

Contoh: Toko Matos punya Dallas Black, assortment 7 sizes (36-42).
- Stok aktual: 36 ✅, 37 ✅, 38 ✅, 39 ❌, 40 ❌, 41 ✅, 42 ✅
- Size kosong: 2/7 = 29% → trigger RO Protol
- Gudang protol tidak punya size 39, 40. Tidak ada surplus toko lain.
- Fallback: kirim 1 box (ALL sizes termasuk 36,37,38,41,42 yang sudah ada)
- Pre-plan: size 36,37,38,41,42 akan surplus setelah box masuk → Planner tentukan: kirim ke toko lain yang butuh, atau stay di storage jika muat

### 1.11.3 Surplus Flow (Tier-Based)

**Konsep utama:** Surplus BUKAN asal tarik barang. Surplus ditentukan berdasarkan **gap antara kapasitas ideal per tier vs stok aktual per tier**. Hanya tier over-capacity yang ditarik, dan yang ditarik adalah artikel dengan TO terendah.

**Tier yang dicek vs dikecualikan:**

| Tier | Surplus Check | Alasan |
|------|--------------|--------|
| T1 | ✅ Ya | Best seller — jaga proporsi |
| T2 | ✅ Ya | Secondary fast moving — jaga proporsi |
| T3 | ✅ Ya | Moderate — jaga proporsi |
| T4 | ❌ Tidak | Promo / clearance — tujuan menghabiskan stok |
| T5 | ❌ Tidak | Slow moving — biarkan habis / clearance |
| T8 | ❌ Tidak (3 bulan) | New launch — protection period test market |

**Surplus decision tree:**

```
Sistem hitung kapasitas per tier per toko
│
Bandingkan: Actual % vs Ideal Capacity % per tier
│
├─ T1: Ideal 30%, Actual 35% → Over +5% → SURPLUS CANDIDATE
├─ T2: Ideal 25%, Actual 22% → Under → SKIP (butuh restock)
├─ T3: Ideal 20%, Actual 23% → Over +3% → SURPLUS CANDIDATE
├─ T4: ──────────────────────────────────► SKIP (promo/clearance)
├─ T5: ──────────────────────────────────► SKIP (slow moving)
└─ T8: ──────────────────────────────────► SKIP (protection 3 bln)
│
Untuk tier OVER-CAPACITY:
│
1. Hitung selisih = Actual % - Ideal % → convert ke jumlah artikel
2. Ranking artikel di tier tsb by TO ascending (TO terendah = prioritas tarik)
3. Tarik artikel dgn TO terendah sampai selisih terpenuhi
4. Allocation Planner review & approve list tarik
5. Tarik dari toko → masuk GUDANG PROTOL
6. Cek ada toko lain yang butuh?
   ├─ Ada → kirim protol ke toko yang butuh ✅
   └─ Tidak ada → stay di gudang (future demand / markdown / promo)
```

**Surplus calculation example:**

```
Toko Matos — Total Kapasitas 100 artikel

Tier  Ideal%  IdealQty  ActualQty  Actual%  Status
T1    30%     30        35         35%      Over +5 → tarik 5 artikel (TO terendah)
T2    25%     25        22         22%      Under -3 → butuh restock
T3    20%     20        23         23%      Over +3 → tarik 3 artikel (TO terendah)
T4    15%     15        12         12%      SKIP (promo)
T5    5%      5         4          4%       SKIP (slow moving)
T8    5%      5         4          4%       SKIP (protection)
```

**Surplus rules:**
1. Hanya T1, T2, T3 yang dicek — T4/T5 excluded, T8 excluded (3 bulan)
2. Surplus = actual % - ideal % — hanya over-capacity yang ditarik
3. Prioritas tarik: TO terendah dulu (dead stock keluar pertama)
4. Semua surplus masuk gudang protol — ditarik per size, bukan per box
5. Tidak boleh store-to-store langsung — harus lewat gudang
6. Surplus di gudang protol otomatis jadi pool supply untuk RO Protol toko lain

### 1.11.4 T8 Lifecycle

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

### 1.11.5 Siklus Lengkap (Interconnected)

```
         ALLOCATION PLANNER (control semua flow)
              │                    │
              ▼                    ▼
         RESTOCK              SURPLUS (Tier-Based)
         Toko butuh           T1/T2/T3 over-capacity
         stok                 → tarik TO rendah
              │                    │
              ▼                    ▼
         ┌─────────┐        Masuk GUDANG PROTOL ◄── surplus masuk sini
         │% size   │              │
         │kosong   │              │
         └─┬───┬───┘              │
       ≥50%│   │<50%              │
           ▼   ▼                  │
        RO BOX  RO PROTOL ◄──────┘ (surplus = supply protol)
           │    │
           ▼    ▼
        GUDANG  Tiered: protol → surplus toko lain → fallback box
           │    │
           ▼    ▼
         ┌──────────────────────┐
         │        TOKO          │
         │  Display + Storage   │
         │  RO Box surplus ────►│──► kembali ke surplus flow
         └──────────────────────┘
```

### 1.11.6 Edge Cases Distribusi

1. **RO Box fallback → surplus baru**: Planner WAJIB pre-plan destinasi surplus SEBELUM approve kirim box
2. **T8 protection override**: Hanya jika extremely over-capacity. Case-by-case, documented, T8 ditarik → gudang protol → redistribute ke toko lain yang masih protection
3. **Toko baru / Grand Opening**: Full RO Box semua artikel planogram. Evaluasi surplus setelah 1 bulan. Benchmark pakai toko serupa
4. **Artikel discontinued**: Semua stok → surplus → gudang protol → redistribusi atau markdown
5. **Gudang protol penuh**: Prioritas redistribusi. Tidak ada demand → eskalasi Planner (markdown/promo/retur)
6. **Gudang box kosong**: Flag procurement untuk PO. Cek gudang protol untuk rakit assortment sementara
7. **Semua tier under-capacity**: Restock prioritas: T1 → T2 → T3 berdasarkan sales contribution
8. **T8 reclassified ke T4/T5**: Masuk clearance, tidak ditarik surplus, biarkan habis atau markdown

### 1.11.7 RO Request Output (Step 3)

Semua logic di atas menghasilkan **RO Request** — dokumen Excel 5 sheet:

| Sheet | Isi | Format |
|-------|-----|--------|
| RO Request | Cover page, summary (protol/box/surplus count), instructions, signature block | Dokumen resmi AS → WH Supervisor |
| Daftar RO Protol | 1 row per artikel: No, Article, Kode Mix, Tier, Sizes Needed (size:qty), Total Pairs | Grouped by size — WH picker tau size mana aja yang perlu diambil |
| Daftar RO Box | 1 row per artikel: No, Article, Kode Mix, Tier, Box Qty (always 1), WH Available (YES/NO) | 1 box = 12 pairs all sizes |
| Daftar Surplus | 1 row per artikel+size: No, Article, Kode Mix, Size, Pairs to Pull | Size-level detail untuk WH picker tarik dari display |
| Reference | Tier capacity analysis + full article status + off-planogram articles | Internal use (tidak dicetak) |

**Pipeline dependency**: RO Request membutuhkan planogram sebagai input.

```
Pre-Planogram → Planogram (Step 1) → Visual Planogram (Step 2) → RO Request (Step 3)
```

**Script**: `build_ro_{store}.py` — configurable per store via `STORE_NAME`, `STORE_DB_PATTERN`, `STORAGE_CAPACITY`.

**Dependencies**: `pip install psycopg2-binary openpyxl`

Lihat `SKILL.md` (zuma-distribution-flow) untuk dokumentasi lengkap format output, styling, dan script reference.
