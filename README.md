# Zindi Bias Bounty Mapping Equity Challenge: designmastersolutions

Start with [WRITEUP.pdf](WRITEUP.pdf) (version 2, 4 November 2026; source in [WRITEUP.md](WRITEUP.md)). It is the
writeup submitted for Best Bias Discovery and Best Documentation, tied to leaderboard submissions RoWYaNLs and
eAwjeoDr. `WRITEUP-2026-10-28-original.pdf` is the first version; [CORRECTION-2026-10-31.md](CORRECTION-2026-10-31.md)
explains what changed.

Reproduce (Python 3; put the challenge data package, CC-BY-SA 4.0 and not redistributed here, in `data/`):

```
python -m venv .venv && .venv/bin/pip install duckdb pandas pyarrow
.venv/bin/python src/features.py && .venv/bin/python src/predict.py   # scored file, submissions/v2.csv
.venv/bin/python src/discovery_sources.py                             # every table in the bias discovery
.venv/bin/python -m unittest tests/test_closed_share.py               # closure-flag denominator tests
.venv/bin/python tools/build_writeup_pdf.py                           # WRITEUP.pdf (needs pandoc and typst)
```
