<p align="center">
  <img src="https://img.shields.io/badge/ZUMA-Business_Skills-00E273?style=for-the-badge&labelColor=002A3A" alt="Zuma Business Skills"/>
  <br/>
  <img src="https://img.shields.io/badge/Claude_Code-Skills_Library-7C3AED?style=flat-square" alt="Claude Code"/>
  <img src="https://img.shields.io/badge/Status-Active-00E273?style=flat-square" alt="Active"/>
  <img src="https://img.shields.io/badge/Skills-24_Installed-FF6B35?style=flat-square" alt="24 Skills"/>
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
|   |-- zuma-company-context/
|   |   |-- SKILL.md                        Brand identity, 4 entitas, data sources
|   |   +-- brand-guidelines.md             Warna, tipografi, estetika Japandi
|   |-- zuma-business-metrics/
|   |   +-- SKILL.md                        Business metrics framework
|   |-- data-storytelling-skill/
|   |   +-- SKILL.md                        Data storytelling & narrative
|   |-- deploy-to-live/
|   |   +-- SKILL.md                        Deployment & live infrastructure
|   |-- zuma-image-gen-skill/
|   |   +-- SKILL.md                        AI image generation workflow
|   +-- zuma-ppt-design/
|       |-- SKILL.md                        PowerPoint design templates
|       +-- TEMPLATE.html                   Design template file
|
|-- ops/                                  DEPARTEMEN OPERASIONAL
|   |-- zuma-sku-context/
|   |   +-- SKILL.md                        Hierarki produk, Kode Mix, tier, assortment
|   |-- zuma-branch/
|   |   +-- SKILL.md                        6 cabang, jaringan toko, operasional retail
|   |-- zuma-warehouse-and-stocks/
|   |   +-- SKILL.md                        3 gudang, tahapan stok, sistem RO
|   |-- zuma-data-analyst-skill/
|   |   |-- SKILL.md                        Data analyst workflow & SQL patterns
|   |   |-- data-analyst-etl-cron.md        ETL cron schedule & process
|   |   |-- data-analyst-schema-reference.md  Database schema reference
|   |   +-- data-analyst-sql-templates.md   SQL templates & queries
|   |-- zuma-database-assistant-skill/
|   |   |-- SKILL.md                        Database assistant & queries
|   |   |-- database-column-reference.md    Column mappings & reference
|   |   +-- database-troubleshooting.md     Troubleshooting guide
|   |-- notion-metrics/
|   |   |-- SKILL.md                        FF/FA/FS fill rate metrics
|   |   |-- ff-fa-fs-calculation-logic.md   Calculation methodology
|   |   |-- ff-fa-fs-history.md             Historical tracking
|   |   |-- ff-fa-fs-pipeline-details.md    Pipeline details
|   |   +-- ff-fa-fs-sql-templates.md       SQL calculation templates
|   |-- zuma-inventory-control/
|   |   +-- zuma-ff-skills/
|   |       |-- SKILL.md                    FF skill (inventory fill factor)
|   |       |-- ff-fa-fs-calculation-logic.md  Calculation logic
|   |       |-- ff-fa-fs-history.md         Historical data
|   |       |-- ff-fa-fs-pipeline-details.md  Pipeline & processing
|   |       +-- ff-fa-fs-sql-templates.md   SQL templates
|   |   +-- stock-opname-level-2/
|   |       +-- SKILL.md                    Stock opname level 2 skill
|   |-- zuma-plano-ro-skills/
|   |   |-- PLANOGRAM_Royal_Plaza.xlsx      Royal Plaza planogram data
|   |   |-- PROMPT_new_planogram.md         Prompt: generate new planogram
|   |   |-- PROMPT_ro_request.md            Prompt: generate RO Request
|   |   |-- step0.5-pre-planogram/
|   |   |   |-- SKILL.md                    Pre-planogram data generation
|   |   |   |-- pre-planogram-algorithm.md  Algorithm & logic
|   |   |   +-- pre-planogram-output-spec.md  Output specification
|   |   |-- step1-planogram/
|   |   |   |-- SKILL.md                    Planogram generation (v3.2)
|   |   |   |-- planogram-algorithm.md      Algorithm & layout rules
|   |   |   |-- planogram-display-rules.md  Display & rendering rules
|   |   |   |-- planogram-examples.md       Example planograms
|   |   |   |-- planogram-output-spec.md    Output format specification
|   |   |   +-- _archive/                   Legacy planogram versions
|   |-- step2-visualizations/
|   |   |   |-- SKILL.md                    Planogram visualization
|   |   |   |-- visualization-examples.md   Visual examples
|   |   |   |-- visualization-rendering-details.md  Rendering details
|   |   |   |-- VISUAL_PLANOGRAM_Royal_Plaza.txt  Visual output
|   |   |   +-- VISUAL_PLANOGRAM_Royal_Plaza.xlsx  Visual spreadsheet
|   |-- step3-zuma-ro-surplus-skills/
|   |       |-- SKILL.md                    RO request & surplus distribution
|   |       +-- ro-surplus-output-format.md  Output format specification
|   |-- dn-to-po/
|   |   +-- SKILL.md                        DN to PO conversion workflow
|   |-- zuma-token-usage-report/
|       +-- SKILL.md                        Token usage & API metrics reporting
|
|-- finance/                              DEPARTEMEN FINANCE
|   |-- coretax-faktur-generator/
|   |   |-- SKILL.md                    Coretax Faktur Generator (tax doc)
|   |   +-- coretax_faktur.py            Python script for Coretax XLSX
|   +-- fp-rekon-stock/
|       |-- SKILL.md                    Financial reconciliation & stock
|       +-- fp_rekon.py                 Python script for reconciliation
|-- _archive/
|
|-- _archive/                             DEPRECATED SKILLS (archived)
|   +-- (legacy skill versions)
|
|-- BRAND.md                              Brand guidelines & standards
|-- README.md                             File ini
+-- CHANGELOG.md                          Riwayat perubahan
```

> **Pipeline Flow:**
> ```
> Pre-Planogram (0.5) → Step 1: Planogram → Step 2: Visual Planogram → Step 3: RO Request
>                                                                          ↓
>                                                              notion-metrics: FF/FA/FS Report
> ```
> Setiap step punya skill `.md` + script `.py` sendiri. Prompt template tersedia untuk generate planogram baru maupun RO Request mingguan. Output Pre-Planogram juga jadi input untuk kalkulasi FF/FA/FS metric.

### Kenapa Dipisah per Folder?

| Folder | Fungsi | Siapa yang Pakai |
|--------|--------|------------------|
| `general/` | Pengetahuan lintas departemen — brand, struktur entitas | Semua orang |
| `ops/` | Pengetahuan operasional — produk, toko, gudang, data analytics | Tim ops, data analyst, AI agent |
| `finance/` | Pengetahuan keuangan — P&L, margin, COGS, pajak | Tim finance |
| `hrga/` | Pengetahuan HR & GA — struktur organisasi, kebijakan | Tim HR (planned) |

Folder departemen baru akan ditambahkan seiring ekspansi automasi AI Zuma.

---

## Daftar Skill (24 Skills)

### General (Lintas Departemen) — 6 Skills

| # | Skill | File | Apa yang Diketahui |
|---|-------|------|-------------------|
| 1 | **zuma-company-context** | SKILL.md + brand-guidelines.md | Brand tone (witty/casual/confident), visual identity (Japandi, Zuma Teal `#002A3A`, Zuma Green `#00E273`), 4 entitas bisnis (DDD, MBB, UBB, LJBB), sumber data |
| 2 | **zuma-business-metrics** | SKILL.md | Business metrics framework & KPI definition |
| 3 | **data-storytelling-skill** | SKILL.md | Data storytelling & narrative synthesis techniques |
| 4 | **deploy-to-live** | SKILL.md | Production deployment & live infrastructure workflows |
| 5 | **zuma-image-gen-skill** | SKILL.md | AI image generation & visual asset creation |
| 6 | **zuma-ppt-design** | SKILL.md + TEMPLATE.html | PowerPoint design templates & styling guidelines |

