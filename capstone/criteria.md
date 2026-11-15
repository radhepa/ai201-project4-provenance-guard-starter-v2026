# Capstone acceptance criteria — Provenance Guard, Shape A (deploy and instrument)

Written and committed **before** the instrumentation was run against anything.
The targets are not edited after seeing results; if one turns out wrong, the
README says so instead.

> Drafted with AI assistance (Claude). See "How I Used AI" under `## Capstone`
> in the README.

**What's being added:** a request log, `logs/requests.jsonl`, with one
structured line per HTTP request to `/submit` or `/appeal`. That includes
requests that are refused or rate-limited. Each line records how long the
request took, how much CPU it burned and what came out, and for scored
submissions where the time went (signal one vs signal two) and how many tokens
gpt2 read. It's separate from `logs/audit.jsonl`. The audit log records
*decisions*. This log records *operations*.

**Schema.** Every entry has these fields, never null:
`timestamp`, `request_id`, `route`, `method`, `status`, `duration_ms`,
`cpu_ms`, `input_bytes`, `input_sha256`, `outcome`.
An accepted `/submit` (status 200) also has these, never null:
`words`, `tokens_scored`, `model_ms`, `style_ms`, `cold_start`.

**One trial** (`capstone/run_capstone_eval.py`):
1. Start the service fresh, on its own port.
2. Send a fixed batch of **58 requests**:
   - the 30 evaluation texts (20 known-human, 10 known-AI)
   - the 12 malformed requests from criterion 5 of `criteria.md`
   - a 12-request burst from one `creator_id` (crosses the 10/minute limit)
   - 2 appeals: one valid, one with an unknown `content_id`
   - a further 2 accepted submissions, used only to check C2
3. Time each request on the client.
4. Stop the service and read the log.

Three trials, each from a cold start. A criterion is MET only if it holds on
all three.

---

## 1. Every request leaves exactly one complete log entry *(extension)*

**Measurement:** Match log entries to requests by `request_id`. The client
sends it as an `X-Request-Id` header, and the server echoes it back.

**Target:** 58 of 58 requests matched to exactly one entry, with **0** required
fields missing or null, on every trial.

**Why this target:** The whole point of instrumenting is to see what the
service is doing. A refused request or a 429 that leaves no line is the
attack you never find; unit 8 already showed that refusals are where the
interesting failures are. Anything under 100% means the log lies by omission.
A missing CPU number also makes the cost figures below wrong.

## 2. The timings are trustworthy *(extension)*

**Measurement:** Compare each entry's server-side `duration_ms` with the
client's round-trip time for the same request. For accepted submissions,
compare `model_ms + style_ms` with `duration_ms`.

**Target:** For **100%** of requests, `0 <= duration_ms <= client_ms`. For
**≥ 95%** of requests, `client_ms − duration_ms <= 50 ms`. For **100%** of
accepted submissions, `model_ms + style_ms <= duration_ms`.

**Why this target:** Every cost and latency number in the write-up comes from
these fields. A timer that starts late, for example after another hook has
already done work, makes the service look cheaper than it is. A cost
estimate built on that is the kind of mistake that gets a deployment
under-provisioned. 50 ms is loopback HTTP overhead plus JSON encoding. More
than that means the timer is missing part of the request.

## 3. No writer's text ends up in the request log *(extension)*

**Measurement:** For every text sent in the trial, take every run of 6
consecutive words and search for it in `logs/requests.jsonl`.

**Target:** **0** matches, on every trial.

**Why this target:** A request log gets tailed, pasted into READMEs and
shipped to log tools. Writers' unpublished work must not leak through it. The
log needs to identify an input, which a hash and a size do, without holding
it. One leaked paragraph is a privacy failure no latency win pays for.

## 4. Latency and compute cost stay inside a budget *(extension)*

**Measurement:** Use the logged `duration_ms` and `cpu_ms` of accepted
`/submit` requests. A warm request is one with `cold_start == false`. The cold
request is the first accepted one after start-up.

**Target:**
- warm p95 `duration_ms` **≤ 2000 ms**
- warm mean `cpu_ms` **≤ 3000 ms** (3 CPU-seconds per scored submission)
- the cold request **≤ 30 s**

All three must hold on every trial.

**Why this target:** Two seconds is about as long as a writer will wait after
pressing submit before assuming it broke and pressing again, and pressing
again now costs them a rate-limit slot. 3 CPU-seconds caps 100 submissions a
day at 5 CPU-minutes, which a single laptop core absorbs without noticing. 30
s for the first request after a restart (gpt2 loading into memory) is the
longest an HTTP client waits by default before timing out. Past that, the
first writer after every restart gets an error.

## 5. Instrumenting changes nothing a writer sees *(regression)*

**Measurement:** Compare the 30 evaluation texts with the unit 8 *after* run
(`results/run_2026-11-14_2109_after.json`). Check the response keys of an
accepted `/submit`.

**Target:** **30 of 30** get the identical `guess` and identical
`combined_score`, and the accepted response has exactly the same 8 keys as
before, on every trial. Also `python -m pytest tests` passes.

**Why this target:** An operational layer that changes a decision is a bug,
whatever it measures. If logging shifted even one label, every result from
units 7 and 8 would stop describing the service that's actually running.
