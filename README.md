# i-meb.github.io — Quarto CV site

A from-scratch Quarto redesign for `https://i-meb.github.io`.

## Information architecture

- `index.qmd` — concise research identity and entry points
- `research.qmd` — research questions and methods
- `publications.qmd` — ORCID-synchronized outputs
- `presentations.qmd` — manually curated talks/posters
- `software.qmd` — research software and technical stack
- `cv.qmd` — compact web CV

The site is English-first. Japanese-specific formal records should be linked through researchmap or a Japanese PDF CV rather than maintaining a duplicated Japanese site.

## Local setup

1. Install Quarto.
2. Install Python dependencies if you want to refresh ORCID data.
3. Preview the site:

```bash
quarto preview
```

## ORCID sync

The site uses ORCID only as the upstream source for published research outputs. Education, employment, presentations, and research descriptions remain locally curated so external metadata cannot silently change the official wording of the CV.

Required GitHub repository secrets:

- `ORCID_CLIENT_ID`
- `ORCID_CLIENT_SECRET`

Run locally:

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
export ORCID_CLIENT_ID="..."
export ORCID_CLIENT_SECRET="..."
python scripts/sync_orcid.py
```

The generated `generated/publications.yml` is committed intentionally. This gives local previews a stable cached publication list even when ORCID credentials are unavailable.

### Manual publication corrections

Use `data/publication_overrides.yml`, keyed by stable ID:

```yaml
"doi:10.xxxx/example":
  authors: "Exact Author List"
  venue: "Exact Journal Name"
```

Use `data/publications_manual.yml` only for outputs not represented in ORCID.

## GitHub Pages deployment

`publish.yml` publishes the Quarto output to the `gh-pages` branch. Because `i-meb.github.io` is a GitHub **user site**, set **Settings → Pages → Build and deployment → Branch** to `gh-pages` after the first Quarto publish.

## Migration from the current site

Do not merge the old `index.html`, old CSS, or old runtime ORCID JavaScript into this project.

Recommended migration:

1. Create a backup tag/branch from the current `main`.
2. Replace the working tree with this Quarto project.
3. Fill exact CV metadata and presentations.
4. Add ORCID secrets (existing secrets can be reused if already configured).
5. Run ORCID sync once.
6. Run `quarto preview` locally.
7. Push to `main`.
8. Switch GitHub Pages source to `gh-pages` if required.

## Design rules

- No bilingual duplication.
- No blog unless there is a real publishing need.
- No separate Skills page; technical skills belong in Software and CV.
- No separate Contact page; contact links belong in the homepage/footer/CV.
- No publication data copied by hand when ORCID already contains it.
- No generated `_site` content committed to `main`.
