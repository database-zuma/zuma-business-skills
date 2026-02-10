<p align="center">
  <img src="https://img.shields.io/badge/ZUMA-Business_Skills-00E273?style=for-the-badge&labelColor=002A3A" alt="Zuma Business Skills"/>
  <br/>
  <img src="https://img.shields.io/badge/Claude_Code-Skills_Library-7C3AED?style=flat-square" alt="Claude Code"/>
  <img src="https://img.shields.io/badge/Status-Active-00E273?style=flat-square" alt="Active"/>
  <img src="https://img.shields.io/badge/Skills-8_Installed-FF6B35?style=flat-square" alt="8 Skills"/>
  <img src="https://img.shields.io/badge/Updated-Feb_2026-blue?style=flat-square" alt="Updated"/>
</p>

<h1 align="center">Zuma Business Skills</h1>

<p align="center">
  <strong>AI Skills Library untuk Zuma Indonesia</strong>
  <br/>
  Kumpulan modul pengetahuan bisnis yang bikin Claude Code (dan AI agent lainnya) langsung paham konteks Zuma — mulai dari produk, toko, gudang, sampai data analytics.
  <br/><br/>
  <em>Skill baru terus ditambahkan. Skill yang ada terus di-upgrade.<br/>Pastikan selalu pull versi terbaru.</em>
</p>

---

## Apa Ini?

Repo ini berisi **skill files untuk Claude Code** (file `.md` dengan YAML frontmatter) yang ngajarin AI semua hal tentang bisnis Zuma Indonesia. Begitu di-install, Claude Code otomatis load skill yang relevan sesuai konteks pertanyaan.

**Analoginya:** Pengetahuan institusional Zuma, dikemas supaya bisa dikonsumsi AI.

```
Kamu:    "Analisa penjualan Classic Jet Black di Bali 3 bulan terakhir
          dan cek stok terkini di tiap toko"

Claude:  *otomatis load zuma-data-ops + zuma-sku-context + zuma-branch*
         *tau koneksi DB, SQL join yang bener, sistem Kode Mix versioning,
          3 sub-area Bali, dan kasih hasil analisis yang akurat*
```

---

## Cara Kerjanya

```
                      PERTANYAAN KAMU
                            |
                            v
                 +--------------------+
                 |   Claude Code CLI  |
                 |   deteksi konteks  |
                 +--------------------+
                            |
                  otomatis load skill yg cocok
                            |
        +-------+-------+-------+-------+-------+
        |       |       |       |       |       |
        v       v       v       v       v       v
    +-------+-------+-------+-------+-------+-------+
    |COMPANY|  SKU  |BRANCH |GUDANG | DATA  |FUTURE |
    |CONTEXT|CONTEXT|       |& STOK |  OPS  |SKILLS |
    +-------+-------+-------+-------+-------+-------+
    |Brand, |Kode   |6      |WHS/   |Postgre|Finance|
    |tone,  |Mix,   |cabang,|WHJ/   |SQL VPS|HRGA,  |
    |warna, |tier,  |toko,  |WHB,   |5 sche-|Market-|
    |4 PT   |assort.|area   |RO sys |ma, SQL|place  |
    +-------+-------+-------+-------+-------+-------+
        |       |       |       |       |
        +-------+-------+-------+-------+
                        |
                        v
            +------------------------+
            |  AI nulis SQL yang     |
            |  bener, paham konteks  |
            |  bisnis, kasih hasil   |
            |  analisis akurat       |
            +------------------------+
                        |
                        v
            JAWABAN YANG AKURAT & KONTEKSTUAL
```

---

## Penting: Transaksi Affiliasi

> **Skills di repo ini sudah otomatis meng-exclude transaksi affiliasi (inter-company) dari semua analisis.**

Zuma punya 4 entitas (DDD, MBB, UBB, LJBB) yang kadang saling "jual" di atas kertas untuk keperluan perpajakan. Transaksi ini **bukan penjualan nyata** — kalau ikut dihitung, revenue jadi double-counting.

**Contoh:** Di tabel penjualan DDD, ada transaksi ke "CV Makmur Besar Bersama" (= MBB). Ini bukan jualan ke customer beneran, ini transfer antar entitas.

Skill `zuma-data-ops` sudah mendokumentasikan daftar lengkap nama pelanggan inter-company dan cara filter-nya. Semua tabel `mart.*` (yang dipakai buat dashboard & analisis) sudah exclude transaksi ini secara default.

**Kalau kamu butuh data termasuk transaksi affiliasi**, bilang secara eksplisit ke AI: *"include transaksi affiliasi"* — baru dia akan query dari `core.*` tanpa filter.

