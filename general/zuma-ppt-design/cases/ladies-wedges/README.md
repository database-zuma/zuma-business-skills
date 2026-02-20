# Ladies Wedges Case Study — PPT Design Process

**Project:** Zuma Indonesia — Ladies Wedges Sales Performance 2025 YTD  
**Date:** 2026-02-20  
**Output:** https://ladies-wedges-deck.vercel.app

---

## Design Process & Iterations

### Iteration 1: Initial Attempt (FAILED)
- **Approach:** Reveal.js default template
- **Result:** Too dark, Electric Blue accent (not Zuma brand)
- **Feedback:** "Jelek" — not professional

### Iteration 2: Premium Dark (FAILED)
- **Approach:** Gemini 3.1 Pro Preview, custom CSS
- **Result:** Better quality but still too dark
- **Feedback:** "Better tapi gelap"

### Iteration 3: Bright Version (FAILED)
- **Approach:** Light background, reduced padding
- **Result:** Too loose, visual elements too small
- **Feedback:** "Padding kebesaran, visual kekecilan"

### Iteration 4: Compact (FAILED)
- **Approach:** Reduced padding, larger fonts
- **Result:** Too cramped, "jelek banget"

### Iteration 5: Balanced (FAILED)
- **Approach:** Fresh start, moderate settings
- **Result:** Still not meeting quality bar

### Iteration 6: **FINAL — Canonical Template (SUCCESS)** ✅
- **Approach:** Used `zuma-business-skills/general/zuma-ppt-design/TEMPLATE.html`
- **Key Lesson:** Always start from Canonical Template, never from scratch
- **Result:** Professional, KBI Finance Report style, proper Zuma branding

---

## Key Insights from Data Analysis (Argus)

1. **Bali Premium Dominance:** 65% revenue, highest ASP (Rp 192K)
2. **Tier 3 Volume Driver:** 50%+ volume but dilutes margins
3. **Color Concentration Risk:** Chestnut + Jet Black = 60% sales
4. **Critical Size Imbalance:**
   - Size 38-39: 88-92% sell-through (stockout risk)
   - Size 36: 22% sell-through (dead stock)
5. **Strong MoM Growth:** 24.7% (Jan → Feb 2025)

---

## Workflow Pattern

```
User Request → Iris Delegates → Argus (Data) → Eos (Visual) → Deploy
                    ↓
              Use Canonical Template (MANDATORY)
```

**Critical Success Factor:** Using established Zuma template instead of creating from scratch.

---

## Files

- `output.html` — Final presentation
- `wedges_raw_data.json` — Data from Argus
- `wedges_strategic_report.md` — Insights from Argus
