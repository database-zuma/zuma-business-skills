---
name: data-visualization
description: "Chart and graph generation for Zuma business reports. Creates visual output (PNG/HTML) from sales, stock, and performance data using matplotlib/plotly. Zuma brand colors (#002A3A teal, #00E273 green). Use when user asks for 'grafik', 'chart', 'visualisasi data', 'plot tren', or any visual representation of data beyond text tables."
user-invocable: false
---

# Data Visualization — Zuma Reports

Skill ini menghasilkan grafik dan chart dari data operasional Zuma. Output bisa berupa PNG (untuk WA/laporan) atau HTML interaktif (untuk dashboard/Eos).

## Kapan Digunakan

- Tren sales per bulan/minggu (line chart)
- Perbandingan performa antar toko/cabang (bar chart)
- Distribusi sell-through (histogram / box plot)
- Komposisi sales per kategori/tier (pie/donut)
- Heatmap performa toko per artikel
- Gabung dengan statistical-analysis untuk visualisasi insight

---

## Library

| Library | Gunakan untuk |
|---------|--------------|
| `matplotlib` + `seaborn` | PNG output, laporan statis |
| `plotly` | HTML interaktif, dashboard |

**Default:** `matplotlib` untuk output ke WA (PNG). `plotly` untuk output ke HTML/Eos.

---

## Zuma Brand Palette

```python
ZUMA_TEAL    = "#002A3A"   # Header, primary dark
ZUMA_GREEN   = "#00E273"   # Highlight, positive, target
ZUMA_LIGHT   = "#E8F5E9"   # Background light
ZUMA_RED     = "#FF4444"   # Deficit, warning, negative
ZUMA_GRAY    = "#9E9E9E"   # Secondary, grid lines
ZUMA_WHITE   = "#FFFFFF"

# Palette untuk multi-series
ZUMA_PALETTE = ["#002A3A", "#00E273", "#4CAF50", "#80CBC4", "#B2DFDB", "#FF4444"]
```

---

## 1. Tren Sales (Line Chart)

```python
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import pandas as pd

def plot_sales_trend(df_monthly, title="Sales Trend", output_path="sales_trend.png"):
    """
    df_monthly: DataFrame dengan kolom ['bulan', 'total_sales']
    bulan: string YYYY-MM atau datetime
    """
    fig, ax = plt.subplots(figsize=(10, 5))
    fig.patch.set_facecolor('#FAFAFA')

    ax.plot(df_monthly['bulan'], df_monthly['total_sales'],
            color="#002A3A", linewidth=2.5, marker='o', markersize=5, label='Actual')

    # Moving average (opsional)
    if len(df_monthly) >= 3:
        df_monthly['ma3'] = df_monthly['total_sales'].rolling(3).mean()
        ax.plot(df_monthly['bulan'], df_monthly['ma3'],
                color="#00E273", linewidth=1.5, linestyle='--', label='MA 3 bulan')

    # Format Y axis ke Rupiah
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(
        lambda x, _: f"Rp {x/1_000_000:.0f}M"
    ))

    ax.set_title(title, fontsize=14, fontweight='bold', color="#002A3A", pad=15)
    ax.set_xlabel("Periode", fontsize=10)
    ax.set_ylabel("Total Sales", fontsize=10)
    ax.tick_params(axis='x', rotation=45)
    ax.legend()
    ax.grid(axis='y', alpha=0.3)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    return output_path
```

---

## 2. Perbandingan Toko / Cabang (Bar Chart)

```python
def plot_store_comparison(df, value_col, label_col, title, output_path="bar.png"):
    """
    df: DataFrame
    value_col: kolom angka (misal 'total_sales')
    label_col: kolom label (misal 'nama_toko')
    """
    df = df.sort_values(value_col, ascending=True)  # ascending=True → horizontal bar terbalik

    fig, ax = plt.subplots(figsize=(10, max(5, len(df) * 0.4)))
    fig.patch.set_facecolor('#FAFAFA')

    # Color bars: top 3 hijau, bottom 3 merah, sisanya teal
    colors = ["#9E9E9E"] * len(df)
    colors[-3:] = ["#00E273"] * 3   # top 3 (karena ascending)
    colors[:3]  = ["#FF4444"] * 3   # bottom 3

    bars = ax.barh(df[label_col], df[value_col], color=colors)

    # Label di ujung bar
    for bar in bars:
        val = bar.get_width()
        ax.text(bar.get_x() + bar.get_width() + val * 0.01,
                bar.get_y() + bar.get_height() / 2,
                f"Rp {val/1_000_000:.1f}M",
                va='center', fontsize=8, color="#002A3A")

    ax.set_title(title, fontsize=14, fontweight='bold', color="#002A3A")
    ax.set_xlabel("Total Sales", fontsize=10)
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"Rp {x/1_000_000:.0f}M"))
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.grid(axis='x', alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    return output_path
```

---

## 3. Komposisi per Kategori (Donut Chart)