---

## Struktur Repo

```
zuma-business-skills/
|
|-- general/                              LINTAS DEPARTEMEN (brand, identitas)
|   +-- zuma-company-context/
|       |-- SKILL.md                        Brand identity, 4 entitas, data sources
|       +-- brand-guidelines.md             Warna, tipografi, estetika Japandi
|
|-- ops/                                  DEPARTEMEN OPERASIONAL
|   |-- zuma-sku-context/
|   |   +-- SKILL.md                        Hierarki produk, Kode Mix, tier, assortment
|   |-- zuma-branch/
|   |   +-- SKILL.md                        6 cabang, jaringan toko, operasional retail
|   |-- zuma-warehouse-and-stocks/
|   |   +-- SKILL.md                        3 gudang, tahapan stok, sistem RO
|   |-- zuma-data-ops/
|   |   +-- SKILL.md                        PostgreSQL VPS, schema, SQL cookbook, analisis
|   +-- zuma-plano-and-ro/                PLANOGRAM & RO REQUEST PIPELINE
|       |-- PROMPT_new_planogram.md         Prompt template: generate planogram baru
|       |-- PROMPT_ro_request.md            Prompt template: generate RO Request (single/multi store)
|       |-- step1-planogram/                Step 1: Planogram generation
|       |   |-- SKILL_planogram_zuma_v3.md    Skill planogram v3.2 (1400+ baris)
|       |   |-- SKILL_planogram_zuma_v2.md    Skill planogram v2 (legacy)
|       |   |-- build_royal_planogram.py      Script: Royal Plaza planogram
|       |   +-- build_tunjungan_planogram.py  Script: Tunjungan Plaza planogram
|       |-- step2-visualizations/           Step 2: Visual planogram
|       |   |-- SKILL_visualized-plano_zuma_v1.md  Skill visualisasi v1.2
|       |   |-- visualize_planogram.py        Script: Royal Plaza visual
|       |   +-- visualize_tunjungan_planogram.py  Script: Tunjungan visual
|       +-- step3-ro-request/               Step 3: RO Request & Surplus
|           |-- SKILL.md                      Distribution flow skill (surplus/restock rules)
|           |-- section-for-planogram.md      Planogram reference section
|           +-- build_ro_royal_plaza.py       Script: Royal Plaza RO Request
|
|-- finance/                              DEPARTEMEN FINANCE (segera hadir)
|   +-- README.md
|
|-- hrga/                                 DEPARTEMEN HR & GA (segera hadir)
|   +-- README.md
|
|-- README.md                             File ini
+-- CHANGELOG.md                          Riwayat perubahan
```

> **Pipeline Flow:**
> ```
> Pre-Planogram → Step 1: Planogram → Step 2: Visual Planogram → Step 3: RO Request
> ```
> Setiap step punya skill `.md` + script `.py` sendiri. Prompt template tersedia untuk generate planogram baru maupun RO Request mingguan.

### Kenapa Dipisah per Folder?

| Folder | Fungsi | Siapa yang Pakai |
|--------|--------|------------------|
| `general/` | Pengetahuan lintas departemen — brand, struktur entitas | Semua orang |
| `ops/` | Pengetahuan operasional — produk, toko, gudang, data analytics | Tim ops, data analyst, AI agent |
| `finance/` | Pengetahuan keuangan — P&L, margin, COGS, pajak | Tim finance (planned) |
| `hrga/` | Pengetahuan HR & GA — struktur organisasi, kebijakan | Tim HR (planned) |

Folder departemen baru akan ditambahkan seiring ekspansi automasi AI Zuma.

---

## Daftar Skill

### General (Lintas Departemen)

| Skill | Baris | Apa yang Diketahui |
|-------|-------|--------------------|
| **zuma-company-context** | 137 | Brand tone (witty/casual/confident), visual identity (Japandi, Zuma Teal `#002A3A`, Zuma Green `#00E273`), 4 entitas bisnis (DDD, MBB, UBB, LJBB), sumber data (Accurate, iSeller, Ginee) |

### Operations

| Skill | Baris | Apa yang Diketahui |
|-------|-------|--------------------|
| **zuma-sku-context** | 376 | Hierarki produk (Type > Gender > Series > Article > Size), sistem versioning Kode Mix, pola assortment (12 pasang/box), klasifikasi 6 tier (T1-T5 + T8) |
| **zuma-branch** | 575 | 6 cabang (Jatim, Jakarta, Sumatra, Sulawesi, Batam, Bali), kategori toko (RETAIL/NON-RETAIL/EVENT), format mall vs Ruko, Area Supervisor, kapasitas stok |
| **zuma-warehouse-and-stocks** | 385 | 3 gudang fisik (WHS/WHJ/WHB), formula stok (ready = whs - queue - picked - ...), alur status RO lengkap, variance tracking |
| **zuma-data-ops** | 760+ | Koneksi PostgreSQL VPS, 5 schema (raw/portal/core/mart/public), definisi semua tabel/view, 7 aturan SQL kritikal (termasuk filter transaksi affiliasi), 9 template query, metodologi analisis, jadwal ETL |

