# FF/FA/FS Calculation Logic

> Reference file for SKILL: FF / FA / FS — Store Fill Rate Metrics  
> Contains: Auto-sync store map algorithm (Section 4), Size column mapping (Section 5), Full calculation code (Section 6)

---

## 4. Auto-Sync Store Map Algorithm

The `sync_store_map()` function runs **before every calculation** to ensure new planogram stores are automatically mapped to VPS stock locations.

### Algorithm Flow

```python
def sync_store_map(conn):
    """
    Auto-match planogram stores to VPS stock nama_gudang.
    Preserves existing mappings (manual or auto).
    """
    # 1. Get existing mappings from portal.store_name_map
    existing = {row['planogram_name']: row for row in fetch_existing_mappings(conn)}
    
    # 2. Get DISTINCT store_name from planogram table
    planogram_stores = fetch_planogram_stores(conn)
    
    # 3. Get DISTINCT nama_gudang from stock table
    stock_stores = fetch_stock_stores(conn)
    
    # 4. For each NEW planogram store (not already in map):
    for plano_store in planogram_stores:
        if plano_store in existing:
            continue  # Skip — already mapped
        
        # Pass 1: Exact match (case-insensitive)
        for stock_store in stock_stores:
            if plano_store.lower().strip() == stock_store.lower().strip():
                insert_mapping(conn, plano_store, stock_store, 'auto_exact')
                break
        
        # Pass 2: Substring match (one name contains the other, SINGLE candidate only)
        candidates = [s for s in stock_stores 
                      if plano_store.lower() in s.lower() or s.lower() in plano_store.lower()]
        if len(candidates) == 1:
            insert_mapping(conn, plano_store, candidates[0], 'auto_fuzzy')
            continue
        
        # Pass 3: Word overlap >= 75% (SINGLE candidate only, excludes 'zuma')
        candidates = []
        plano_words = set(plano_store.lower().split()) - {'zuma'}
        for stock_store in stock_stores:
            stock_words = set(stock_store.lower().split()) - {'zuma'}
            overlap = len(plano_words & stock_words) / len(plano_words | stock_words)
            if overlap >= 0.75:
                candidates.append(stock_store)
        
        if len(candidates) == 1:
            insert_mapping(conn, plano_store, candidates[0], 'auto_fuzzy')
            continue
        
        # No match → logged as unmapped in status JSON for Atlas to flag
        log_unmapped(plano_store)
    
    # 5. Branch lookup from portal.store
    for mapping in new_mappings:
        branch = lookup_branch(conn, mapping['stock_nama_gudang'])
        update_branch(conn, mapping['planogram_name'], branch)
```

### Matching Results (Feb 14, 2026)

**8 auto_exact matches:**
- Zuma Matos → Zuma Malang Town Square
- Zuma Galaxy Mall → ZUMA GALAXY MALL
- ZUMA PTC → Zuma PTC
- Zuma Lippo Sidoarjo → Zuma Lippo Plaza Sidoarjo
- Zuma Lippo Batu → Zuma Lippo Plaza Batu
- Zuma Royal Plaza → Zuma Royal Plaza
- Zuma City Of Tomorrow Mall → Zuma City of Tomorrow
- Zuma Mall Olympic Garden → Zuma MOG

**3 auto_fuzzy matches:**
- Zuma Icon Gresik → Zuma Icon Mall Gresik (substring match)
- Zuma Tunjungan Plaza → Zuma Tunjungan Plaza 3 (substring match)
- Zuma Sunrise Mall → Zuma Sunrise Mall Mojokerto (word overlap 75%+)

**0 unmapped stores** — all 11 Jatim stores successfully auto-matched.

### Manual Override

To manually override an auto-matched store:

```sql
-- Update existing mapping
UPDATE portal.store_name_map
SET stock_nama_gudang = 'Correct VPS Name',
    match_method = 'manual',
    updated_at = NOW()
WHERE planogram_name = 'Planogram Store Name';

-- Or insert new manual mapping
INSERT INTO portal.store_name_map (planogram_name, stock_nama_gudang, branch, match_method)
VALUES ('Planogram Store Name', 'VPS Stock Name', 'Jatim', 'manual')
ON CONFLICT (planogram_name) DO UPDATE
SET stock_nama_gudang = EXCLUDED.stock_nama_gudang,
    match_method = 'manual',
    updated_at = NOW();
```

Manual mappings are **never overwritten** by the auto-sync algorithm.

---

## 5. Size Column Mapping (Dynamic)

The script **dynamically detects** size columns from the planogram table. No hardcoded mapping.

### Detection Algorithm

```python
def build_size_map(planogram_columns):
    """
    Dynamically build size mapping from planogram column names.
    
    Column 'size_X_Y' → stock sizes ['X', 'Y'] (paired)
    Column 'size_X' → stock size ['X'] (individual)
    """
    size_map = {}
    
    for col in planogram_columns:
        if not col.startswith('size_'):
            continue
        
        size_part = col.replace('size_', '')
        
        if '_' in size_part:
            # Paired: size_39_40 → ['39', '40']
            sizes = size_part.split('_')
            size_map[col] = sizes
        else:
            # Individual: size_39 → ['39']
            size_map[col] = [size_part]
    
    return size_map
```

