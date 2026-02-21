# FF/FA/FS SQL Query Templates

> Reference file for SKILL: FF / FA / FS — Store Fill Rate Metrics  
> Contains: SQL query templates (Section 13)

---

## 13. SQL Query Templates

### 13.1 Latest Metrics for All Stores

```sql
-- Latest FF/FA/FS for all Jatim stores
SELECT 
    report_date,
    store_label,
    ROUND(ff * 100, 1) AS ff_pct,
    ROUND(fa * 100, 1) AS fa_pct,
    ROUND(fs * 100, 1) AS fs_pct
FROM mart.ff_fa_fs_daily
WHERE branch = 'Jatim'
  AND report_date = (SELECT MAX(report_date) FROM mart.ff_fa_fs_daily)
ORDER BY ff DESC;
```

### 13.2 Trend Over Time (Last 30 Days)

```sql
-- FF trend for one store over last 30 days
SELECT 
    report_date,
    ROUND(ff * 100, 1) AS ff_pct,
    ROUND(fa * 100, 1) AS fa_pct,
    ROUND(fs * 100, 1) AS fs_pct
FROM mart.ff_fa_fs_daily
WHERE store_label = 'Zuma Royal Plaza'
  AND report_date >= CURRENT_DATE - INTERVAL '30 days'
ORDER BY report_date;
```

### 13.3 Stores Below Target

```sql
-- Stores with FF < 70% (need urgent restock)
SELECT 
    store_label,
    ROUND(ff * 100, 1) AS ff_pct,
    ROUND(fa * 100, 1) AS fa_pct,
    ROUND(fs * 100, 1) AS fs_pct
FROM mart.ff_fa_fs_daily
WHERE report_date = (SELECT MAX(report_date) FROM mart.ff_fa_fs_daily)
  AND ff < 0.70
ORDER BY ff;
```

### 13.4 Branch-Level Summary

```sql
-- Average metrics per branch
SELECT 
    branch,
    COUNT(DISTINCT store_label) AS num_stores,
    ROUND(AVG(ff) * 100, 1) AS avg_ff,
    ROUND(AVG(fa) * 100, 1) AS avg_fa,
    ROUND(AVG(fs) * 100, 1) AS avg_fs
FROM mart.ff_fa_fs_daily
WHERE report_date = (SELECT MAX(report_date) FROM mart.ff_fa_fs_daily)
GROUP BY branch
ORDER BY avg_ff DESC;
```

### 13.5 Check Store Mappings

```sql
-- View all store mappings
SELECT 
    planogram_name,
    stock_nama_gudang,
    branch,
    match_method,
    updated_at
FROM portal.store_name_map
ORDER BY branch, planogram_name;
```

### 13.6 Check Unmapped Stores

```sql
-- Find planogram stores not in mapping table
SELECT DISTINCT store_name
FROM portal.temp_portal_plannogram
WHERE store_name NOT IN (SELECT planogram_name FROM portal.store_name_map)
ORDER BY store_name;
```
