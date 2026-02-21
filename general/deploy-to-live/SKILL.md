---
name: deploy-to-live
description: End-to-end local-to-live deployment workflow. Covers git init, commit, push to GitHub (database-zuma org), and deploy to Vercel via CLI. Includes authenticated tokens for both GitHub and Vercel. Use when committing code, pushing to GitHub, deploying to Vercel, or any local-to-production pipeline task.
user-invocable: true
disable-model-invocation: true
allowed-tools: ["Bash", "Read", "Glob", "Grep"]
---

# Deploy to Live — Local → GitHub → Vercel

Generic workflow for shipping any project from local machine to production. Works with any framework (Next.js, Vite, static, etc.). Pre-configured authentication for the **database-zuma** organization.

---

## 1. Authentication Tokens

### GitHub Personal Access Token (PAT)

```
Token: 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
Org: database-zuma
Scope: repo, workflow
```

**Usage in git commands:**
```bash
# Clone with auth
git clone https://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@github.com/database-zuma/{repo-name}.git

# Set remote with auth (existing repo)
git remote set-url origin https://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@github.com/database-zuma/{repo-name}.git

# Push (after setting authenticated remote)
git push -u origin main
```

### Vercel CLI Token

```
Token: WNWvm9fjTerfhyG9zqiSEzdx
Team: database-zumas-projects
```

**Usage in Vercel CLI commands:**
```bash
# Deploy to production
vercel --prod --yes --token=WNWvm9fjTerfhyG9zqiSEzdx

# Add environment variable
echo "value" | vercel env add VAR_NAME production --token=WNWvm9fjTerfhyG9zqiSEzdx

# List projects
vercel ls --token=WNWvm9fjTerfhyG9zqiSEzdx

# Pull project settings
vercel pull --yes --token=WNWvm9fjTerfhyG9zqiSEzdx
```

---

## 2. Full Deployment Workflow

### Phase 1: Pre-Flight Checks

Before deploying, ALWAYS verify:

```bash
# 1. Build locally first — catches errors before they hit Vercel
npm run build   # or: yarn build, pnpm build

# 2. Verify build output shows expected routes/pages
# Next.js App Router:  Look for "Route (app)" section listing all pages
# Next.js Pages Router: Look for "Page" section
# Vite: Look for dist/ output

# 3. Check .gitignore exists and covers:
#    node_modules, .next, .vercel, .env*, dist, build, *.tsbuildinfo

# 4. Verify .env.local has all required variables (they won't be committed)
```

### Phase 2: Git Init & Commit

```bash
# 1. Initialize git (if not already)
git init

# 2. Create .gitignore (if missing) — adapt to your framework
cat > .gitignore << 'EOF'
node_modules/
.next/
.vercel/
.env
.env.local
.env*.local
dist/
build/
*.tsbuildinfo
.turbo/
EOF

# 3. Stage and verify what's being committed
git add -A
git status   # ← ALWAYS check: are all your source files staged?

# 4. Commit
git commit -m "feat: initial commit"
```

**CRITICAL CHECK**: After `git add`, run `git status` and verify:
- All source directories are listed (e.g., `app/`, `lib/`, `components/`, `src/`, `pages/`)
- `node_modules/` is NOT listed
- `.env.local` is NOT listed
- If source files are missing, your `.gitignore` may be too aggressive — check for overly broad patterns

### Phase 3: Push to GitHub

```bash
# 1. Set authenticated remote (replace {repo-name} with actual name)
git remote add origin https://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@github.com/database-zuma/{repo-name}.git

# If remote already exists:
git remote set-url origin https://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@github.com/database-zuma/{repo-name}.git

# 2. Push to main
git push -u origin main

# If rejected (remote has commits local doesn't):
git pull origin main --rebase
git push -u origin main
```

### Phase 4: Deploy to Vercel

