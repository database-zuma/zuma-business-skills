---
name: SPG Leaderboard Workflow
description: Complete data flow for SPG Leaderboard — sources, matching, calculation, export
type: reference
---

# SPG Leaderboard — Complete Workflow

## Data Sources

| Source | Endpoint | Origin | Cache |
|---|---|---|---|
| SPG Master | `/api/spg-master` | Google Sheets `1EEMBXrX2c-Dhr9NUwUylimOzEMBYxjhwxJ_jAkCrlXs` | 1 jam |
| Sales Data | `/api/sales/detail` | DB `core.iseller` (iSeller POS) | per session |
| Target Store | `/api/targets` | DB `portal.store_monthly_target` <- Sheets `1T1szUFDsN7XgU9_fzdDeBMp7OyQgXPruA9Ap_iSI0rM` sync tiap 2 jam | 5 menit |
| Refund Data | `/api/sales/refunds` | DB | per session |

## 1. SPG Master (nama SPG -> toko + area)

**Source**: Google Sheets `1EEMBXrX2c-...` — 7 sheet per area:
- SPG BALI -> area: Bali
- SPG JATIM -> area: Jawa Timur
- SPG LOMBOK -> area: Lombok
- SPG JAKARTA -> area: Jakarta
- SPG PEKANBARU -> area: Sumatera
- SPG BATAM & KEPRI -> area: Batam
- SPG SULAWESI -> area: Sulawesi

**Kolom per sheet**: STORE | NAMA KARYAWAN | NIK | HP | SUPERVISOR

**API**: `/api/spg-master` -> `[{name, store, area, nik, phone, supervisor}, ...]`

**Dashboard**: `SPG_MASTER = { "nama lowercase": { store, area } }`

**Store name normalization**: Raw nama toko dari Sheets (misal "STORE TABANAN") di-normalize ke display name (misal "Zuma Tabanan") via `STORE_NAME_MAP` di `/opt/zuma-api/routes/spg_master.py`.

## 2. Sales Data (transaksi per SPG)

**Source**: `/api/sales/detail` (iSeller POS data)

Setiap record: `{ spg, store, total, qty, order_no, date, kasir, ... }`
- `spg` = nama SPG/kasir yang handle transaksi
- `store` = nama toko iSeller
- `total` = nilai transaksi (Rp)
- `qty` = jumlah item
- `order_no` = nomor pesanan (unique per transaksi)

## 3. Target Store (target bulanan per toko)

**Source**: Google Sheets `1T1szUFDsN7XgU9_fzdDeBMp7OyQgXPruA9Ap_iSI0rM`

**Sync**: `/opt/zuma-api/sync_targets.py` -> cron tiap 2 jam -> DB `portal.store_monthly_target`

**API**: `/api/targets?year=2026` -> `{ "store_name_norm": { store, area, jan, feb, mar, apr, mei, ... } }`

**Struktur Sheets**:
- Row 0: Title "RINCIAN TARGET 2026"
- Row 2: Header (Branch | Nama Toko | Branch | Jan | Feb | Mar | Apr | Mei | Juni)
- Row 3+: Data per toko

## 4. Matching SPG -> Home Store

```
getSPGHomeStore(spgName):
  1. Exact match: SPG_MASTER["nama lowercase"]
  2. Alias match: SPG_ALIASES (hardcoded mapping nama iSeller beda dgn master)
     contoh: "yuni novianty" -> "kadek yuni novianty"
  3. Fuzzy match: key.includes(masterKey) || masterKey.includes(key)
  4. Not found -> null (fallback: toko dengan transaksi terbanyak)
```

## 5. Leaderboard Table (dashboard display)

```
salesDetailData (filtered by date range)
  -> Group by SPG name
  -> Per SPG:
     - sales     = SUM(total)
     - qty       = SUM(qty)
     - trx       = COUNT(DISTINCT order_no)
     - home store = getSPGHomeStore() -> SPG_MASTER
     - ATV       = sales / trx  (Average Transaction Value)
     - ATU       = qty / trx    (Average Transaction Unit)
     - ARP       = sales / qty  (Average Retail Price)
     - refund_qty = dari refundData.by_spg
  -> Sort by sales DESC
  -> Render: Rank | SPG | Toko | Qty | Trx | Sales | ATV | ATU | ARP
```

## 6. Export Excel

**Sheet 1: "SPG Leaderboard"**
Group by SPG + bulan. Per SPG per bulan:
- Tahun, Bulan, Area, Toko, Nama SPG
- Capaian Sales = SUM sales SPG di bulan tsb
- Target Toko = `portal.store_monthly_target[store][month]`
- Jumlah SPG = count SPG di toko tsb (dari SPG_MASTER)
- Jumlah Hari Kerja = Senin-Sabtu dalam bulan
- Target Daily = Target Toko / Hari Kerja / Jumlah SPG
- Target SPG = Target Toko / Jumlah SPG
- Achievement (%) = Capaian / Target SPG x 100

**Sheet 2: "Double Store"**
SPG yang transaksi di >1 toko (selain home store). Untuk deteksi SPG yang "pinjam" toko lain.

## 7. Dependency Chain

```
Google Sheets SPG Master --> /api/spg-master --> SPG_MASTER (nama->toko)
                                                      |
Google Sheets Target --> sync_targets.py --> DB --> /api/targets --> targetData
                                                      |
iSeller DB --> /api/sales/detail --> salesDetailData --> renderSalesSPG()
                                                      |
                                            SPG Leaderboard
                                            Table + Export
```

## Key Files

| File | Location | Purpose |
|---|---|---|
| spg_master.py | `/opt/zuma-api/routes/spg_master.py` | API endpoint + Sheets reader + store normalization |
| targets.py | `/opt/zuma-api/routes/targets.py` | API endpoint target store |
| sync_targets.py | `/opt/zuma-api/sync_targets.py` | Sheets -> DB sync script |
| dashboard | `dashboard_inventory.html` lines 9287-9650 | Frontend SPG leaderboard |

## SPG Area Metrics

Selain leaderboard, ada juga `renderSPGAreaMetrics()` (line 9832) yang menampilkan breakdown per area:
- Total SPG per area
- Total sales per area
- Average sales per SPG per area
