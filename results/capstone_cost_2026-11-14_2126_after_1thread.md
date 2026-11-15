# Capstone cost — 10 runs

- Produced by: `capstone/run_capstone_eval.py::run_cost`, from `logs/requests.jsonl`
- 2026-11-14 21:26 · request ids `cost-4838fad8-*` · machine: 16 logical CPUs, CPU-only torch

| Run | tokens | duration_ms | cpu_ms | model_ms | style_ms | guess |
|---|---|---|---|---|---|---|
| 1 | 112 | 639.7 | 640.6 | 636.8 | 0.4 | unsure |
| 2 | 100 | 536.0 | 562.5 | 533.7 | 0.3 | unsure |
| 3 | 109 | 570.6 | 562.5 | 567.9 | 0.4 | unsure |
| 4 | 143 | 694.6 | 687.5 | 692.2 | 0.4 | unsure |
| 5 | 85 | 480.2 | 468.8 | 478.1 | 0.2 | unsure |
| 6 | 123 | 631.3 | 625.0 | 628.2 | 0.3 | ai |
| 7 | 133 | 659.7 | 656.2 | 656.7 | 0.5 | ai |
| 8 | 137 | 693.0 | 656.2 | 690.4 | 0.4 | ai |
| 9 | 126 | 682.5 | 687.5 | 680.1 | 0.4 | ai |
| 10 | 135 | 710.7 | 687.5 | 707.4 | 0.4 | ai |

Cold start (model load, not one of the 10): duration 14350.8 ms, cpu 13625.0 ms.

```
total CPU   = 0.641 + 0.562 + 0.562 + 0.688 + 0.469 + 0.625 + 0.656 + 0.656 + 0.688 + 0.688 = 6.234 CPU-s
per run     = 6.234 / 10 = 0.623 CPU-s   (wall 0.630 s, 120 tokens)
100 a day   = 100 x 0.623 = 62.3 CPU-s = 1.04 CPU-min of compute
            + 1 cold start a day (13.6 CPU-s) = 76.0 CPU-s
tokens/day  = 100 x 120 = 12030 tokens through gpt2
API spend   = $0 (gpt2 runs locally; no hosted API is called)
```