### Operations — 16 Skills

#### Core Context Skills (4)

| # | Skill | File | Apa yang Diketahui |
|---|-------|------|-------------------|
| 7 | **zuma-sku-context** | SKILL.md | Hierarki produk (Type > Gender > Series > Article > Size), Kode Mix versioning, assortment (12 pasang/box), 6 tier |
| 8 | **zuma-branch** | SKILL.md | 6 cabang (Jatim, Jakarta, Sumatra, Sulawesi, Batam, Bali), kategori toko, layout, Area Supervisor |
| 9 | **zuma-warehouse-and-stocks** | SKILL.md | 3 gudang (WHS/WHJ/WHB), formula stok, alur RO, variance tracking |
| 10 | **zuma-token-usage-report** | SKILL.md | Token usage metrics & API consumption reporting |

#### Data & Analytics Skills (3)

| # | Skill | File | Apa yang Diketahui |
|---|-------|------|-------------------|
| 11 | **zuma-data-analyst-skill** | SKILL.md + data-analyst-etl-cron.md + data-analyst-schema-reference.md + data-analyst-sql-templates.md | ETL pipeline, PostgreSQL schema, SQL patterns, analysis methodology |
| 12 | **zuma-database-assistant-skill** | SKILL.md + database-column-reference.md + database-troubleshooting.md | Database queries, column mappings, troubleshooting guide |
| 13 | **notion-metrics** | SKILL.md + ff-fa-fs-calculation-logic.md + ff-fa-fs-history.md + ff-fa-fs-pipeline-details.md + ff-fa-fs-sql-templates.md | FF/FA/FS fill rate metrics, calculation logic, SQL templates, store mapping |