### Example Mappings

**Kids sizes (paired):**
- `size_18_19` → `['18', '19']`
- `size_20_21` → `['20', '21']`
- `size_22_23` → `['22', '23']`
- `size_24_25` → `['24', '25']`

**Adult sizes (individual):**
- `size_26` → `['26']`
- `size_27` → `['27']`
- ...
- `size_44` → `['44']`

**Adult sizes (paired, for AIRMOVE series):**
- `size_39_40` → `['39', '40']`
- `size_41_42` → `['41', '42']`
- `size_43_44` → `['43', '44']`

**How paired sizes work in FF calculation:**

For a paired column like `size_18_19` with `plan_qty = 2`:
- Check VPS stock for size "18" AND size "19" separately
- Sum their quantities: `stock_qty = stock_18 + stock_19`
- FF logic: if `plan_qty > 0 AND stock_qty > 0` → count as 1 filled size slot
- This means if size 18 has 0 but size 19 has 3, the slot counts as filled (stock_qty = 3 > 0)

---

## 6. Calculation Logic

### 6.1 High-Level Flow

```python
def main():
    conn = connect_to_db()
    
    # 1. Auto-sync store mappings
    sync_store_map(conn)
    
    # 2. Load planogram from portal.temp_portal_plannogram
    planogram = load_planogram(conn)
    
    # 3. Build dynamic size map from planogram columns
    size_map = build_size_map(planogram.columns)
    
    # 4. Load stock from core.stock_with_product (today's snapshot)
    stock = load_stock(conn, snapshot_date=today())
    
    # 5. Calculate FF/FA/FS per store
    for store in planogram['store_name'].unique():
        metrics = calculate_store_metrics(planogram, stock, store, size_map)
        
        # 6. Upsert into mart.ff_fa_fs_daily
        upsert_metrics(conn, store, metrics)
    
    # 7. Write status JSON
    write_status_json(metrics_summary)
```

### 6.2 Metric Formulas (Unchanged from v1.0)

#### FF (Fill Factor) — Size-Level

```python
def calculate_ff(planogram, stock, store, size_map):
    """
    FF = Count(Plan>0 AND Stock>0) / Count(Plan>0)
    
    Numerator:  How many size-column slots have BOTH plan > 0 AND stock > 0
    Denominator: How many size-column slots have plan > 0
    """
    count_plan_pos = 0
    count_stock_pos = 0
    
    for article_row in planogram[planogram['store_name'] == store]:
        article_mix = article_row['article_mix']
        
        for size_col, stock_sizes in size_map.items():
            plan_qty = int(article_row.get(size_col, 0) or 0)
            
            if plan_qty > 0:
                count_plan_pos += 1
                
                # Sum stock across all sizes in this column
                stock_qty = sum(
                    get_stock(stock, store, article_mix, size)
                    for size in stock_sizes
                )
                
                if stock_qty > 0:
                    count_stock_pos += 1
    
    return count_stock_pos / count_plan_pos if count_plan_pos > 0 else 0.0
```

#### FA (Fill Article) — Article-Level

```python
def calculate_fa(planogram, stock, store, size_map):
    """
    FA = Count(Articles_with_any_stock) / Count(Articles_in_plan)
    
    Numerator:  How many articles have Total_Stock > 0
    Denominator: How many articles have Total_Plan > 0
    """
    count_article_plan = 0
    count_article_stock = 0
    
    for article_row in planogram[planogram['store_name'] == store]:
        article_mix = article_row['article_mix']
        
        total_plan = sum(int(article_row.get(col, 0) or 0) for col in size_map.keys())
        
        if total_plan > 0:
            count_article_plan += 1
            
            total_stock = sum(
                get_stock(stock, store, article_mix, size)
                for sizes in size_map.values()
                for size in sizes
            )
            
            if total_stock > 0:
                count_article_stock += 1
    
    return count_article_stock / count_article_plan if count_article_plan > 0 else 0.0
```

#### FS (Fill Stock) — Quantity Depth

```python
def calculate_fs(planogram, stock, store, size_map):
    """
    FS = Sum(Total_Stock) / Sum(Total_Plan)
    
    Can exceed 1.0 — this means overstocked (more stock than plan).
    FS > 1.0 is a signal for potential surplus return to warehouse.
    """
    total_plan = 0
    total_stock = 0
    
    for article_row in planogram[planogram['store_name'] == store]:
        article_mix = article_row['article_mix']
        
        for size_col, stock_sizes in size_map.items():
            plan_qty = int(article_row.get(size_col, 0) or 0)
            total_plan += plan_qty
            
            stock_qty = sum(
                get_stock(stock, store, article_mix, size)
                for size in stock_sizes
            )
            total_stock += stock_qty
    
    return total_stock / total_plan if total_plan > 0 else 0.0
```

### 6.3 Performance Optimization

The production script uses **raw psycopg2** (not pandas) for performance:
- O(1) dict lookups instead of DataFrame filtering
- Pre-builds stock lookup dict: `{(store, article_mix, size): quantity}`
- Processes 11 stores × 235 articles × 28 sizes in ~4.5 seconds

**Script reference:** `/opt/openclaw/scripts/calculate_ff_fa_fs.py` (599 lines, not included in this doc)
