# Zuma Data Analyst — ETL Pipeline, Admin & Setup Guide

> This file contains ETL schedule details, database administration queries, and the setup guide for non-technical users.
> Referenced from `SKILL.md` in the same directory.

---

## ETL / Auto-Update Schedule

Cron jobs on the VPS pull data from Accurate Online API daily.

| Time (WIB) | Job | Description |
|-------------|-----|-------------|
| **02:00** | Database backup | Full `pg_dump` of `openclaw_ops` |
| **03:00** | Stock pull | All 4 entities (DDD, LJBB, MBB, UBB) — overwrites stock tables with latest snapshot |
| **05:00** | Sales pull | 3 entities (DDD, MBB, UBB) — incremental, pulls last 3 days to catch late-arriving invoices |

**No LJBB sales pull** — LJBB is a PO receiving entity only, no direct sales.

**ETL audit trail:**
```sql
SELECT * FROM raw.load_history ORDER BY loaded_at DESC LIMIT 20;
```

**iSeller data:** Currently minimal (`raw.iseller_sales`). Integration still evolving — structure may change.

---

## Database Administration Quick Reference

### Check ETL Status
```sql
SELECT entity, table_name, row_count, loaded_at
FROM raw.load_history
ORDER BY loaded_at DESC
LIMIT 10;
```

### Check Data Freshness
```sql
-- Latest sales date per entity
SELECT source_entity, MAX(transaction_date) AS latest_sale
FROM core.fact_sales_unified
GROUP BY 1;

-- Latest stock snapshot
SELECT source_entity, MAX(snapshot_date) AS latest_snapshot
FROM core.fact_stock_unified
GROUP BY 1;
```

### Check Match Rates
```sql
-- Sales kodemix match rate
SELECT
    COUNT(*) AS total_rows,
    COUNT(kode_mix) AS matched,
    ROUND(COUNT(kode_mix)::numeric / COUNT(*) * 100, 1) AS match_pct
FROM core.sales_with_product;

-- Stock kodemix match rate
SELECT
    COUNT(*) AS total_rows,
    COUNT(kode_mix) AS matched,
    ROUND(COUNT(kode_mix)::numeric / COUNT(*) * 100, 1) AS match_pct
FROM core.stock_with_product;
```

### List All Tables/Views in a Schema
```sql
SELECT table_schema, table_name, table_type
FROM information_schema.tables
WHERE table_schema IN ('raw', 'portal', 'core', 'mart', 'public')
ORDER BY table_schema, table_name;
```

### Table Row Counts
```sql
SELECT schemaname, relname, n_live_tup AS estimated_rows
FROM pg_stat_user_tables
WHERE schemaname IN ('raw', 'portal', 'core', 'mart', 'public')
ORDER BY n_live_tup DESC;
```

---

## Setup Guide — Persiapan Mesin untuk Non-Teknis

> **Siapa yang butuh baca ini?**
> Kamu yang bukan programmer tapi perlu menjalankan script Python Zuma — seperti generate planogram, RO Request, laporan stok, analisis penjualan, dll.
> Panduan ini step-by-step, asumsi kamu mulai dari NOL.

### Install Python

Python adalah "mesin" yang menjalankan semua script Zuma.

**Windows:**
1. Buka https://www.python.org/downloads/
2. Klik **Download Python 3.13** (atau versi terbaru, minimal 3.8)
3. **PENTING**: Di installer, centang **"Add Python to PATH"** (ada di bawah, jangan sampai kelewat!)
4. Klik **Install Now**
5. Setelah selesai, buka **Command Prompt** (ketik `cmd` di Start Menu) dan ketik:
   ```
   python --version
   ```
   Kalau muncul `Python 3.13.x` → berhasil.

**macOS:**
```bash
# Buka Terminal, lalu:
brew install python
# Kalau belum ada Homebrew: https://brew.sh
```

**Cek apakah Python sudah ada:**
```
python --version
# atau
python3 --version
```
Kalau muncul versi 3.8 ke atas → sudah aman, skip langkah install.

### Install Library Python

Library = "alat tambahan" yang dibutuhkan script. Buka Command Prompt / Terminal, lalu jalankan:

```bash
pip install psycopg2-binary openpyxl pandas
```

