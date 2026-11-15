# Capstone cost — 10 runs

- Produced by: `capstone/run_capstone_eval.py::run_cost`, from `logs/requests.jsonl`
- 2026-11-14 21:25 · request ids `cost-2e1969b0-*` · machine: 16 logical CPUs, CPU-only torch

| Run | tokens | duration_ms | cpu_ms | model_ms | style_ms | guess |
|---|---|---|---|---|---|---|
| 1 | 112 | 332.6 | 2703.1 | 328.8 | 0.5 | unsure |
| 2 | 100 | 267.1 | 3125.0 | 263.7 | 0.3 | unsure |
| 3 | 109 | 322.5 | 3125.0 | 319.1 | 0.4 | unsure |
| 4 | 143 | 378.5 | 3359.4 | 374.7 | 0.8 | unsure |
| 5 | 85 | 302.9 | 2937.5 | 299.4 | 0.4 | unsure |
| 6 | 123 | 460.7 | 3671.9 | 457.1 | 0.7 | ai |
| 7 | 133 | 377.2 | 2890.6 | 372.7 | 0.7 | ai |
| 8 | 137 | 355.5 | 2968.8 | 351.8 | 0.6 | ai |
| 9 | 126 | 254.8 | 2781.2 | 251.8 | 0.6 | ai |
| 10 | 135 | 284.6 | 2953.1 | 280.8 | 0.6 | ai |

Cold start (model load, not one of the 10): duration 15495.5 ms, cpu 19078.1 ms.

```
total CPU   = 2.703 + 3.125 + 3.125 + 3.359 + 2.938 + 3.672 + 2.891 + 2.969 + 2.781 + 2.953 = 30.516 CPU-s
per run     = 30.516 / 10 = 3.052 CPU-s   (wall 0.334 s, 120 tokens)
100 a day   = 100 x 3.052 = 305.2 CPU-s = 5.09 CPU-min of compute
            + 1 cold start a day (19.1 CPU-s) = 324.2 CPU-s
tokens/day  = 100 x 120 = 12030 tokens through gpt2
API spend   = $0 (gpt2 runs locally; no hosted API is called)
```
