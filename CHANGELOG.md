# Changelog

All notable changes to this skill library will be documented here.

---

## [1.0.0] — 9 Feb 2026

### Initial Release

**5 skills across 2 departments:**

#### General (Cross-Department)
- **zuma-company-context** — Brand identity (witty/casual/confident tone), 4 business entities (DDD, MBB, UBB, LJBB), data source mapping (Accurate, iSeller, Ginee, Supabase)
- **brand-guidelines.md** — Visual identity reference: Zuma Teal `#002A3A`, Zuma Green `#00E273`, Japandi aesthetic, GT Walsheim typography

#### Operations
- **zuma-sku-context** — Product hierarchy (Type > Gender > Series > Article > Size), Kode Mix versioning system (V0-V4 unification), assortment patterns (12 pairs/box), 6-tier classification
- **zuma-branch** — 6 branches (Jatim, Jakarta, Sumatra, Sulawesi, Batam, Bali), store categories (RETAIL/NON-RETAIL/EVENT), Area Supervisors, store stock management, replenishment process
- **zuma-warehouse-and-stocks** — 3 physical warehouses (WHS/WHJ/WHB), stock formula & stages, full RO workflow (QUEUE > APPROVED > PICKING > ... > COMPLETED), variance tracking
- **zuma-data-ops** — PostgreSQL VPS connection (76.13.194.120:5432), 5 schemas (raw/portal/core/mart/public), complete table/view documentation, 6 critical SQL rules, 9 query templates, analysis methodology, ETL schedule (02:00 backup, 03:00 stock, 05:00 sales)
