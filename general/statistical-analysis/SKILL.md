---
name: statistical-analysis
description: "Statistical analysis skill for Zuma business data. Compute descriptive stats (mean, median, std dev, percentile), trend analysis, correlation, and basic regression on sales, stock, and performance data. Upgrades Argus/Metis report quality from plain aggregations to statistical insights. Use when user wants 'analisis mendalam', 'trend analysis', 'outlier detection', 'performa toko vs rata-rata', atau butuh angka statistik yang credible."
user-invocable: false
---

# Statistical Analysis — Zuma Business Data

Skill ini upgrade kualitas analisis dari sekadar "total penjualan bulan ini X" menjadi insight statistik: distribusi, outlier, tren, korelasi, dan perbandingan yang meaningful.

## Kapan Digunakan

- User minta analisis performa toko vs rata-rata regional
- Deteksi outlier (toko overperform / underperform)
- Trend analysis sales per periode
- Korelasi antara dua variabel (misal: sell-through vs stok awal)
- Membandingkan dua periode atau dua kelompok toko
- Forecasting sederhana berdasarkan historis

---

## Library yang Digunakan

```python
import pandas as pd
import numpy as np
from scipy import stats
import statistics
```

Untuk analisis berat: `pingouin`, `statsmodels` (install kalau belum ada).

---

## 1. Descriptive Statistics (Paling Sering Dipakai)

### Basic Stats dari Query Result

```python
import pandas as pd
import numpy as np

# Contoh: data sales per toko
df = pd.DataFrame({
    'kode_toko': ['JT001', 'JT002', 'JT003', 'JT004', 'JT005'],
    'total_sales': [45_000_000, 32_000_000, 67_000_000, 28_000_000, 55_000_000]
})

sales = df['total_sales']

stats_summary = {
    'n_toko': len(sales),
    'total': sales.sum(),
    'rata_rata': sales.mean(),
    'median': sales.median(),
    'std_dev': sales.std(),
    'min': sales.min(),
    'max': sales.max(),
    'p25': sales.quantile(0.25),
    'p75': sales.quantile(0.75),
    'iqr': sales.quantile(0.75) - sales.quantile(0.25),
    'cv_%': (sales.std() / sales.mean()) * 100  # Coefficient of variation
}

for k, v in stats_summary.items():
    print(f"{k}: {v:,.0f}" if isinstance(v, float) else f"{k}: {v}")
```

### Output Format untuk Report Iris

```
📊 Statistik Sales — Cabang Jatim (Feb 2026)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
N toko       : 15
Total sales  : Rp 847.500.000
Rata-rata    : Rp 56.500.000
Median       : Rp 52.300.000
Std Dev      : Rp 18.200.000
Min          : Rp 28.000.000 (Toko Sidoarjo)
Max          : Rp 95.400.000 (Toko Surabaya Pusat)
P25 – P75    : Rp 42M – Rp 68M
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## 2. Outlier Detection (Toko Abnormal)

### Metode IQR (Robust, Recommended)

```python
Q1 = df['total_sales'].quantile(0.25)
Q3 = df['total_sales'].quantile(0.75)
IQR = Q3 - Q1

lower_bound = Q1 - 1.5 * IQR
upper_bound = Q3 + 1.5 * IQR

df['status'] = 'normal'
df.loc[df['total_sales'] < lower_bound, 'status'] = '🔴 underperform (outlier)'
df.loc[df['total_sales'] > upper_bound, 'status'] = '🟢 overperform (outlier)'

outliers = df[df['status'] != 'normal']
print(outliers[['kode_toko', 'total_sales', 'status']])
```

### Metode Z-Score (kalau data normal distributed)

```python
from scipy import stats

df['z_score'] = np.abs(stats.zscore(df['total_sales']))
df['is_outlier'] = df['z_score'] > 2.0  # threshold: 2 std dev

# |z| > 2 = unusual, |z| > 3 = extreme outlier
```

---

## 3. Trend Analysis (Sales Over Time)

### Month-over-Month Growth

```python
df_monthly = df.sort_values('bulan')
df_monthly['mom_growth_%'] = df_monthly['total_sales'].pct_change() * 100
df_monthly['mom_abs'] = df_monthly['total_sales'].diff()

# Simple trend (naik/turun/flat)
last_3 = df_monthly['total_sales'].tail(3).values
if last_3[-1] > last_3[0]:
    trend = "📈 Naik"
elif last_3[-1] < last_3[0]:
    trend = "📉 Turun"
else:
    trend = "➡️ Flat"
```

### Moving Average (Smoothing)

```python
df_monthly['ma_3m'] = df_monthly['total_sales'].rolling(window=3).mean()
df_monthly['ma_6m'] = df_monthly['total_sales'].rolling(window=6).mean()
```

### Simple Linear Trend

```python
from scipy import stats

# Hitung apakah ada tren signifikan
x = np.arange(len(df_monthly))
y = df_monthly['total_sales'].values

slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)

print(f"Tren: {'naik' if slope > 0 else 'turun'} Rp {abs(slope):,.0f}/bulan")
print(f"R²: {r_value**2:.3f} ({'tren kuat' if r_value**2 > 0.7 else 'lemah'})")
print(f"Signifikan: {'Ya' if p_value < 0.05 else 'Tidak'} (p={p_value:.3f})")
```

---

## 4. Perbandingan Dua Periode / Kelompok

### Period Comparison (Simple)

```python
feb_sales = df[df['bulan'] == '2026-02']['total_sales']
jan_sales = df[df['bulan'] == '2026-01']['total_sales']

change = (feb_sales.sum() - jan_sales.sum()) / jan_sales.sum() * 100
print(f"Feb vs Jan: {change:+.1f}%")
```

### T-Test (Apakah perbedaan signifikan secara statistik?)

```python
from scipy import stats

# Contoh: bandingkan sales toko mall vs ruko
mall_sales = df[df['tipe'] == 'mall']['total_sales']
ruko_sales = df[df['tipe'] == 'ruko']['total_sales']

t_stat, p_value = stats.ttest_ind(mall_sales, ruko_sales)

print(f"Mall avg: Rp {mall_sales.mean():,.0f}")
print(f"Ruko avg: Rp {ruko_sales.mean():,.0f}")
print(f"Perbedaan signifikan: {'Ya' if p_value < 0.05 else 'Tidak'} (p={p_value:.3f})")
```

---

## 5. Korelasi

### Korelasi Sell-Through vs Stok Awal

```python
# Pearson (linear relationship)
corr, p_val = stats.pearsonr(df['stok_awal'], df['sell_through_pct'])
print(f"Korelasi stok awal vs sell-through: r={corr:.3f} (p={p_val:.3f})")

# Interpretasi:
# r > 0.7  → korelasi kuat positif
# 0.3-0.7  → korelasi sedang
# < 0.3    → korelasi lemah
# negatif  → berbanding terbalik
```

### Correlation Matrix (Multi-variabel)

```python
cols = ['total_sales', 'stok_awal', 'sell_through_pct', 'jumlah_sku']
corr_matrix = df[cols].corr()
print(corr_matrix.round(2))
```

---

## 6. Ranking & Percentile

### Ranking Toko

```python
df['rank'] = df['total_sales'].rank(ascending=False).astype(int)
df['percentile'] = df['total_sales'].rank(pct=True) * 100

# Top 20% performer
top_performers = df[df['percentile'] >= 80].sort_values('total_sales', ascending=False)
# Bottom 20%
bottom_performers = df[df['percentile'] <= 20].sort_values('total_sales')
```

---

## 7. Forecasting Sederhana

### Linear Projection

```python
# Proyeksi bulan depan berdasarkan tren linear
months_ahead = 1
projected = intercept + slope * (len(df_monthly) + months_ahead - 1)
print(f"Proyeksi bulan depan: Rp {projected:,.0f}")
```

### YTD Run Rate Annualization

```python
current_month = 2  # Feb
ytd_sales = 847_500_000
annualized = (ytd_sales / current_month) * 12
print(f"Full-year run rate: Rp {annualized:,.0f}")
```

---

## Format Output Statistik ke User

Gunakan format ini saat deliver ke Wayan via WA:

```
📊 *Analisis [Topik] — [Periode]*

*Ringkasan:*
• Total: Rp X
• Rata-rata per toko: Rp X
• Median: Rp X (tengah distribusi)
• Std Dev: Rp X (variasi antar toko)

*Outlier:*
🟢 Overperform (top): [Toko A] Rp X (+Y% dari rata-rata)
🔴 Underperform: [Toko B] Rp X (-Y% dari rata-rata)

*Tren:*
📈/📉 [Naik/Turun] X% vs bulan lalu
Tren 3 bulan: [deskripsi]

*Insight:*
[1-2 kalimat actionable insight]
```

---

## Notes

- Selalu sertakan n (jumlah data points) dalam laporan
- Kalau data < 10 toko, jangan pakai t-test — gunakan perbandingan deskriptif saja
- Untuk data Zuma: gunakan schema `core.*`, `portal.*`, atau `mart.*` — JANGAN `raw.*`
- Currency dalam Rupiah, format: `Rp 1.234.567` (titik ribuan, koma desimal)


---

## File Input: Data dari Dokumen User

Kalau data yang akan dianalisis berasal dari **file yang dikirim user** (PDF laporan, Excel, CSV, Word), gunakan `markitdown` sebagai pre-processing:

```bash
# Convert ke markdown dulu, baru analisis
markitdown laporan_sales.pdf > data.md
markitdown data_toko.xlsx > data.md
markitdown export.csv > data.md
```

Setelah convert, extract angka/tabel dari markdown untuk dimasukkan ke pipeline statistik. Lihat: `markitdown` skill untuk format yang didukung.
