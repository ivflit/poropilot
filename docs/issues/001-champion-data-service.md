# [T1] Champion static-data service (Data Dragon)

<!--
Ready to file with the GitHub CLI once a remote exists:

  gh issue create \
    --title "[T1] Champion static-data service (Data Dragon)" \
    --body-file docs/issues/001-champion-data-service.md \
    --label "p1,backend"

Then create the p1/p2/p3, backend/frontend/infra and `ralph` labels once,
and repeat this template per task in tasks.md.
-->

**Priority:** p1  ·  **Area:** backend  ·  **Ralph:** no
**Blocks:** T2 (profile display), T3 (pool/win-rate), T4 (draft UI)
**Blocked by:** nothing — this is the first task.

## Summary

The Riot API returns numeric champion IDs. We need a service that maps those IDs
to human-readable names, titles and icon URLs from Riot's Data Dragon CDN, so the
rest of the app can show something readable. Everything visual depends on this, so
it goes first.

## Acceptance criteria

- [ ] Backend fetches and caches the current Data Dragon version on startup.
- [ ] A service maps `championId` → `{name, title, imageUrl}`.
- [ ] `GET /api/champions` returns the full mapping.
- [ ] Data is cached (no Data Dragon call per request).
- [ ] Unit tests cover the ID→name mapping with a stubbed dataset.

## Notes

- Data Dragon needs no API key. Version list:
  `https://ddragon.leagueoflegends.com/api/versions.json`; champion data:
  `.../cdn/{version}/data/en_US/champion.json`; icons:
  `.../cdn/{version}/img/champion/{image}`.
- Follow the backend conventions in `CLAUDE.md` (Pydantic, DI, pooled httpx,
  thin router). Load the `fastapi-python` skill before starting.