```bash
# 1. Deploy to production (auto-detect framework)
vercel --prod --yes --token=WNWvm9fjTerfhyG9zqiSEzdx

# 2. Add environment variables (if the project needs them)
echo "your-value" | vercel env add VAR_NAME production --token=WNWvm9fjTerfhyG9zqiSEzdx

# 3. MUST redeploy after adding env vars (they only take effect on new deployments)
vercel --prod --yes --token=WNWvm9fjTerfhyG9zqiSEzdx
```

### Phase 5: Post-Deploy Verification

```bash
# 1. Check the live URL responds
curl -s -o /dev/null -w "%{http_code}" https://{project-name}.vercel.app

# 2. Check Vercel function logs for runtime errors
vercel logs https://{project-name}.vercel.app --token=WNWvm9fjTerfhyG9zqiSEzdx

# 3. Open in browser and check browser console for client-side errors
# Common: TypeError from data type mismatches (see Troubleshooting section)
```

---

## 3. Environment Variables

### Adding Environment Variables to Vercel

```bash
# Single variable
echo "value" | vercel env add VAR_NAME production --token=WNWvm9fjTerfhyG9zqiSEzdx

# Multiple variables — add each one
echo "val1" | vercel env add VAR_1 production --token=WNWvm9fjTerfhyG9zqiSEzdx
echo "val2" | vercel env add VAR_2 production --token=WNWvm9fjTerfhyG9zqiSEzdx

# IMPORTANT: Redeploy after adding env vars
vercel --prod --yes --token=WNWvm9fjTerfhyG9zqiSEzdx
```

### Listing Environment Variables

```bash
vercel env ls --token=WNWvm9fjTerfhyG9zqiSEzdx
```

### Removing Environment Variables

```bash
vercel env rm VAR_NAME production --yes --token=WNWvm9fjTerfhyG9zqiSEzdx
```

---

## 4. Common Operations

### Create New GitHub Repository

```bash
# Using GitHub CLI (gh) — creates repo and pushes in one step
gh repo create database-zuma/{repo-name} --public --source=. --remote=origin --push

# Or using GitHub API with token
curl -H "Authorization: token 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" \
  https://api.github.com/orgs/database-zuma/repos \
  -d '{"name": "{repo-name}", "private": false}'
```

### Redeploy (After Code Changes)

```bash
# 1. Build locally first
npm run build

# 2. Commit & push changes
git add -A
git status   # ← verify changes look correct
git commit -m "fix: description of change"
git push origin main

# 3. Redeploy on Vercel
vercel --prod --yes --token=WNWvm9fjTerfhyG9zqiSEzdx
```

### View Deployment Logs

```bash
# List recent deployments
vercel ls --token=WNWvm9fjTerfhyG9zqiSEzdx

# Inspect specific deployment
vercel inspect {deployment-url} --token=WNWvm9fjTerfhyG9zqiSEzdx

# View build logs
vercel logs {deployment-url} --token=WNWvm9fjTerfhyG9zqiSEzdx
```

### Rollback Deployment

```bash
vercel promote {deployment-url} --token=WNWvm9fjTerfhyG9zqiSEzdx
```

---

## 5. Troubleshooting

### 5.1 Git: Files Not Committed

**Symptom:** Deployed site is empty or missing pages/routes, even though files exist locally.

**Root cause:** Files were never committed to git. Common when:
- `.gitignore` has overly broad patterns that exclude source files
- `git add .` was run but new directories were created AFTER staging
- Working in `/tmp/` and session state was lost before committing

**Fix:**
```bash
# Check what git actually tracks
git ls-files

# If source files are missing, check .gitignore
cat .gitignore

# Force-add specific files if needed
git add app/ lib/ components/ src/ --force
git status   # verify they appear
git commit -m "fix: add missing source files"
git push origin main
```

**Prevention:** ALWAYS run `git status` after `git add` and BEFORE `git commit` to verify all source directories are staged.

### 5.2 Git: Push Rejected

```bash
git pull origin main --rebase
git push origin main
```

### 5.3 Vercel: Build Fails

```bash
# Check logs
vercel logs {deployment-url} --token=WNWvm9fjTerfhyG9zqiSEzdx
```

