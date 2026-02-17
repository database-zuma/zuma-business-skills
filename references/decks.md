# Zuma PPT Reference Decks

Katalog deck yang sudah dibuat & teruji. Gunakan sebagai **starting point & benchmark** saat ada request baru untuk role yang sama.

> Skills.md tetap generic. File ini = contoh nyata per role & konteks.

---

## CEO / GM
**Context:** Strategic overview, board meeting, monthly review

### Zuma Portfolio Strategy (BCG + PLC)
- **URL:** https://zuma-product-analysis.vercel.app
- **File:** `~/Desktop/zuma-product-analysis/index.html`
- **Data:** Jan–Feb 2026 vs Jan–Feb 2025 (same-period YoY)
- **Frameworks:** BCG Matrix 2×2 · PLC overlay · Forecast per quadrant
- **Slides:** Cover · BCG visual · Stars deep dive · Q-Marks · Cash Cows · Dogs · PLC · Forecast · Strategy per quadrant · Summary
- **Key data:** 76,208 pairs (-16.7% YoY) · Forecast 569K · BLACKSERIES = Stars
- **When to use:** Product strategy review, assortment decisions, R&D prioritization

### Zuma Performance Analysis (Revenue Bridge + ABC + Growth×Revenue)
- **URL:** https://zuma-performance-analysis.vercel.app
- **File:** `~/Desktop/zuma-performance-analysis/index.html`
- **Data:** Jan–Feb 2026 vs Jan–Feb 2025
- **Frameworks:** SCQA · Revenue Bridge / Waterfall · ABC Store Pareto · Growth×Revenue Matrix · 3-Play Strategy
- **Slides:** Cover · SCQA · Revenue Bridge · ABC Store · Growth×Revenue Matrix · Lombok opportunity · Product×Store connection · ASP strategy · 3-Play · Summary
- **Key data:** Revenue -8.7% (Volume -16.7% offset by ASP +9.8%) · Mataram #1 (+56%) · Dalung ⚠️ (-56%)
- **When to use:** Business performance review, store strategy, quarterly ops review

---

## Dept Ops
**Context:** Store performance, stock optimization, distribution planning

> Belum ada dedicated deck. Use **Zuma Performance Analysis** di atas sebagai proxy — filter per cabang kalau sudah ada branch JOIN fix.

---

## R&D / Product
**Context:** Product development review, series performance, PLC analysis

> Use **Zuma Portfolio Strategy** di atas. R&D version bisa filter ke series tertentu + tambah SKU-level breakdown.

---

## Branch Manager
**Context:** Per-cabang store performance, local ABC analysis

> Belum ada. Needs: portal.store JOIN fix dulu (timeout issue). Template: sama dengan Performance Analysis tapi filtered `WHERE branch = 'Bali'` etc.

---

## Finance
**Context:** P&L, contribution margin, cost analysis

> ❌ Blocked — COGS/gross margin data belum ada di DB. Hold sampai Accurate margin data tersedia.

---

## BusDev
**Context:** Market opportunity, new store feasibility, channel expansion

> ❌ Blocked — needs external market data + competitor landscape. Lombok opportunity insight sudah ada di Performance deck sebagai preview.

---

## RO / Operations Benchmark
**Context:** Replenishment Order performance, distribution efficiency

### RO Benchmark Deck
- **URL:** https://ro-benchmark-vercel.vercel.app
- **File:** `~/Desktop/ro-benchmark-vercel/index.html`
- **Frameworks:** Swiss Style · RO metrics · Benchmark comparison
- **When to use:** RO process review, distribution benchmarking

---

## Notes
- Semua deck: print-ready (`@media print` A4 landscape) — Cmd+P → Background graphics ✅
- Update file ini setiap ada deck baru yang dibuat & approved
- Deck lama yang di-replace → archive URL di sini (jangan delete, buat reference)

---

## Branch Manager — Jawa Timur
**Context:** Monthly branch review, store performance monitoring, planogram audit

### Zuma BM Jatim Review (Jan–Feb 2026)
- **URL:** https://zuma-bm-jatim.vercel.app
- **File:** `~/Desktop/zuma-bm-jatim/index.html`
- **Data:** Jan–Feb 2026 (Feb YTD s/d 17 Feb)
- **Frameworks:** Branch Scorecard · Achievement vs Target · ABC Store · Growth×Revenue Matrix · FF/FA/FS Planogram Health · Product Mix BCG overlay · MoM Trend · Benchmark Nasional · 3 Action Items
- **Slides:** Cover · Scorecard · Actual vs Target (per store) · ABC+Matrix · Planogram Health · Product Mix · Trend+Benchmark · Action Items
- **Key data:** 11 stores · Jan achievement 87% · Avg FF 66% · PTC FF kritis 52.9% · Galaxy Mall concern 64% · BLACKSERIES under-penetrated
- **Data sources:** core.sales_with_product + portal.store_monthly_target (JOIN via store_name_norm) + mart.ff_fa_fs_daily
- **Template for other branches:** Copy this deck → filter branch name → update data → redeploy
- **When to use:** Monthly BM review, ops meeting, performance escalation