| Library | Fungsi | Kenapa Dibutuhkan |
|---------|--------|-------------------|
| `psycopg2-binary` | Koneksi ke database PostgreSQL | Semua script perlu ambil data dari VPS database Zuma |
| `openpyxl` | Baca dan tulis file Excel (.xlsx) | Generate planogram, RO Request, laporan — semua output-nya Excel |
| `pandas` | Olah data (tabel, filter, grouping) | Proses data sebelum ditulis ke Excel |

**Kalau ada error saat install:**

| Error | Solusi |
|-------|--------|
| `'pip' is not recognized` | Python belum di-PATH. Uninstall Python, install ulang, pastikan centang "Add to PATH" |
| `pip: command not found` (Mac) | Coba `pip3 install ...` |
| `error: Microsoft Visual C++ is required` | Install Visual Studio Build Tools dari https://visualstudio.microsoft.com/visual-cpp-build-tools/ |
| `permission denied` | Tambah `--user` di akhir: `pip install --user psycopg2-binary openpyxl pandas` |

**Verifikasi instalasi berhasil:**
```bash
python -c "import psycopg2; import openpyxl; import pandas; print('Semua library OK!')"
```
Kalau muncul `Semua library OK!` → lanjut.

### Cek Akses ke Database VPS

Database Zuma ada di server VPS (IP: `76.13.194.120`). Komputer kamu harus bisa "reach" server ini.

**Test koneksi (dari Command Prompt / Terminal):**
```bash
python -c "
import psycopg2
conn = psycopg2.connect(host='76.13.194.120', port=5432, dbname='openclaw_ops', user='openclaw_app', password='Zuma-0psCl4w-2026!')
cur = conn.cursor()
cur.execute('SELECT COUNT(*) FROM core.stock_with_product')
print(f'Koneksi berhasil! Stock rows: {cur.fetchone()[0]}')
conn.close()
"
```

**Kalau berhasil:** Muncul `Koneksi berhasil! Stock rows: 142xxx` → lanjut.

**Kalau gagal:**

| Error | Artinya | Solusi |
|-------|---------|--------|
| `connection refused` | VPS tidak bisa dicapai dari jaringan kamu | Hubungi admin IT — mungkin perlu VPN atau IP kamu perlu di-whitelist di VPS |
| `timeout` / `could not connect` | Sama — jaringan terblokir | Coba dari WiFi lain, atau minta admin buka port 5432 untuk IP kamu |
| `password authentication failed` | Password salah | Cek ulang password di section 1 skill ini |
| `database "openclaw_ops" does not exist` | Konek ke server lain atau DB belum dibuat | Pastikan host `76.13.194.120` dan dbname `openclaw_ops` |

### Download Script dari GitHub

Semua script Zuma ada di repo **private** GitHub:

```bash
git clone https://github.com/database-zuma/zuma-business-skills.git
```

**Kalau belum ada Git:**
1. Download dari https://git-scm.com/downloads
2. Install (default settings semua OK)
3. Buka ulang Command Prompt, coba `git --version`

**Kalau tidak mau install Git:**
- Buka https://github.com/database-zuma/zuma-business-skills
- Login dengan akun GitHub yang punya akses
- Klik **Code** → **Download ZIP**
- Extract ZIP-nya

**Struktur penting setelah download:**
```
zuma-business-skills/
└── ops/
    └── zuma-plano-and-ro/
        ├── step1-planogram/
        │   ├── build_royal_planogram.py      ← Script planogram Royal Plaza
        │   └── build_tunjungan_planogram.py  ← Script planogram Tunjungan
        ├── step2-visualizations/
        │   ├── visualize_planogram.py        ← Visual planogram Royal Plaza
        │   └── visualize_tunjungan_planogram.py
        └── step3-ro-request/
            └── build_ro_royal_plaza.py       ← Script RO Request Royal Plaza
```

### Menjalankan Script

**Contoh: Generate RO Request untuk Royal Plaza:**

1. Buka Command Prompt / Terminal
2. Navigasi ke folder script:
   ```bash
   cd path/ke/zuma-business-skills/ops/zuma-plano-and-ro/step3-ro-request
   ```
3. Jalankan:
   ```bash
   python build_ro_royal_plaza.py
   ```
