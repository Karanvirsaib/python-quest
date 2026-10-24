# Python Quest

An independent personal learning platform with 4 Python courses and 24 original interactive lessons. Includes ChatGPT sign-in, account-scoped D1 progress and notes, Python execution in a module web worker with Pyodide, exercise checks, searchable practice, a sandbox, XP, badges, and daily goals.

## Local development

Requires Node 22.13+ and npm. Install dependencies with `npm run install:ci`, then run `npm run dev`. The starter's local sign-in uses a development account; production identity is managed by Sites. No password database is maintained by this app.

The local database must be migrated before saving progress. After `npm run build`, run:

```powershell
node --import ./scripts/sites-env.mjs ./node_modules/wrangler/bin/wrangler.js d1 execute DB --local --config dist/server/wrangler.json --persist-to .wrangler/state --file drizzle/0000_complete_bug.sql
```

Run each migration once on a fresh local database. Hosted migrations are applied by Sites during deployment. Local test records are not published.

## Content and checks

Edit `app/curriculum.json` to maintain lessons. Each lesson includes original teaching text, starter code, a hint, a solution, and Python assertion checks. `python scripts/check-curriculum.py` verifies all 24 solutions. `node node_modules/typescript/bin/tsc --noEmit` checks types. `npm run build` creates the Worker and browser bundles.

The Python runtime is pinned to Pyodide 314.0.7 and loaded from jsDelivr. First use requires an internet connection and may download a sizable runtime. Each lesson has a fresh worker and each run has a fresh namespace; standard-library module state can persist within the same lesson worker. Programs have a 10-second execution limit after initialization and a Stop control. This is a personal learning runner, not a grading service for untrusted submissions. Completion checks execute in the browser and are not an anti-cheating boundary.

The sandbox draft stays on the current device. Course code and notes sync when Save draft is pressed; successful checks save completion automatically. Exit prompts warn about unsaved course changes. XP is derived from unique completed lessons, and completion timestamps remain stable on review.

## Scope

The four courses cover Python foundations, decisions and loops, collections, and functions/problem solving. This release does not include other programming languages, AI tutoring, payments, or classroom administration. It does not use Codédex content, assets, branding, source code, or REA. Public interaction patterns were sufficient to build the independent experience.