**Common causes:**
1. **Missing dependency** → `npm install {pkg}`, commit package.json + lock file, push, redeploy
2. **Env var missing** → `vercel env add ...`, redeploy
3. **TypeScript error** → Fix locally, run `npm run build` to verify, push, redeploy
4. **Node version mismatch** → Add `engines` field to package.json

### 5.4 Vercel: Empty Page (No Content)

**Common causes:**
1. **Source files not committed** — See 5.1 above. Check `git ls-files` for missing files
2. **No page exports** — Next.js App Router needs `app/page.tsx` or `app/{route}/page.tsx`
3. **Missing 'use client'** — Client components without the directive fail silently
4. **Environment variable missing** — API routes return errors, pages render empty
5. **Build output has no routes** — Check build log for `Route (app)` or `Page` section

**Fix:**
```bash
# Build locally and verify routes
npm run build

# Expected output (Next.js App Router):
# Route (app)
# ├ ○ /              ← static pages
# ├ ƒ /api/data      ← dynamic API routes
# └ ○ /dashboard     ← your page routes

# If routes are missing, source files weren't committed (see 5.1)
```

### 5.5 Runtime: TypeError on Data Rendering

**Symptom:** Page loads briefly then crashes with `TypeError: e.toFixed is not a function` or similar.

**Root cause:** PostgreSQL's `pg` driver returns `numeric`, `bigint`, and `decimal` columns as **strings**, not JavaScript numbers. Code calling `.toFixed()`, `.toLocaleString()`, or doing math on these values crashes because strings don't have those methods.

**This affects ANY project using `pg` (node-postgres) with numeric columns.**

**Fix — Always coerce pg values:**
```typescript
// BAD: crashes when pg returns "86988538011.66" as a string
function formatCurrency(n: number): string {
  return `$${n.toFixed(2)}`;  // TypeError: n.toFixed is not a function
}

// GOOD: safe coercion at the top of every formatter
function toNum(v: unknown): number | null {
  if (v == null || v === "") return null;
  const n = Number(v);
  return isNaN(n) ? null : n;
}

function formatCurrency(v: number | string | null): string {
  const n = toNum(v);
  if (n == null) return "-";
  return `$${n.toFixed(2)}`;
}
```

**Also watch for:**
- TanStack Table `getValue()` returns raw pg values → wrap with `Number()` or your coerce helper
- Recharts expects numbers for data points → map with `Number(row.value) || 0`
- Sorting comparisons → `Number(a.revenue) - Number(b.revenue)`, not `a.revenue - b.revenue`

### 5.6 Runtime: Database Connection Timeout on Vercel

**Symptom:** API routes return 500 errors or timeout.

**Common causes:**
1. **VPS firewall blocking Vercel IPs** — Vercel serverless functions run from various IPs. The database server needs to allow connections from Vercel's IP ranges, or from all IPs (less secure)
2. **Connection string wrong** — Check DATABASE_URL in Vercel env vars
3. **Pool exhaustion** — Use a singleton pool pattern, not new Pool() per request
4. **SSL required** — Some hosts require `?sslmode=require` in the connection string

**Fix — Singleton pool pattern (for any Node.js + pg project):**
```typescript
// lib/db.ts — works for any project
import { Pool } from "pg";

const globalForPg = globalThis as unknown as { pool: Pool | undefined };

export const pool =
  globalForPg.pool ??
  new Pool({
    connectionString: process.env.DATABASE_URL,
    max: 10,
    idleTimeoutMillis: 30000,
    connectionTimeoutMillis: 5000,
  });

if (process.env.NODE_ENV !== "production") {
  globalForPg.pool = pool;
}
```

### 5.7 Next.js: useSearchParams() Causes Build Error

**Symptom:** Build fails or warns about `useSearchParams()` needing Suspense boundary.

**Fix:** Wrap the component using `useSearchParams()` in `<Suspense>`:
```tsx
import { Suspense } from "react";

export default function Page() {
  return (
    <Suspense fallback={<div>Loading...</div>}>
      <PageContent />  {/* ← useSearchParams() goes here */}
    </Suspense>
  );
}
```

