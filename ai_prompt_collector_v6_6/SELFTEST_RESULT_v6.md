# AI Prompt Collector v6 — Self-test Result

- Manifest validation: **PASS** — 93 rows, 0 errors, 0 warnings
- Python syntax compile: **PASS**
- Local Git clone: **PASS**
- Incremental Git pull/update: **PASS**
- Text-only sparse checkout: **PASS**
- Git LFS smudge skip configuration: **PASS (implemented in runner environment)**
- JSON/Markdown prompt extraction: **PASS**
- Language/input-mode inference: **PASS**
- Source URL / license / verified date / git commit propagation: **PASS**
- SQLite FTS database generation: **PASS**
- Ranked recommendation: **PASS**
- Model optimization profile lookup: **PASS**
- Exact duplicate pipeline: **PASS**
- Near-duplicate review detection: **PASS**
- Repo overlap reporting: **PASS**
- Postflight CSV/SQLite count reconciliation: **PASS**
- HTML dashboard generation: **PASS**
- Excel repository index render/formula scan: **PASS**

The only unexecuted step in the ChatGPT environment is mass cloning the 73 public active GitHub repositories, because this environment blocks direct bulk git network access. `START_HERE.bat` performs that step on an internet-connected Windows PC.
