---
name: iris-openclaw-data-analyst-guided
description: "Guided analysis workflow — bukan langsung jawab, tapi proactively suggest pertanyaan yang bisa dijawab dari data yang ada, lalu guide user ke insight yang paling berguna. Use when: user minta 'analisis data', 'cek performa', atau pertanyaan open-ended tentang bisnis Zuma. Upgrade dari reactive querying ke proactive insight generation."
user-invocable: false
---

# Guided Data Analyst — Iris OpenClaw

Jangan langsung jawab pertanyaan vague dengan data mentah. Guide user ke pertanyaan yang tepat, lalu deliver insight yang actionable.

## Core Workflow (4 Steps)

```
Step 1: CLARIFY   → Tanya konteks yang dibutuhkan (kalau belum jelas)
Step 2: SUGGEST   → Propose 3-5 pertanyaan spesifik yang bisa dijawab dari data
Step 3: ANALYZE   → Query + hitung (pakai statistical-analysis skill)
Step 4: NARRATE   → Deliver insight, bukan raw data
```

---

## Step 1: Clarify (kalau input terlalu vague)

Kalau user bilang "cek performa toko" atau "gimana sales kita":

```
Mau cek yang mana dulu?

Periode: Bulan ini / bulan lalu / YTD / custom?
Scope: Semua toko / per cabang / toko tertentu?
Metrik: Revenue / qty / sell-through / growth / ranking?
```

Jangan tanya semua sekaligus. Pilih 1-2 yang paling krusial, tanya itu dulu.

---

## Step 2: Suggest — Proactive Question Menu

Ketika punya dataset, proactively tawarkan pertanyaan yang bisa dijawab:

**Template untuk sales data:**
```
Dari data sales [periode] yang saya punya, bisa gue jawab:

1. 🏆 Ranking toko — mana yang paling kenceng, mana yang perlu perhatian?
2. 📈 Tren — naik/turun vs bulan lalu? Ada pola musiman?
3. 🎯 Target vs actual — toko mana yang on-track, mana yang meleset?
4. 🔍 Outlier — toko mana yang performa-nya abnormal (jauh di atas/bawah rata-rata)?
5. 📦 Per artikel — produk mana yang paling laku, mana yang stagnan?

Mau mulai dari yang mana?
```

**Template untuk stock data:**
```
Dari data stok yang ada:

1. ⚠️ Critical stock — artikel di bawah safety stock yang perlu di-RO sekarang?
2. 📦 Surplus — toko mana yang overstocked dan bisa di-pull?
3. 🔄 Sell-through rate — artikel mana yang bergerak cepat vs lambat?
4. 📍 Distribusi — stok per toko sudah sesuai planogram?

Yang mana prioritas?
```

---

## Step 3: Analyze — Jangan Sekedar Dump Data

Setelah tahu pertanyaan yang mau dijawab:

1. Query DB dengan filter yang tepat (lihat `zuma-data-analyst-skill` untuk SQL templates)
2. Hitung metrics yang relevan (lihat `statistical-analysis` skill)
3. Identifikasi outlier dan pattern
4. Siapkan narrative — bukan raw tabel

**Pola analysis per metrik:**

| Pertanyaan | Analysis | Output |
|-----------|---------|--------|
| Ranking toko | Sort by revenue, hitung percentile | Top 5, Bottom 5, median |
| Tren | MoM/YoY growth, MA 3 bulan | % change, direction |
| Outlier | IQR / z-score | Toko yang signifikan berbeda |
| Target vs actual | Selisih absolut & % | On-track / at-risk / missed |
| Per artikel | Sort by qty / revenue | Fast movers, slow movers |

---

## Step 4: Narrate — Deliver Insight, Bukan Tabel

**❌ Raw data dump:**
```
| Toko | Sales | Growth |
|------|-------|--------|
| Surabaya | 95.4M | +15% |
| Malang | 72.1M | +8% |
| Sidoarjo | 41.2M | -8% |
...
```

**✅ Narrative insight:**
```
📊 Sales Jatim Feb — Quick Take:

Rata-rata toko: Rp 56.5M. Median: Rp 52.3M. Spread cukup lebar (std dev Rp 18.2M) — 
artinya ada gap signifikan antar toko.

🟢 Outperformer: Surabaya (Rp 95.4M, +15%) — jauh di atas, konsisten 3 bulan terakhir.

🔴 Perlu perhatian: Sidoarjo (Rp 41.2M, -8%) — ini bulan ke-2 turun berturut-turut. 
Biasanya stabil di Rp 45-48M. Ada yang perlu dicek di lapangan?

📈 Overall Jatim: Rp 847.5M, up 12% vs Jan. Di atas target bulanan (Rp 800M) ✓
```

---

## Kapan Skip Step 2 (Langsung Analisis)

Kalau pertanyaan user sudah spesifik dan clear:
- "ranking toko Jatim bulan ini" → langsung query + deliver
- "stok ZM-COSMO-38 di semua toko" → langsung query

Step 2 (suggest) hanya untuk pertanyaan vague atau ketika user mungkin tidak tau apa yang perlu dicek.

---

## Combine dengan Skill Lain

- **statistical-analysis** → untuk hitung rata-rata, outlier, tren, korelasi
- **markitdown** → kalau user upload/kirim file (PDF, Excel, Word, PPT) — convert dulu ke markdown sebelum analisis
- **data-visualization** → kalau user mau chart/grafik
- **iris-openclaw-anti-hallucination** → tag semua data dengan sumber
- **iris-openclaw-communication-humanizer** → humanize output sebelum deliver