### Planogram & RO Pipeline (`zuma-plano-and-ro/`)

| Skill / File | Baris | Apa yang Diketahui |
|--------------|-------|--------------------|
| **SKILL_planogram_zuma_v3** | 1400+ | Full planogram generation: tier assignment, capacity allocation, size-level target, assortment rules, DB queries, Excel output format. Versi terbaru (v3.2) |
| **SKILL_visualized-plano_zuma_v1** | 700+ | Planogram visualization: heatmap per tier, stock vs target comparison, color coding, openpyxl styling. Versi v1.2 |
| **zuma-distribution-flow** (SKILL.md) | 283 | Surplus & restock rules: RO Protol (<50% empty), RO Box (>=50% empty), surplus sort (slowest seller first), same-day restock+pull, WH Pusat source rules (DDD+LJBB for Box, DDD only for Protol) |
| **PROMPT_new_planogram.md** | — | Template prompt untuk generate planogram baru (single store) |
| **PROMPT_ro_request.md** | 172 | Template prompt untuk generate RO Request mingguan: single store, multi-store (region), custom (protol-only/box-only/surplus-only). Termasuk store name reference table |

---

## Instalasi

### Prasyarat

- [Claude Code CLI](https://docs.anthropic.com/en/docs/claude-code) sudah ter-install
- Akses Git ke repo private ini
- **Python 3.8+** dengan library berikut (untuk generate planogram & RO Request):

```bash
pip install psycopg2-binary openpyxl
```

| Library | Versi Tested | Fungsi |
|---------|-------------|--------|
| `openpyxl` | 3.1.5 | Baca/tulis Excel (.xlsx) — planogram, RO Request, visualisasi. Library ini yang bikin output Excel rapi dengan formatting, merged cells, conditional coloring, dll. |
| `psycopg2-binary` | 2.9.11 | Koneksi ke PostgreSQL VPS (openclaw_ops) — query stock, sales, warehouse data |

> **Tanpa `openpyxl`**, AI agent tidak bisa generate file Excel yang rapi. Pastikan sudah ter-install.

### Cara Cepat (Recommended)

Clone repo, lalu copy skill ke direktori Claude:

**Windows (PowerShell):**
```powershell
# Clone repo
git clone https://github.com/database-zuma/zuma-business-skills.git "$env:USERPROFILE\.claude\skills-repo"

# Copy skill general
Copy-Item -Recurse "$env:USERPROFILE\.claude\skills-repo\general\*" "$env:USERPROFILE\.claude\skills\" -Force

# Copy skill ops
Copy-Item -Recurse "$env:USERPROFILE\.claude\skills-repo\ops\*" "$env:USERPROFILE\.claude\skills\" -Force
```

**macOS / Linux:**
```bash
# Clone repo
git clone https://github.com/database-zuma/zuma-business-skills.git ~/.claude/skills-repo

# Copy semua skill
cp -r ~/.claude/skills-repo/general/* ~/.claude/skills/
cp -r ~/.claude/skills-repo/ops/* ~/.claude/skills/
```

### Install Pilihan

Cuma mau install skill tertentu? Bisa:

```bash
# Contoh: cuma data-ops dan sku-context
cp -r ~/.claude/skills-repo/ops/zuma-data-ops ~/.claude/skills/
cp -r ~/.claude/skills-repo/ops/zuma-sku-context ~/.claude/skills/
```

### Setelah Install

Direktori `~/.claude/skills/` kamu harusnya jadi kayak gini:

```
~/.claude/skills/
|-- zuma-company-context/
|   |-- SKILL.md
|   +-- brand-guidelines.md
|-- zuma-sku-context/
|   +-- SKILL.md
|-- zuma-branch/
|   +-- SKILL.md
|-- zuma-warehouse-and-stocks/
|   +-- SKILL.md
+-- zuma-data-ops/
    +-- SKILL.md
```

Restart Claude Code. Skill otomatis ter-load sesuai konteks — ga perlu invoke manual.

### Verifikasi

Di Claude Code session manapun, ketik:
```
/zuma-data-ops
```
Kalau skill ke-load dan nampil info database, berarti udah beres.

---

## Update Skill

> **Skill di repo ini aktif di-maintain dan di-improve.**
> Skill yang udah ada terus di-upgrade — kolom baru, query pattern baru, business rule yang dikoreksi.
> Skill baru ditambahkan seiring cakupan automasi AI Zuma meluas.
> **Selalu pull versi terbaru.**

### Cara Update

**Windows (PowerShell):**
```powershell
cd "$env:USERPROFILE\.claude\skills-repo"
git pull origin main
Copy-Item -Recurse .\general\* "$env:USERPROFILE\.claude\skills\" -Force
Copy-Item -Recurse .\ops\* "$env:USERPROFILE\.claude\skills\" -Force
# Tambahkan departemen baru kalau udah tersedia:
# Copy-Item -Recurse .\finance\* "$env:USERPROFILE\.claude\skills\" -Force
```

**macOS / Linux:**
```bash
cd ~/.claude/skills-repo && git pull origin main
cp -r general/* ~/.claude/skills/
cp -r ops/* ~/.claude/skills/
```

### Apa Aja yang Di-update?

| Jenis Update | Kapan | Contoh |
|-------------|-------|--------|
| Perubahan schema | Saat struktur DB berubah | Tabel/kolom/view baru |
| Aturan bisnis | Saat operasi berkembang | Cabang baru, kriteria tier berubah |
| Pattern query | Saat analisis umum teridentifikasi | Query cookbook baru, join dioptimasi |
| Bug fix | Saat masalah ditemukan | Nama kolom dikoreksi, match rate di-update |
| **Skill baru** | **Saat cakupan automasi meluas** | **Finance, HRGA, Marketplace, Creative** |

---

## Roadmap

### Skill yang Direncanakan

| Departemen | Skill | Cakupan | Status |
|------------|-------|---------|--------|
| **Finance** | `zuma-financial-analysis` | Struktur P&L, analisis margin, kalkulasi BPP/COGS | Planned |
| **HRGA** | `zuma-org-structure` | Struktur organisasi, jabatan, hierarki keputusan | Planned |
| **Ops** | `zuma-marketplace-ops` | Operasional Shopee/Tokopedia/TikTok Shop | Planned |
| **Ops** | `zuma-supply-chain` | Hubungan supplier (HJS/Ando), manajemen PO | Planned |
| **Creative** | `zuma-creative-hub` | Workflow AI creative — foto produk, VM design | Planned |

### Upgrade yang Direncanakan

| Skill | Improvement |
|-------|-------------|
| `zuma-data-ops` | Integrasi iSeller, template tabel mart, query report otomatis |
| `zuma-sku-context` | Pola assortment lengkap tiap series, kalender launch musiman |
| `zuma-branch` | Profil toko individual, benchmark performa, struktur staffing |
| `zuma-warehouse-and-stocks` | Aturan transfer antar gudang, workflow rekonsiliasi stock count |
| `zuma-company-context` | Org chart, hierarki keputusan, kontak vendor |

---

## Visi ke Depan

```
  SEKARANG (v1.1)                           NANTI
  ===============                           ====

  +----------+                    +----------+----------+----------+
  | general/ |                    | general/ | finance/ |  hrga/   |
  |  1 skill |                    |   2+     |   2+     |   2+     |
  +----------+                    +----------+----------+----------+
  |  ops/    |                    |  ops/    |creative/ |  sales/  |
  |  8 skill |                    |  12+     |   3+     |   3+     |
  +----------+                    +----------+----------+----------+

  8 skills + 2 prompts            20+ skills lintas departemen
  covering ops, planogram,        covering seluruh bisnis
  RO request & brand context      = Otak AI Zuma yang Lengkap
```

Setiap skill baru bikin setiap AI agent makin pinter soal bisnis Zuma.
Setiap upgrade bikin analisis yang ada makin akurat.

**Repo ini adalah single source of truth untuk pengetahuan AI Zuma.**

---

## Kontribusi

Mau nambah atau update skill:

1. Bikin branch: `feat/nama-skill` atau `update/nama-skill`
2. Tambah/edit `SKILL.md` di folder departemen yang sesuai
3. Ikutin format frontmatter:
   ```yaml
   ---
   name: nama-skill-disini
   description: Deskripsi satu baris. Use when [kondisi trigger].
   user-invocable: false
   ---
   ```
4. Update `CHANGELOG.md`
5. Buka PR buat review

---

<p align="center">
  <sub>Dibangun oleh tim AI Zuma Indonesia</sub>
  <br/>
  <sub>Skills yang bikin AI beneran paham bisnis.</sub>
</p>
