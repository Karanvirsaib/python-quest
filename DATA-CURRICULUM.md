# Python for Data: the question path

The learning target is the scope of tasks encountered from first-time Python use through roughly 2–3 years of applied data work. Completing exercises is practice, not a substitute for workplace experience. Every scenario uses synthetic, self-contained data; no credentials, paid services, or real customer data are needed.

| Order | Course | Exercises | Focus |
|---|---|---:|---|
| 1–4 | Python foundations, decisions, collections, functions | 24 | First principles and reusable code |
| 5 | Python for Messy Data | 8 | Currency, CSV quoting, nested JSON, UTC, streams, deduplication |
| 6 | NumPy for Data Work | 8 | Masks, broadcasting, missing values, ratios, standardization |
| 7 | pandas: Clean & Transform | 8 | Types, null audits, snapshots, safe joins, daily series, lag, cohorts |
| 8 | SQL from Python | 8 | Bound parameters, grouping, joins, windows, ranks, retention, atomic upserts |
| 9 | Analytical Thinking & ML Evaluation | 8 | Metric grains, precision/recall, weighted rates, leakage, uncertainty, guardrails |
| 10 | Reliable Data Pipelines | 8 | Quarantine, pagination, retries, late data, idempotency, chunking, redaction, quality gates |
| 11 | Production Data Problem Solving | 8 | Mutable state, JSONL, indexed joins, sessions, temporal joins, freshness, recovery |
| 12 | Real-World Data Case Studies | 8 | Retail, attribution, MRR, inventory, settlements, anomalies, point-in-time features, data product |

Each new exercise specifies its function signature, input grain, output shape, empty-input policy, mutation rules, and relevant boundaries. It includes starter code, inspectable examples, hints, a worked solution, and checks covering more than a happy-path sample. The final cases integrate skills from earlier tracks. Use Check answer for SQL exercises: their in-memory database fixtures are prepared by the checks, without requiring external database access.

The stages are a learning sequence, not a claim that an exercise confers a job title. The advanced tracks emphasize business definitions, reproducibility, failure handling, and observable invariants. Production performance cannot be established from these small fixtures; benchmark and load-test with representative data in a real project.

## Suggested way to work

1. Read the contract and predict the result before running code.
2. Implement without opening the solution; use the hint when stuck.
3. Add your own counterexample: duplicates, an empty input, a boundary timestamp, or a failed callback.
4. Explain the data grain and what would go wrong if the assumption changed.
5. Save a short note about the failure mode you learned.

## Verification

Run `scripts/expand-curriculum.py` to regenerate the authored data tracks while retaining the first four courses and their stable lesson IDs. Run `scripts/check-curriculum.py` with NumPy and pandas installed. It compiles starter code, executes every solution against its checks, and verifies that each new suite rejects a no-op function. Browser verification uses the same Pyodide worker as the application, including library loading and SQLite.

## Further reading

- [Python standard library](https://docs.python.org/3/library/)
- [pandas joins and cardinality validation](https://pandas.pydata.org/docs/user_guide/merging.html)
- [NumPy broadcasting](https://numpy.org/doc/stable/user/basics.broadcasting.html)
- [Pyodide package loading](https://pyodide.org/en/stable/usage/loading-packages.html)
