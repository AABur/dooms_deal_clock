# Static Push Deployment (Variant 1)

Goal: Keep full backend on NAS (updates, Telegram, DB). Publish a safe, static snapshot to external hosting that the current frontend can consume without code changes.

## Scope
- No backend changes on external hosting.
- NAS builds static site + API snapshot and pushes it out.
- Keep SQLite and session strictly on NAS; optional: include a read-only SQLite copy with the static for archive/SEO.

## Deliverables
- export_static.sh (NAS):
  - Build `dist/` directory:
    - Copy `web/` assets (excluding admin tools if any).
    - Create `dist/api/` tree with JSON responses:
      - `/api/health` -> `dist/api/health/index.html`
      - `/api/clock/latest` -> `dist/api/clock/latest/index.html`
      - `/api/clock/history` -> `dist/api/clock/history/index.html` (use `?limit=...` internally; publish a single file)
    - Optionally add `dist/version.txt` and `dist/build_info.json` (timestamp, git sha, source API URL).
    - Optional: add `dist/data/clock_data.sqlite` (read-only copy) for backup/archive.
  - Source of truth for JSON: call NAS API (`http://127.0.0.1:8000/api/...`) and serialize exact payloads.
  - Validate JSON structure (non-empty, required keys present).

- deploy_static.sh (NAS -> REG.RU):
  - Rsync over SSH to `~/www/doomsdealclock.ru/` (or exact path):
    - `rsync -az --delete dist/ user@server18.hosting.reg.ru:/var/www/<user>/data/www/doomsdealclock.ru/`
  - Dry-run mode and logging to `admin/logs/` on NAS.
  - Atomic-ish rollout: upload to `dist_tmp` then move into place, or rely on rsync --delete.

- Makefile targets (optional on NAS):
  - `make export-static` -> runs export script
  - `make deploy-static` -> runs deploy script
  - `make publish` -> export + deploy

## Directory Structure (published)
- `/index.html`, `/styles.css`, `/script.js` (as in `web/`)
- `/api/health/index.html` (JSON)
- `/api/clock/latest/index.html` (JSON)
- `/api/clock/history/index.html` (JSON)
- Optionally `/data/clock_data.sqlite`

## Update Workflow
- Trigger: cron or event on NAS after new data stored.
- Steps:
  1) export_static.sh builds `dist/` from local API.
  2) deploy_static.sh syncs `dist/` to REG.RU.
- Frequency: every 2–5 minutes.

## Cron Examples (NAS)
- `*/5 * * * * /path/to/export_static.sh && /path/to/deploy_static.sh >> /path/to/admin/logs/publish.log 2>&1`

## Validation
- After deploy: curl HEAD/GET against external URLs:
  - `https://doomsdealclock.ru/` (page loads, assets 200)
  - `https://doomsdealclock.ru/api/health` (200 JSON)
  - `https://doomsdealclock.ru/api/clock/latest` (200 JSON)
  - `https://doomsdealclock.ru/api/clock/history` (200 JSON)

## Risks & Mitigations
- Stale data between pushes: choose small cron interval; embed `build_info.json` to confirm freshness.
- Partial uploads: use rsync; consider temp dir + rename if needed.
- Caching: set proper headers on REG.RU if possible; or version file names.

## Next Steps
- Implement export_static.sh and deploy_static.sh (NAS).
- Add Make targets (NAS only).
- Configure SSH key from NAS to REG.RU (use admin/ssh_setup.sh on REG.RU once).

