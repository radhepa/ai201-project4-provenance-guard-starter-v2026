# Unit 10 demo: Provenance Guard

About 3 minutes, four beats. Keep `capstone/criteria.md` and
`results/capstone_run_2026-11-14_2121_before.md` open while presenting.

## Before the session (5 minutes)

1. Start it: `python app.py` (serves `http://127.0.0.1:5000`).
2. Wait for `ready in …s` (about 15 s). gpt2 loads at start-up now, so the
   first submission is fast: 0.48 s in rehearsal, against 18.4 s before.
3. In a second terminal: `tail -f logs/requests.jsonl`, to show the log
   filling live.
4. Have the submit command ready (Git Bash; in PowerShell use `curl.exe` on
   one line):

```bash
curl -X POST http://127.0.0.1:5000/submit -H "Content-Type: application/json" -d '{"creator_id": "demo", "text": "PASTE 40+ WORDS HERE"}'
```

## Beat 1: What I built (about 45 s)

> "Provenance Guard is a small web service that guesses whether a piece of
> writing was written by a person or an AI tool. It returns human, AI or
> unsure, never a bare accusation. It combines two signals: how predictable
> gpt2 finds the text, and its style, meaning sentence-length spread, word
> variety and punctuation. Every decision goes to an audit log, and writers
> can appeal. For the capstone I instrumented it: every request now writes
> one log line with its wall time, CPU time, time per signal and outcome.
> The line holds a hash of the input, never the text."

**Show it:** run the curl. Point at the JSON response, then at the new line
in `requests.jsonl` (`duration_ms`, `cpu_ms`, `model_ms`, `outcome`).

## Beat 2: What standard I set (about 30 s)

Read criterion 4 from `criteria.md`:

> "Latency and CPU budget: warm p95 at or under **2000 ms**, mean warm CPU
> at or under **3000 ms** per scored request, and the cold first request at
> or under **30 s**, on every trial. Two seconds is about how long a writer
> waits before pressing submit again. Three CPU-seconds keeps 100 submissions
> a day under 5 CPU-minutes."

Optional second criterion, criterion 3: **zero** six-word runs of any
submitted text may appear in the log. The log must never hold the writing.

## Beat 3: What the test found (about 60 s)

> "Three cold-start trials of 58 requests each. Four criteria held on every
> trial. **Criterion 4 missed**: mean CPU was 2963, 3020 and 3135 ms. That's
> two of three over the budget, and the one that passed did so by 37 ms.
> Latency was fine at about 0.4 s, so it wasn't slow. It was burning CPU.
> The log showed where: gpt2 was 99% of every request's time, and CPU time
> was **10 times** wall time. torch was running gpt2 on 8 threads by default,
> and for a ~130-token input most of them sit waiting on each other. I
> confirmed it by measuring gpt2 alone: 8 threads used 2405 ms of CPU for
> 324 ms of wall time, while 1 thread used 620 ms for 631 ms."

## Beat 4: What I changed (about 45 s)

> "One setting: torch now runs on one thread. CPU per request fell to 614–656
> ms, about a fifth. All five criteria were met on all three trials, and all
> 30 test decisions are identical to before. A hundred submissions a day went
> from 324 to 76 CPU-seconds. The cost: warm latency roughly doubled, to
> 0.9–1.1 s. That's still under half the budget, but a writer waits longer.
> Since then I've done the one thing I said I'd do first: the model loads at
> start-up, so the first writer waits half a second instead of 18. What's
> still broken: text in Japanese or other non-Latin scripts is refused as
> 'too short', because the word counter only counts ASCII words. And one
> maximum-length input took 2.2 s, over my 2-second budget, even though p95
> passes."

## Peer testing

**Hand over:** `RUNNING.md` (section "Capstone: Path B"). Then stop talking.

**What rehearsal says they'll probably hit:**

| They try | What happens |
|---|---|
| Starting it | about 15 s before it listens, while gpt2 loads; wait for `ready in` |
| Empty text | 400 `empty_field` |
| No JSON header | 415 `unsupported_media_type` |
| A one-line question | 422 `text_too_short` (under 20 words) |
| Something enormous (>20,000 chars) | 413 `field_too_long` |
| Non-English text | 422 `text_too_short`, even with plenty of words |
| An everyday paragraph about a walk to the market | "unsure" (0.786) in rehearsal, not "human" |
| 11+ submits in a minute | 429 `rate_limited` |

**My job when they report back:** write it down and ask one question. Don't
explain.

## Feedback sheet

For the system I test:

- Started from RUNNING.md alone? yes / no. If no, where it stopped:
- One thing that worked:
- One thing that surprised me:
- One thing I couldn't figure out:

From the person who tested mine:

- Worked:
- Surprised them:
- Couldn't figure out:
- My one question:
