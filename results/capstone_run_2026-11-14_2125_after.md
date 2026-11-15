# Capstone run log — after

- Produced by: `capstone/run_capstone_eval.py::main`
- 3 trials, each from a cold start · 2026-11-14 21:25

| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |
|---|---|---|---|---|---|
| 1. Every request leaves one complete entry | 58/58 matched, 0 incomplete | 58/58 matched, 0 incomplete | 58/58 matched, 0 incomplete | 58/58 matched, 0 incomplete | **MET** |
| 2. Timings trustworthy | 100% bounded, >=95% <=50ms, stages 100% | 58/58 bounded, 100% <=50ms, stages 32/32 | 58/58 bounded, 100% <=50ms, stages 32/32 | 58/58 bounded, 100% <=50ms, stages 32/32 | **MET** |
| 3. No writer text in the log | 0 6-grams found | 0 of 3076 6-grams found | 0 of 3076 6-grams found | 0 of 3076 6-grams found | **MET** |
| 4. Latency and CPU budget | warm p95 <=2000ms, cpu <=3000ms, cold <=30s | p95 890ms, cpu 617ms, cold 13.7s | p95 844ms, cpu 614ms, cold 13.9s | p95 1093ms, cpu 656ms, cold 12.9s | **MET** |
| 5. Decisions unchanged | 30/30 identical, same 8 keys | 30/30 identical, keys same | 30/30 identical, keys same | 30/30 identical, keys same | **MET** |

## Details per trial

### Trial 1 (request ids `cap-a2d4537a-*`)

```json
[
  {
    "criterion": "1. Every request leaves one complete entry",
    "detail": []
  },
  {
    "criterion": "2. Timings trustworthy",
    "detail": {
      "max_gap_ms": 28.2,
      "median_gap_ms": 4.05
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
      "warm_p95_ms": 890.0,
      "warm_mean_cpu_ms": 616.9,
      "warm_mean_ms": 619.0,
      "cold_ms": 13679.3
    }
  },
  {
    "criterion": "5. Decisions unchanged",
    "detail": null
  }
]
```

Status codes: 200 200 200 200 200 200 200 200 200 200 200 200 200 200 200 200 200 200 200 200 200 200 200 200 200 200 200 200 200 200 400 415 400 400 400 400 400 400 400 400 413 422 422 422 422 422 422 422 422 422 422 422 429 429 200 404 200 200

### Trial 2 (request ids `cap-3f54a2db-*`)

```json
[
  {
    "criterion": "1. Every request leaves one complete entry",
    "detail": []
  },
  {
    "criterion": "2. Timings trustworthy",
    "detail": {
      "max_gap_ms": 29.4,
      "median_gap_ms": 4.4
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
      "warm_p95_ms": 844.3,
      "warm_mean_cpu_ms": 614.4,
      "warm_mean_ms": 619.3,
      "cold_ms": 13859.5
    }
  },
  {
    "criterion": "5. Decisions unchanged",
    "detail": null
  }
]
```

Status codes: 200 200 200 200 200 200 200 200 200 200 200 200 200 200 200 200 200 200 200 200 200 200 200 200 200 200 200 200 200 200 400 415 400 400 400 400 400 400 400 400 413 422 422 422 422 422 422 422 422 422 422 422 429 429 200 404 200 200

### Trial 3 (request ids `cap-d40af4ef-*`)

```json
[
  {
    "criterion": "1. Every request leaves one complete entry",
    "detail": []
  },
  {
    "criterion": "2. Timings trustworthy",
    "detail": {
      "max_gap_ms": 28.1,
      "median_gap_ms": 5.55
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
      "warm_p95_ms": 1093.0,
      "warm_mean_cpu_ms": 656.2,
      "warm_mean_ms": 666.5,
      "cold_ms": 12872.4
    }
  },
  {
    "criterion": "5. Decisions unchanged",
    "detail": null
  }
]
```

Status codes: 200 200 200 200 200 200 200 200 200 200 200 200 200 200 200 200 200 200 200 200 200 200 200 200 200 200 200 200 200 200 400 415 400 400 400 400 400 400 400 400 413 422 422 422 422 422 422 422 422 422 422 422 429 429 200 404 200 200