### 5.8 Authentication Expired

If tokens are expired or revoked, ask the user for new tokens. Current tokens:
- **GitHub PAT**: `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` (org: database-zuma)
- **Vercel Token**: `WNWvm9fjTerfhyG9zqiSEzdx` (team: database-zumas-projects)

---

## 6. One-Shot Deploy (Copy-Paste Ready)

For the fastest deployment from any project directory:

```bash
# === FULL PIPELINE: Local → GitHub → Vercel ===

# 1. Build first (catch errors early)
npm run build

# 2. Git setup
git init
git add -A
git status   # ← VERIFY: all source files listed, no secrets
git commit -m "feat: initial commit"
git remote add origin https://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@github.com/database-zuma/{REPO_NAME}.git
git push -u origin main

# 3. Vercel deploy
vercel --prod --yes --token=WNWvm9fjTerfhyG9zqiSEzdx

# 4. Add env vars (if needed — replace with actual values)
echo "{VALUE}" | vercel env add {VAR_NAME} production --token=WNWvm9fjTerfhyG9zqiSEzdx

# 5. Redeploy with env vars
vercel --prod --yes --token=WNWvm9fjTerfhyG9zqiSEzdx

# 6. Verify
curl -s -o /dev/null -w "%{http_code}" https://{REPO_NAME}.vercel.app
```

---

## 7. Platform Notes

### Windows

- Git Bash paths: `/c/Users/Wayan/...` — CMD paths: `C:\Users\Wayan\...`
- Temp directory: `C:\Users\Wayan\AppData\Local\Temp\` (mapped as `/tmp/` in Git Bash)
- Use `workdir` parameter instead of `cd` when running commands via tools
- CRLF warnings are normal on Windows — safe to ignore

### Framework Auto-Detection

Vercel auto-detects and configures:
- **Next.js** → `next build` (App Router and Pages Router)
- **Vite / React** → `vite build`
- **Nuxt** → `nuxt build`
- **SvelteKit** → `svelte-kit build`
- **Static HTML** → No build step

No manual framework configuration needed.

### Vercel Project Naming

- Vercel project name defaults to **directory name** (not repo name)
- Lives under `database-zumas-projects` team
- Domain pattern: `{project-name}.vercel.app`
- To get a clean name, ensure the local directory has a good name before first deploy

---

## 8. Quick Reference

| Action | Command |
|--------|---------|
| Build locally | `npm run build` |
| Check tracked files | `git ls-files` |
| Push to GitHub | `git push -u origin main` (with authenticated remote) |
| Deploy to Vercel | `vercel --prod --yes --token=WNWvm9fjTerfhyG9zqiSEzdx` |
| Add env var | `echo "val" \| vercel env add NAME production --token=WNWvm9fjTerfhyG9zqiSEzdx` |
| View deployments | `vercel ls --token=WNWvm9fjTerfhyG9zqiSEzdx` |
| View logs | `vercel logs {url} --token=WNWvm9fjTerfhyG9zqiSEzdx` |
| Rollback | `vercel promote {url} --token=WNWvm9fjTerfhyG9zqiSEzdx` |
| Remove env var | `vercel env rm NAME production --yes --token=WNWvm9fjTerfhyG9zqiSEzdx` |

---

## 9. Deployment Checklist

Use this before every deploy:

- [ ] `npm run build` passes locally
- [ ] `git status` shows all source files staged (no missing directories)
- [ ] `.gitignore` excludes: `node_modules`, `.env*`, `.next`, `.vercel`, `dist`
- [ ] `.env.local` has all required variables (for local dev)
- [ ] No secrets in committed files (`git diff --cached` to double-check)
- [ ] Pushed to GitHub (`git push origin main`)
- [ ] Vercel env vars set for production (`vercel env ls`)
- [ ] Deployed (`vercel --prod --yes --token=...`)
- [ ] Live URL responds (HTTP 200)
- [ ] Browser console has no runtime errors
- [ ] Data renders correctly (especially numeric fields from databases)
