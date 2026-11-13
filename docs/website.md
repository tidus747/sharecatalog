# Build and publish the documentation

The static documentation site lives in `website/`. It uses Astro and adapts
Terminal Noir's Noir/Paper palette, typography, styling and section component.
The original theme's MIT notice is preserved in `licenses/Terminal-Noir-MIT.txt`.
Application guides are Markdown files in `docs/`, rendered directly through an
Astro content collection. Do not maintain separate copies of the same guide.

## Local setup

Use Node.js 22.22.0 or newer; `website/.nvmrc` records the tested version.
From a checkout:

```powershell
cd website
npm ci
npm run dev
```

Open the local URL printed by Astro, including `/sharecatalog/` when using the
default base. The Python application does not need Node.js to run.

## Verification

```powershell
npm run format:check
npm run check
npm run build
npm test
npx playwright install chromium
npm run test:e2e
```

The built-link tests validate local links, images, headings and route prefixes.
Browser tests check desktop/mobile layout, Noir/Paper persistence, code copy and
automated accessibility. Python tests and Ruff remain separate at the repository root.

## Add or update a guide

Edit a Markdown file in `docs/`. To add a new page, also add its filename slug and
navigation title to `website/src/lib/site.ts`. Keep examples fictional, descriptions
accurate and link-verification limits explicit. Use English and avoid Unicode U+2014.
Do not add real projects, internal URLs or screenshots of organizational data.

The app screenshot is generated from fictional in-memory data with
`python scripts/capture_demo.py`. It does not scan or open a source document.

## GitHub Pages

`.github/workflows/pages.yml` checks and builds the site on relevant pull requests.
Pushes to `main` and manual workflow dispatches also deploy the checked static output.
The default public address is `https://tidus747.github.io/sharecatalog/`.

On the repository's **Settings > Pages**, choose **GitHub Actions** as the build
source. The Pages workflow uses read-only repository content access and grants
Pages/OIDC write permission only to the deployment job. Official actions are pinned
to commit hashes. No GitHub token belongs in site code or environment files.

For another repository or domain, update `site` and `base` in
`website/astro.config.mjs`, or provide `SITE_URL` and `SITE_BASE` during the build.
Check both route links and sitemap URLs after changing the prefix.

## Theme provenance

Upstream: [Terminal Noir](https://github.com/nandomoreirame/terminalnoir-astro-theme),
commit `f702aa1a2175f3e8ac4447e1d008c286728a1d0e`, copyright 2026 Fernando Moreira.
ShareCatalog adapts the presentation for English application documentation, removes
the fictional CLI/integration catalogue, and adds app guides, screenshots and
project-path routing. Fontsource serves Inter, Newsreader and JetBrains Mono locally;
their SIL Open Font License terms remain with those packages.