4. Tunggu ~10-30 detik (koneksi ke database, proses data, tulis Excel)
5. File output muncul di folder yang sama: `RO_REQUEST_Royal_Plaza.xlsx`
6. Buka file Excel-nya — siap cetak dan serahkan ke Warehouse Supervisor

**PENTING:** Beberapa script butuh file input (seperti planogram Excel). Pastikan file `RO Input Jatim.xlsx` ada di folder yang benar (biasanya satu level di atas folder script).

### Pakai Claude Code (AI-Assisted) — Opsional

Kalau kamu pakai **Claude Code** (Anthropic CLI), AI bisa generate dan jalankan script langsung. Lebih mudah — kamu tinggal bilang apa yang mau dianalisis.

**Install Claude Code:**
```bash
npm install -g @anthropic-ai/claude-code
```
(Butuh Node.js — download dari https://nodejs.org jika belum ada)

**Install Zuma skills ke Claude Code:**
```bash
# Clone repo (kalau belum)
git clone https://github.com/database-zuma/zuma-business-skills.git ~/.claude/skills-repo

# Copy skills
# Windows PowerShell:
Copy-Item -Recurse "$env:USERPROFILE\.claude\skills-repo\general\*" "$env:USERPROFILE\.claude\skills\" -Force
Copy-Item -Recurse "$env:USERPROFILE\.claude\skills-repo\ops\*" "$env:USERPROFILE\.claude\skills\" -Force

# macOS/Linux:
cp -r ~/.claude/skills-repo/general/* ~/.claude/skills/
cp -r ~/.claude/skills-repo/ops/* ~/.claude/skills/
```

**Setelah install, di Claude Code kamu bisa bilang:**
```
"Generate RO Request mingguan untuk Zuma Royal Plaza"
"Analisa penjualan Classic Jet Black di semua toko Jatim bulan ini"
"Cek stok Warehouse Pusat — artikel mana yang tinggal sedikit?"
```
Claude otomatis load skill yang relevan dan tau cara query database-nya.

### Checklist Persiapan Lengkap

Sebelum bisa menjalankan script apapun, pastikan semua ini sudah OK:

| # | Item | Cara Cek | Status |
|---|------|----------|--------|
| 1 | Python 3.8+ ter-install | `python --version` → muncul versi | |
| 2 | `pip` tersedia | `pip --version` → muncul versi | |
| 3 | `psycopg2-binary` ter-install | `python -c "import psycopg2"` → no error | |
| 4 | `openpyxl` ter-install | `python -c "import openpyxl"` → no error | |
| 5 | `pandas` ter-install | `python -c "import pandas"` → no error | |
| 6 | Bisa konek ke VPS database | Test koneksi (lihat section di atas) → muncul row count | |
| 7 | Script sudah di-download | Folder `zuma-business-skills/` ada | |
| 8 | File input tersedia | `RO Input {Region}.xlsx` ada di folder yang benar | |

**Kalau semua sudah OK → kamu siap jalankan script apapun.**

### Troubleshooting Umum

| Masalah | Penyebab | Solusi |
|---------|----------|--------|
| `ModuleNotFoundError: No module named 'psycopg2'` | Library belum di-install | `pip install psycopg2-binary` |
| `ModuleNotFoundError: No module named 'openpyxl'` | Library belum di-install | `pip install openpyxl` |
| `SyntaxError: invalid syntax` | Python versi lama (< 3.8) | Upgrade Python ke 3.8+ |
| `UnicodeEncodeError` | Windows console encoding | Script Zuma sudah handle ini otomatis. Kalau masih muncul, tambah `chcp 65001` sebelum jalankan script |
| `FileNotFoundError: RO Input Jatim.xlsx` | File planogram tidak ditemukan | Pastikan path relatif benar. Biasanya 1 folder di atas script |
| `PermissionError: ... .xlsx` | File Excel masih dibuka | Tutup dulu file Excel-nya, baru jalankan script lagi |
| Script jalan tapi output Excel kosong | Planogram tidak ada data untuk toko tersebut | Cek sheet "Planogram" di file input — pastikan ada baris untuk toko target |
| `psycopg2.OperationalError: connection refused` | Tidak bisa konek ke VPS | Lihat troubleshooting di section Cek Akses ke Database VPS |
| Excel output tidak rapi (tanpa warna/border) | `openpyxl` versi terlalu lama | `pip install --upgrade openpyxl` (minimal versi 3.1+) |
