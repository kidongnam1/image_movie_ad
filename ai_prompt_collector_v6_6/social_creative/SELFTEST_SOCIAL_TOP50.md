# SNS Creative TOP50 Selftest

- Candidate rows: 58
- Duplicate repo names: 0
- Refresh/ranking synthetic test: PASS
  - metadata OK: 58/58 (mock)
  - Stars TOP50 rows: 50
  - Recommended TOP50 rows: 50
  - SQLite `top50_stars`: 50 rows
  - SQLite `top50_recommended`: 50 rows
- Download synthetic test: PASS
  - selected: 50
  - success: 50
  - failed: 0
  - local repo folders created: 50
- Python compile: PASS
- Download policy: shallow clone + blob filter + Git LFS skip

Actual public GitHub Stars are refreshed on the user's internet-connected PC immediately before final TOP50 selection.