```python
def plot_donut(df, value_col, label_col, title, output_path="donut.png"):
    fig, ax = plt.subplots(figsize=(7, 7))
    fig.patch.set_facecolor('#FAFAFA')

    wedges, texts, autotexts = ax.pie(
        df[value_col],
        labels=df[label_col],
        autopct='%1.1f%%',
        pctdistance=0.75,
        wedgeprops=dict(width=0.5),  # donut hole
        colors=ZUMA_PALETTE[:len(df)],
        startangle=90
    )

    for at in autotexts:
        at.set_fontsize(9)
        at.set_fontweight('bold')

    ax.set_title(title, fontsize=14, fontweight='bold', color="#002A3A", pad=20)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    return output_path
```

---

## 4. Distribusi (Box Plot — Outlier Detection)

```python
def plot_boxplot(df, value_col, group_col=None, title="Distribusi", output_path="boxplot.png"):
    import seaborn as sns

    fig, ax = plt.subplots(figsize=(10, 5))
    fig.patch.set_facecolor('#FAFAFA')

    if group_col:
        sns.boxplot(data=df, x=group_col, y=value_col,
                    palette=[ZUMA_TEAL, ZUMA_GREEN, "#4CAF50", "#80CBC4"], ax=ax)
    else:
        sns.boxplot(data=df, y=value_col, color=ZUMA_TEAL, ax=ax)

    ax.set_title(title, fontsize=14, fontweight='bold', color="#002A3A")
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"Rp {x/1_000_000:.0f}M"))
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.grid(axis='y', alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    return output_path
```

---

## 5. Heatmap (Performa Toko × Artikel)

```python
def plot_heatmap(pivot_df, title="Heatmap", output_path="heatmap.png"):
    """pivot_df: DataFrame dengan toko di index, artikel di columns, nilai di cells"""
    import seaborn as sns

    fig, ax = plt.subplots(figsize=(max(10, len(pivot_df.columns) * 0.8),
                                    max(6, len(pivot_df) * 0.5)))

    sns.heatmap(pivot_df, annot=True, fmt=".0f", cmap="YlGn",
                linewidths=0.5, ax=ax,
                cbar_kws={'label': 'Qty'})

    ax.set_title(title, fontsize=14, fontweight='bold', color="#002A3A")
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    return output_path
```

---

## 6. Dashboard Multi-Chart (4 Panel)

```python
def plot_dashboard(data_dict, title="Zuma Dashboard", output_path="dashboard.png"):
    """
    data_dict = {
        'trend': df_monthly,         # bulan, total_sales
        'by_store': df_stores,       # nama_toko, total_sales
        'by_category': df_cat,       # kategori, pct
        'monthly_growth': df_growth  # bulan, growth_pct
    }
    """
    fig = plt.figure(figsize=(16, 10))
    fig.patch.set_facecolor('#FAFAFA')
    fig.suptitle(title, fontsize=16, fontweight='bold', color="#002A3A", y=1.01)

    # Layout 2x2
    gs = fig.add_gridspec(2, 2, hspace=0.4, wspace=0.3)

    ax1 = fig.add_subplot(gs[0, :])  # Full width top — trend
    ax2 = fig.add_subplot(gs[1, 0]) # Bottom left — by store
    ax3 = fig.add_subplot(gs[1, 1]) # Bottom right — category

    # Plot 1: Trend line (top full width)
    df_t = data_dict['trend']
    ax1.plot(df_t['bulan'], df_t['total_sales'], color=ZUMA_TEAL, linewidth=2, marker='o')
    ax1.set_title("Sales Trend", fontsize=12, fontweight='bold')
    ax1.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"Rp {x/1e6:.0f}M"))
    ax1.grid(axis='y', alpha=0.3)

    # Plot 2: Bar by store
    df_s = data_dict['by_store'].head(10).sort_values('total_sales')
    ax2.barh(df_s['nama_toko'], df_s['total_sales'], color=ZUMA_TEAL)
    ax2.set_title("Top 10 Toko", fontsize=12, fontweight='bold')
    ax2.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"Rp {x/1e6:.0f}M"))

    # Plot 3: Donut category
    df_c = data_dict['by_category']
    ax3.pie(df_c['pct'], labels=df_c['kategori'], autopct='%1.0f%%',
            colors=ZUMA_PALETTE[:len(df_c)], wedgeprops=dict(width=0.5))
    ax3.set_title("Komposisi per Kategori", fontsize=12, fontweight='bold')

    for ax in [ax1, ax2]:
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)

    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    return output_path
```

---

## Output Convention

```python
import os

# Simpan ke outbox nanobot
output_dir = os.path.expanduser("~/.openclaw/workspace-argus-nanobot/outbox/")
os.makedirs(output_dir, exist_ok=True)

output_path = os.path.join(output_dir, "sales_trend_feb2026.png")
plot_sales_trend(df, title="Sales Trend Feb 2026", output_path=output_path)
print(f"Chart saved: {output_path}")
```

Setelah generate:
1. Upload ke GDrive via `gog drive upload {path}`
2. Kirim image langsung ke WA kalau bisa (embed)
3. Atau share link GDrive

---

## Checklist Sebelum Deliver

- [ ] Title jelas (include periode/konteks)
- [ ] Axis labels ada dan readable
- [ ] Y-axis diformat ke Rupiah (kalau currency)
- [ ] DPI >= 150 (clear di mobile)
- [ ] Tidak ada overlap label
- [ ] Warna Zuma konsisten (teal/green/red)
- [ ] File tersimpan di outbox/
