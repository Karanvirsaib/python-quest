# Updating Python Quest on GitHub

The repository contains two editions using the same 88-question curriculum:

- **GitHub Pages:** a public static website with independent browser-local profiles and progress. No backend credentials or ChatGPT login are required. Progress does not sync between devices.
- **Sites:** the existing account-backed app. The GitHub Pages workflow does not update the ChatGPT-hosted URL.

## Change a question in your browser

1. Open `app/curriculum.json` in GitHub and select **Edit**.
2. Find the lesson by `id` or `title`.
3. Update its task, explanation, starter, hint, solution, or Python tests. Keep existing IDs stable so saved progress still matches.
4. Commit to `main`.
5. Open **Actions → Publish Python Quest**. The workflow validates every solution, checks TypeScript, builds the site, and deploys GitHub Pages. A failed check prevents publication.

For substantial curriculum changes, open a branch/PR first. The authoring script is an optional generator: it rewrites the data tracks from its definitions. If you edit JSON directly, do not run that generator until you have also reflected your edits there.

## Run locally

```sh
npm ci --ignore-scripts
node node_modules/vite/bin/vite.js --config vite.pages.config.ts
```

Build with:

```sh
node node_modules/vite/bin/vite.js build --config vite.pages.config.ts
```

The default base path is `/python-quest/`. The workflow sets it from the repository name. Set `PAGES_BASE_PATH=/` for a custom domain served at its root. The worker URL uses the same base path.

## Sharing

Publication is initially paused while repository/site visibility is being chosen. To enable it, select **Settings → Pages → Source → GitHub Actions**, then add a repository Actions variable `ENABLE_PAGES` with value `true` under **Settings → Secrets and variables → Actions → Variables**. Run the workflow once. A public repository supports free GitHub Pages; a private repository may require a paid GitHub plan. Once enabled, every successful push to `main` republishes the website.

Send the GitHub Pages website URL to a friend. Each person starts with their own browser-local profile; your account-backed progress and database are not published. The public source includes questions, solutions, and tests; this is a learning platform, not a secure examination system.

## Data and hosting

Only `dist-pages/` is uploaded by the Pages workflow. Local database state, downloaded dependencies, credentials, and `.env` files are ignored. No secrets are needed for the Pages deployment: GitHub provides a short-lived Actions deployment token. The Sites project identifier is routing metadata, not an authentication credential.
