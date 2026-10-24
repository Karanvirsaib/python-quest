# Updating Python Quest on GitHub

## Current setup

- Live website: https://python-quest-karan.itsmejd2013.chatgpt.site/ — anyone with the link can open it.
- Source repository: https://github.com/Karanvirsaib/python-quest — private.
- GitHub validates changes automatically. It does **not** automatically redeploy the live Sites URL. After committing, ask Codex to deploy the latest private-repository changes to the existing Python Quest site.
- GitHub Pages is not enabled: the current GitHub plan rejected Pages hosting from this private repository. Keep the repository private; making the existing Sites website public does not expose this repository.

The repository contains two editions using the same 88-question curriculum:

- **GitHub Pages (prepared, not published):** a static website with independent browser-local profiles and progress. No backend credentials or ChatGPT login are required. Progress does not sync between devices.
- **Sites:** the existing account-backed app. The GitHub Pages workflow does not update the ChatGPT-hosted URL.

## Change a question in your browser

1. Open `app/curriculum.json` in GitHub and select **Edit**.
2. Find the lesson by `id` or `title`.
3. Update its task, explanation, starter, hint, solution, or Python tests. Keep existing IDs stable so saved progress still matches.
4. Commit to `main`.
5. Open **Actions → Check Python Quest**. The workflow validates every solution, checks TypeScript, and builds the standalone edition. Once checks pass, ask Codex to deploy your changes to the existing live Sites URL. A GitHub commit alone does not change the live site.

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

The optional GitHub Pages deployment is disabled because the current plan does not support this private repository. To enable it, select **Settings → Pages → Source → GitHub Actions**, then add a repository Actions variable `ENABLE_PAGES` with value `true` under **Settings → Secrets and variables → Actions → Variables**. Run the workflow once. A public repository supports free GitHub Pages; a private repository may require a paid GitHub plan. Once enabled, every successful push to `main` republishes the website.

Send the live Sites URL above to a friend. They can explore without signing in and sign in to save account progress. If the optional static Pages edition is later published, send its separate URL instead. Each person starts with their own browser-local profile; your account-backed progress and database are not published. The public source includes questions, solutions, and tests; this is a learning platform, not a secure examination system.

## Data and hosting

Only `dist-pages/` is uploaded by the Pages workflow. Local database state, downloaded dependencies, credentials, and `.env` files are ignored. No secrets are needed for the Pages deployment: GitHub provides a short-lived Actions deployment token. The Sites project identifier is routing metadata, not an authentication credential.
