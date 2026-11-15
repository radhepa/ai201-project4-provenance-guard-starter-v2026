# Capstone run log — before

- Produced by: `capstone/run_capstone_eval.py::main`
- 3 trials, each from a cold start · 2026-11-14 21:21

| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |
|---|---|---|---|---|---|
| 1. Every request leaves one complete entry | 58/58 matched, 0 incomplete | 58/58 matched, 0 incomplete | 58/58 matched, 0 incomplete | 58/58 matched, 0 incomplete | **MET** |
| 2. Timings trustworthy | 100% bounded, >=95% <=50ms, stages 100% | 58/58 bounded, 100% <=50ms, stages 32/32 | 58/58 bounded, 100% <=50ms, stages 32/32 | 58/58 bounded, 100% <=50ms, stages 32/32 | **MET** |
| 3. No writer text in the log | 0 6-grams found | 0 of 3076 6-grams found | 0 of 3076 6-grams found | 0 of 3076 6-grams found | **MET** |
| 4. Latency and CPU budget | warm p95 <=2000ms, cpu <=3000ms, cold <=30s | p95 408ms, cpu 2963ms, cold 12.9s | p95 369ms, cpu 3020ms, cold 14.1s | p95 429ms, cpu 3135ms, cold 14.3s | **MISSED** |
| 5. Decisions unchanged | 30/30 identical, same 8 keys | 30/30 identical, keys same | 30/30 identical, keys same | 30/30 identical, keys same | **MET** |

## Details per trial

### Trial 1 (request ids `cap-6b0795b1-*`)

```json
[
  {
    "criterion": "1. Every request leaves one complete entry",
    "detail": []
  },
  {
    "criterion": "2. Timings trustworthy",
    "detail": {
      "max_gap_ms": 29.3,
      "median_gap_ms": 5.9
    }
  },
  {
    "criterion": "3. No writer text in the log",
    "detail": []
  },
  {
    "criterion": "4. Latency and CPU budget",
    "detail": {
      "warm_n": 31,
      "warm_p95_ms": 408.4,
      "warm_mean_cpu_ms": 2962.7,
      "warm_mean_ms": 305.1,
      "cold_ms": 12929.0
    }
  },
  {
    "criterion": "5. Decisions unchanged",
    "detail": null
  }
]
```

Status codes: 200 200 200 200 200 200 200 200 200 200 200 200 200 200 200 200 200 200 200 200 200 200 200 200 200 200 200 200 200 200 400 415 400 400 400 400 400 400 400 400 413 422 422 422 422 422 422 422 422 422 422 422 429 429 200 404 200 200

### Trial 2 (request ids `cap-d976cfef-*`)

```json
[
  {
    "criterion": "1. Every request leaves one complete entry",
    "detail": []
  },
  {
    "criterion": "2. Timings trustworthy",
    "detail": {
      "max_gap_ms": 29.8,
      "median_gap_ms": 5.75
    }
  },
  {
    "criterion": "3. No writer text in the log",
    "detail": []
  },
  {
    "criterion": "4. Latency and CPU budget",
    "detail": {
      "warm_n": 31,
      "warm_p95_ms": 369.1,
      "warm_mean_cpu_ms": 3020.2,
      "warm_mean_ms": 293.4,
      "cold_ms": 14115.9
    }
  },
  {
    "criterion": "5. Decisions unchanged",
    "detail": null
  }
]
```

Status codes: 200 200 200 200 200 200 200 200 200 200 200 200 200 200 200 200 200 200 200 200 200 200 200 200 200 200 200 200 200 200 400 415 400 400 400 400 400 400 400 400 413 422 422 422 422 422 422 422 422 422 422 422 429 429 200 404 200 200

### Trial 3 (request ids `cap-999e93e8-*`)

```json
[
  {
    "criterion": "1. Every request leaves one complete entry",
    "detail": []
  },
  {
    "criterion": "2. Timings trustworthy",
    "detail": {
      "max_gap_ms": 28.9,
      "median_gap_ms": 6.2
    }
  },
  {
    "criterion": "3. No writer text in the log",
    "detail": []
  },
  {
    "criterion": "4. Latency and CPU budget",
    "detail": {
      "warm_n": 31,
      "warm_p95_ms": 429.1,
      "warm_mean_cpu_ms": 3135.1,
      "warm_mean_ms": 329.7,
      "cold_ms": 14257.9
    }
  },
  {
    "criterion": "5. Decisions unchanged",
    "detail": null
  }
]
```

Status codes: 200 200 200 200 200 200 200 200 200 200 200 200 200 200 200 200 200 200 200 200 200 200 200 200 200 200 200 200 200 200 400 415 400 400 400 400 400 400 400 400 413 422 422 422 422 422 422 422 422 422 422 422 429 429 200 404 200 200