#### Inventory Control Skills (2)

| # | Skill | File | Apa yang Diketahui |
|---|-------|------|-------------------|
| 14 | **zuma-ff-skills** (under inventory-control/) | SKILL.md + ff-fa-fs-calculation-logic.md + ff-fa-fs-history.md + ff-fa-fs-pipeline-details.md + ff-fa-fs-sql-templates.md | Fill Factor calculation, methodology, SQL templates |
| 15 | **stock-opname-level-2** (under inventory-control/) | SKILL.md | Stock opname procedures & level 2 reconciliation |

#### Planogram & RO Pipeline Skills (4)

| # | Skill | File | Apa yang Diketahui |
|---|-------|------|-------------------|
| 16 | **step0.5-pre-planogram** | SKILL.md + pre-planogram-algorithm.md + pre-planogram-output-spec.md | Pre-planogram data generation, sales+stock analysis, 7-step pipeline |
| 17 | **step1-planogram** | SKILL.md + planogram-algorithm.md + planogram-display-rules.md + planogram-examples.md + planogram-output-spec.md | Planogram generation (v3.2), tier assignment, capacity allocation, assortment rules |
| 18 | **step2-visualizations** | SKILL.md + visualization-examples.md + visualization-rendering-details.md | Planogram visualization, heatmaps, stock comparison, color coding |
| 19 | **step3-zuma-ro-surplus-skills** | SKILL.md + ro-surplus-output-format.md | RO request & surplus distribution, restock rules, WH sourcing |

#### Operational Workflow Skills (3)

| # | Skill | File | Apa yang Diketahui |
|---|-------|------|-------------------|
| 20 | **dn-to-po** | SKILL.md | DN to PO conversion workflow & document processing |
| 21 | **fp-rekon-stock** | SKILL.md + fp_rekon.py | Financial reconciliation & stock matching |
| 22 | **coretax-faktur-generator** | SKILL.md + coretax_faktur.py | Generate Coretax DJP-ready Faktur + DetailFaktur XLSX dari Register Penjualan bulanan, DPP Nilai Lain tax math, multi-entity support (DDD/MBB/UBB) |
|
### Finance — 2 Skills

| # | Skill | File | Apa yang Diketahui |
|---|-------|------|-------------------|
**Planogram Prompts:**
- `PROMPT_new_planogram.md` — Template untuk generate planogram baru (single store)
- `PROMPT_ro_request.md` — Template untuk generate RO Request mingguan (single/multi-store)

**Data Files:**
- `PLANOGRAM_Royal_Plaza.xlsx` — Sample planogram data (Royal Plaza store)

**Deprecated:**
- `_archive/` folder berisi legacy planogram versions & old formats

---

## Instalasi

### Prasyarat

- [Claude Code CLI](https://docs.anthropic.com/en/docs/claude-code) sudah ter-install
- Akses Git ke repo private ini
- **Python 3.8+** dengan library berikut (untuk generate planogram & RO Request):

```bash
pip install psycopg2-binary openpyxl pandas python-dotenv
```

| Library | Versi Tested | Fungsi |
|---------|-------------|--------|
| `pandas` | 2.0+ | Data manipulation & SQL query results — dipakai di pre-planogram dan FF/FA/FS metric calculator |
| `python-dotenv` | 1.0+ | Load environment variables dari .env file |
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

  10 skills + 2 prompts            20+ skills lintas departemen
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
