# Provenance Guard

> ### 👋 Start here
>
> **New to this repo? Read [RUNNING.md](RUNNING.md) first.**
>
> Once `python test.py` passes, in one terminal:
>
> ```bash
> python app.py
> ```
>
> and in another:
>
> ```bash
> curl -X POST http://127.0.0.1:5000/ping \
>   -H "Content-Type: application/json" \
>   -d '{"message": "hello"}'
> ```
>
> That's a web service. Something sent it text and it sent something back.
> Everything this unit is filling in the middle.
>
> **The rest of this file is your submission.** Fill it in as you go.

---

<!-- ─────────────────────────────────────────────────────────────────────────
     Unit 7 asks for the first five sections. Unit 8 adds the five below.

     Everything is pasted as TEXT. A pasted curl response gets full credit;
     a picture of your terminal gets none.
     ───────────────────────────────────────────────────────────────────────── -->

<!-- ═══════════════════════ UNIT 7 — THE BUILD ═══════════════════════ -->

## What This Does

Provenance Guard takes a piece of writing, gives an opinion on whether a person
or an AI tool wrote it, says so in plain English, and lets the writer appeal.

1. **The request arrives.** `POST /submit` with JSON `{"text": ..., "creator_id": ...}`
   (`app.py::submit`).
2. **It's checked before anything is scored.** Not JSON → `415`; malformed body,
   or a missing, blank or wrong-type field → `400`; text over 20,000 characters
   (or a body over 256 KB) → `413`; fewer than 20 words → `422`. Every refusal is
   answered in JSON and written to the audit log as a `rejected` entry.
3. **Signal one — the model signal.** `detector.model_signal` runs gpt2 locally
   (loaded once, reused for every request) and turns its perplexity into a 0–1
   score, higher = more AI-like. If the model can't load the answer is `503`.
4. **Signal two — the style signal.** `stylometry.style_signal` measures the shape
   of the text: sentence-length spread, vocabulary variety and expressive
   punctuation, each scaled to 0–1 and averaged.
5. **The two are combined** by `scoring.py::combine_signals`: a 0.6 / 0.4 weighted
   mean, pulled toward 0.5 when the signals disagree.
6. **The score becomes a label** in `scoring.py::score_to_label`: one of three
   full sentences, with a conservative line for the AI label.
7. **Everything is logged and answered.** The decision goes to `logs/audit.jsonl`
   with a new `content_id`, both signal scores, the combined score, the label and
   `status: "decided"`; the response carries the same fields. If the writer
   disagrees, `POST /appeal` with that `content_id` moves it to `under_review`
   and logs the reason beside the original decision.

---

## Signals and Scoring

### Signal one — the model signal

**What it measures:** How predictable the text is to gpt2 (perplexity over the
first 400 tokens), squashed onto 0–1 with
`score = 1 / (1 + (perplexity / 45) ** 1.6)` in `detector.py::model_signal`.
Perplexity 45 scores 0.5; lower perplexity scores higher (more AI-like). I left
the starter's midpoint (45) and steepness (1.6) unchanged.

**Why that might differ between human and AI writing:** A language model writes
by picking likely next words, so its output is text a model finds easy to
predict. Human writing takes more unlikely turns. On my evaluation set the
Claude-written passages scored 0.84–0.96; the pre-1930 human passages scored
0.15–0.80.

**What it can't see:** Who wrote the words. It rewards common words in short,
ordinary sentences, so plain human writing scores AI-like: the plain passages
in my human set (children's readers, *Up from Slavery*, *The Wizard of Oz*)
averaged a higher model score than the ornate ones, and one Booker T.
Washington passage scored 0.80, as high as some AI text. It also can't tell
memorised text from generated text: a famous passage gpt2 has seen many times
is very predictable to it.

### Signal two — the style signal

**What it measures:** Three things about the text's shape, none of them its
meaning (`stylometry.py`):

- **Sentence-length spread:** coefficient of variation (stdev / mean) of words
  per sentence. Low spread → AI-like. One sentence has no spread and counts as
  neutral (0.5), not as AI.
- **Vocabulary variety:** moving-average type-token ratio over 50-word windows
  (plain TTR for shorter text, so short submissions don't break it). On my
  calibration data this ran the *opposite* way to what I expected: generated
  prose avoids repeating words, human narrative repeats names and pronouns. So
  high variety → AI-like.
- **Expressive punctuation:** semicolons, colons, dashes, brackets, quotation,
  question and exclamation marks per word. Full stops and commas are not
  counted. Almost none → AI-like.

Each is mapped linearly onto 0–1 between an "AI end" and a "human end" from
`config.py` (`STYLE_SPREAD_RANGE`, `STYLE_TTR_RANGE`, `STYLE_PUNCT_RANGE`),
clamped, and the three are averaged with equal weights.

**Why that might differ between human and AI writing:** Generated prose tends
toward even, mid-length sentences and leans on full stops and commas. Human
writing is lumpier: a three-word sentence next to a forty-word one, a dash, a
quotation, a question.

**What it can't see:** Anything about what the text says. Adding a few
semicolons, splitting sentences unevenly or pasting in a quotation moves it
toward "human" without changing a word of the substance. Dialogue-heavy human
writing reads very human to it; dense, varied expository human writing
(a report, an essay with no quotations) reads AI-like.

**How the constants were set:** From a calibration split only — 26 Gutenberg
passages taken from different positions in the same books and 5 separate
Claude-written passages (`eval_data/calibration_*.json`,
`python eval_data/calibrate.py`). The evaluation set was never used for tuning.

### The combining rule

**The rule:** Take a weighted mean that trusts the model signal more, because it
reads the words and the style signal only sees the shape. Then, if the two
signals disagree by more than 0.3, pull the result toward 0.5 in proportion to
how far past 0.3 they disagree. At a complete split (0 vs 1) the result is
exactly 0.5. Two methods disagreeing is uncertainty, so a single loud signal
can't produce a confident label by itself.

**The numbers** (all in `config.py`):

```
mean  = 0.6 * model_score + 0.4 * style_score       # WEIGHT_MODEL_SIGNAL, WEIGHT_STYLE_SIGNAL
gap   = |model_score - style_score|
if gap > 0.3:                                        # DISAGREEMENT_GAP
    keep  = 1 - (gap - 0.3) / (1 - 0.3)
    score = 0.5 + (mean - 0.5) * keep
else:
    score = mean
```

Thresholds: `HUMAN_THRESHOLD = 0.35`, `AI_THRESHOLD = 0.85` (0.75 in unit 7;
raised in unit 8 — see The Improvement). A consequence I
test for (`tests/test_scoring.py::test_ai_label_requires_both_signals_above_half`):
a score above the AI threshold is only reachable when *both* signals are above 0.5.

**Where it lives:** `scoring.py::combine_signals`

**A case where my two signals split, and what my rule does with it:**
`human_2376_35`, a plain passage from Booker T. Washington's *Up from Slavery*
(1901). The model signal said 0.7988 (AI-like — plain, predictable words); the
style signal said 0.1878 (human-like — uneven sentences, dashes). The plain
weighted mean would be 0.554; the gap of 0.61 is 0.31 past the 0.3 allowance,
so only 56% of the distance from 0.5 is kept and the final score is 0.5302:
**unsure**. A person wrote it, so "unsure" is a miss in the cautious direction,
which is the direction I chose.

---

## Label Variants

`python scoring.py` prints the ranges straight from `config.py`.

| Label | Score range | The exact text a reader sees |
|---|---|---|
| high-confidence human | 0.00 ≤ score < 0.35 | We think a person most likely wrote this. Our checks found the patterns we usually see in human writing. |
| unsure | 0.35 ≤ score ≤ 0.85 | We can't tell whether a person or an AI tool wrote this. A lot of writing that people do entirely on their own lands here, so please don't read this as an accusation. |
| high-confidence AI | 0.85 < score ≤ 1.00 | We think this was most likely written with an AI tool. Two separate checks both pointed that way, but they can be wrong: if you wrote this yourself, you can appeal and a person will review it. |

These are the current ranges; in unit 7 the AI line was 0.75 (the unit 8
attack run moved it). Both boundary values (0.35 and 0.85) belong to "unsure", so there's no gap and
no overlap; the tests sweep every 0.0001 from 0 to 1 to check that. All three
labels were reached by real submissions to the live service (see the criteria
check below).

**Why I worded the "unsure" one this way:**
Most real human writing in my evaluation landed here (18 of 20 pre-1930
passages), so whoever reads this label is most likely a person who wrote every
word. It says plainly that the system couldn't tell, puts that on the system
rather than on the writer, and tells them in so many words that it isn't an
accusation. It avoids numbers and the word "threshold", and it doesn't say
"may have used AI", which would read as a soft accusation.

---

## Sample Run

Real requests to the live service (`python app.py`, real gpt2), sent with
`curl` from Git Bash on 2026-11-08. The text is a passage from Booker T.
Washington's *Up from Slavery* (1901), from the calibration split, so a
person certainly wrote it.

**A submission**

```bash
$ cat body.json
{"text": "One of the most encouraging signs in connection with the Tuskegee school is found in the fact that the organization is so thorough that the daily work of the school is not dependent upon the presence of any one individual. The whole executive force, including instructors and clerks, now numbers eighty-six. This force is so organized and subdivided that the machinery of the school goes on day by day like clockwork. Most of our teachers have been connected with the institutions for a number of years, and are as much interested in it as I am. In my absence, Mr. Warren Logan, the treasurer, who has been at the school seventeen years, is the executive. He is efficiently supported by Mrs. Washington, and by my faithful secretary, Mr. Emmett J. Scott, who handles the bulk of my correspondence and keeps me in daily touch with the life of the school, and who also keeps me informed of whatever takes place in the South that concerns the race. I owe more to his tact, wisdom, and hard work than I can describe.", "creator_id": "radhepa_demo"}

$ curl -s -X POST http://127.0.0.1:5000/submit \
  -H "Content-Type: application/json" \
  -d @body.json
```

```json
{
    "combined_score": 0.5883,
    "confidence": 0.5883,
    "content_id": "78b393715a754e528455b88a86534039",
    "guess": "unsure",
    "label": "We can't tell whether a person or an AI tool wrote this. A lot of writing that people do entirely on their own lands here, so please don't read this as an accusation.",
    "model_score": 0.7279,
    "status": "decided",
    "style_score": 0.3911
}
```

`guess` is the classification; `confidence` is the combined score on the same
0 (human) to 1 (AI) scale. Plain, predictable wording pushed the model signal
to 0.73; uneven sentences pulled the style signal to 0.39; they're 0.34 apart,
so the rule pulled the 0.59 mean slightly toward the middle.

**An appeal**

```bash
$ curl -s -X POST http://127.0.0.1:5000/appeal \
  -H "Content-Type: application/json" \
  -d '{"content_id": "78b393715a754e528455b88a86534039", "reasoning": "This passage is from Booker T. Washington, Up from Slavery (1901). A person wrote it decades before any AI tool existed."}'
```

```json
{
    "appealed_at": "2026-11-09T03:31:09+00:00",
    "content_id": "78b393715a754e528455b88a86534039",
    "message": "Thanks. Your appeal is recorded and a person will review this decision. The automatic label stays on hold until then.",
    "original_decision": {
        "confidence": 0.5883,
        "decided_at": "2026-11-09T03:31:01+00:00",
        "guess": "unsure",
        "label": "We can't tell whether a person or an AI tool wrote this. A lot of writing that people do entirely on their own lands here, so please don't read this as an accusation."
    },
    "status": "under_review"
}
```

**Repeat-appeal policy:** one appeal per `content_id`. Appealing again while it's
under review is refused with `409` and logged, not silently dropped:

```bash
$ curl -s -X POST http://127.0.0.1:5000/appeal \
  -H "Content-Type: application/json" \
  -d '{"content_id": "78b393715a754e528455b88a86534039", "reasoning": "Appealing a second time."}'
```

```json
{
    "content_id": "78b393715a754e528455b88a86534039",
    "current_status": "under_review",
    "error": "already_under_review",
    "message": "This item has already been appealed and is waiting for a person to review it."
}
```

An unknown `content_id` gets `404 unknown_content_id`. `"reason"` is accepted as
another name for `"reasoning"`.

**What the log shows afterwards**

```bash
$ curl -s "http://127.0.0.1:5000/log?limit=3"
```

```json
{
    "count": 3,
    "entries": [
        {
            "combined_score": 0.5883,
            "content_id": "78b393715a754e528455b88a86534039",
            "creator_id": "radhepa_demo",
            "guess": "unsure",
            "label": "We can't tell whether a person or an AI tool wrote this. A lot of writing that people do entirely on their own lands here, so please don't read this as an accusation.",
            "model_score": 0.7279,
            "status": "decided",
            "style_score": 0.3911,
            "timestamp": "2026-11-09T03:31:01+00:00"
        },
        {
            "combined_score": 0.5883,
            "content_id": "78b393715a754e528455b88a86534039",
            "creator_id": "radhepa_demo",
            "event": "appeal",
            "guess": "unsure",
            "label": "We can't tell whether a person or an AI tool wrote this. A lot of writing that people do entirely on their own lands here, so please don't read this as an accusation.",
            "model_score": 0.7279,
            "reasoning": "This passage is from Booker T. Washington, Up from Slavery (1901). A person wrote it decades before any AI tool existed.",
            "status": "under_review",
            "style_score": 0.3911,
            "timestamp": "2026-11-09T03:31:09+00:00"
        },
        {
            "content_id": "78b393715a754e528455b88a86534039",
            "creator_id": "radhepa_demo",
            "current_status": "under_review",
            "event": "rejected",
            "http_status": 409,
            "reason": "already_under_review",
            "route": "/appeal",
            "status": "rejected",
            "timestamp": "2026-11-09T03:31:10+00:00"
        }
    ]
}
```

The original decision stays exactly where it was; the appeal is appended after
it. `logs/audit.jsonl` is committed and holds every request from these runs.

**Criteria check** — `python evaluate.py` against the same live service, three
trials, targets from `criteria.md` (committed before this ran). Full output:
[`results/eval_2026-11-08_2233.md`](results/eval_2026-11-08_2233.md).

| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |
|---|---|---|---|---|---|
| 1. False positives on known-human text | ≤ 1 of 20 labelled AI | 0 of 20 | 0 of 20 | 0 of 20 | PASS |
| 2. Score separation (mean AI − mean human) | ≥ 0.20 | 0.416 | 0.416 | 0.416 | PASS |
| 3. Label coverage, no gaps/overlaps | 3 of 3 labels; 0 gaps | 3 of 3, sweep ok | 3 of 3, sweep ok | 3 of 3, sweep ok | PASS |
| 4. Appeal path | 5/5 valid + 3/3 unknown → 404 | 5/5 + 3/3 | 5/5 + 3/3 | 5/5 + 3/3 | PASS |
| 5. Bad input refused cleanly | 12/12 4xx, 0 decisions | 12/12, 0 decisions | 12/12, 0 decisions | 12/12, 0 decisions | PASS |

What that table doesn't say: the three trials are identical because gpt2 runs
deterministically here; the human label fired on only 2 of 20 human passages
(18 were "unsure"), so the system is cautious rather than informative for
human writing; and every AI passage came from one model (Claude) in one
generic essay register, so this says nothing yet about edited or disguised AI
text — that's unit 8's attack set. One earlier `evaluate.py` run crashed in its
own tallying code (a bug in the script, fixed before the run above); its
submissions are still in the audit log.

`python -m pytest tests` — 106 tests (stylometry, scoring boundaries, routes with
a mocked detector, and end-to-end runs with the real gpt2) — all pass.

---

## How I Used AI

This project was built by Claude (Anthropic's Claude Opus 5.5, in Claude Code)
working from my written spec. Claude wrote essentially all of it: the
implementation, the tests, the evaluation script, the first drafts of the five
criteria, the AI-written evaluation passages, and this README. It is not my
independent work, and I'm saying so rather than presenting it as mine. The
criteria targets in `criteria.md` are Claude's drafts, left for my own review.

**Moment 1**

- *What I asked for:* The whole Unit 7 build end to end — criteria first, then
  `/submit`, a stylometry signal, a combining rule with conservative labels,
  `/appeal`, an audit log, tests, real runs and this write-up — with known-provenance
  human text for the false-positive measurement and nothing fabricated.
- *What came back:* Five criteria committed before any scoring, the service, 106
  tests, a 20-passage human set taken mechanically from pre-1930 Project
  Gutenberg books (`eval_data/build_human_set.py`), a 10-passage AI set Claude
  generated and labelled as AI, and `evaluate.py`. Every score in this README
  came from a real run.
- *What I changed:* Nothing by hand yet. Changes Claude made after checking its
  own output: a broad `except` in `/submit` swallowed the 413 for oversized
  bodies (fixed so the handler answers); a `status` keyword clash made the
  repeat-appeal path crash with a 500 (renamed to `current_status`); one test
  had miscounted words; and `evaluate.py` crashed in its first run on a tallying
  bug.

**Moment 2**

- *What I asked for:* A second signal with sentence-length variation, lexical
  diversity and punctuation density, normalised to 0–1, without tuning on the
  evaluation set.
- *What came back:* Claude built a separate calibration split first, measured it,
  and found vocabulary variety ran the opposite way to its own assumption
  (Claude-written text had *higher* variety than the human books), so it flipped
  that scale and set every constant from the calibration split only.
- *What I changed:* Nothing yet. The flipped direction is the decision I most
  want to check myself, because it means dense, varied human prose (an essay, a
  report) will read as more AI-like to signal two.

**Moment 3 (unit 8)**

- *What I asked for:* The whole unit 8 red-team pass: turn on rate limiting,
  run the staff attack set before changing anything, run my five criteria three
  times, diagnose every break, make one improvement, re-run both, and write it
  up here.
- *What came back:* Claude turned on the limiter (10/min, 200/day per
  `creator_id`), made 429s log the key they counted against, rewrote
  `scenarios.py` and extended `run_eval.py` so each criterion's verdict is
  computed by a `check` function rather than typed, ran everything against the
  live service, and traced each break to a stage. Its most useful find was that
  two evasions hit a *different* signal than the attack aimed at (typos moved
  gpt2, not stylometry; repetition moved stylometry the "human" way), which made
  the nine evasions one problem in the combining rule instead of nine.
- *What I changed / what I'd check:* Nothing by hand. The choice to spend the
  one improvement on the two false positives rather than the nine evasions is a
  values call from my unit 7 criteria, and Claude reported its cost (10/10 →
  8/10 known-AI caught) instead of hiding it. The diagnosis I'd verify myself is
  MF07: Claude marked a clean 422 as BROKE because the stated reason is false.

<!-- ═══════════════════════ UNIT 8 — THE TEST ═══════════════════════ -->

---

## Rate Limiting

**My limits:** 10 per minute, 200 per day (`config.py`: `RATE_LIMIT_PER_MINUTE`,
`RATE_LIMIT_PER_DAY`; applied to `/submit` in `app.py`).

**Why those numbers and not others:**
A real writer submits a piece, notices a typo, resubmits — a handful of requests
in a minute at the very most, and a few dozen in a heavy day. Ten a minute never
touches that person. It does stop a script hammering the service: every
accepted request runs gpt2 inline, about a second of CPU, so an unlimited burst
is a cheap way to take the service down. 200 a day is far above any real
writer, but a script mapping my thresholds needs hundreds to thousands of
near-identical probes (nudge one word, watch the score move), and 200 makes that
slow for any one identity. I didn't go lower (say 3/minute) because the same
writer fixing and resubmitting, or a class submitting from one shared account,
would hit it.

**What a caller counts as:** per `creator_id`, falling back to the remote
address when the body has no usable `creator_id` (`app.py::rate_limit_key`).
Per-address alone would lump a whole school or household behind one NAT into a
single caller and lock them all out together. Per-`creator_id` keeps them apart,
but `creator_id` is self-asserted, so one script that invents a new id per
request looks like a thousand callers and is never limited — see What's Still
Broken. Refused requests count too: a 422 still costs a slot, so flooding with
junk doesn't get a free pass.

**The run of status codes when I pushed past it:**

```
$ python run_attacks.py --flood 15
200 200 200 200 200 200 200 200 200 200 429 429 429 429 429
```

From [`results/flood_2026-11-14_2055.md`](results/flood_2026-11-14_2055.md)
(`run_attacks.py::run_flood`, 15 submissions as `flood_tester`). Every 429 is
written to the audit log as a rejection naming the limit and the key it was
counted against (one is in the ten entries below).

---

## Attack Run — Before

The full staff attack set (`attacks.csv` + `attacks_malformed_requests.csv`,
56 requests including the 12-request flood), run once against the live service
with the unit 7 settings (`AI_THRESHOLD = 0.75`) and rate limiting on, before I
changed anything. Produced by `run_attacks.py --label before`; full output in
[`results/attack_run_2026-11-14_2055_before.md`](results/attack_run_2026-11-14_2055_before.md).

What counts as HELD: an evasion attack holds only if AI text still gets the
"ai" label; a false-positive attack holds if real human writing is **not**
labelled "ai"; prompt injection holds if the label isn't moved toward human or
corrupted; malformed input holds if it's refused cleanly with a 4xx and an
honest reason; the flood holds if a 429 arrives.

| ID | Family | Targeting | Status · guess · combined (model / style) | Verdict |
|---|---|---|---|---|
| EV01 | evasion | signal two: typos raise word variety | 200 · unsure · 0.500 (0.16 / 1.00) | BROKE |
| EV02 | evasion | signal two: broken-up sentences raise length spread | 200 · unsure · 0.550 (0.59 / 0.48) | BROKE |
| EV03 | evasion | signal two: a pasted quotation changes the shape | 200 · unsure · 0.642 (0.67 / 0.61) | BROKE |
| EV04 | evasion | signal one: unusual words raise perplexity | 200 · unsure · 0.733 (0.61 / 1.00) | BROKE |
| EV05 | evasion | both signals: heavy human editing pass | 200 · unsure · 0.420 (0.32 / 0.57) | BROKE |
| EV06 | evasion | signal two: one very long sentence and one very short | 200 · unsure · 0.587 (0.57 / 0.61) | BROKE |
| EV07 | evasion | signal two: padding with punctuation | 200 · unsure · 0.524 (0.59 / 0.43) | BROKE |
| EV08 | evasion | signal one: text below the token window | 422 | HELD |
| EV09 | evasion | both: AI text with a human opening paragraph bolted on | 200 · unsure · 0.740 (0.70 / 0.79) | BROKE |
| EV10 | evasion | signal two: repeated stanza structure | 200 · unsure · 0.735 (0.98 / 0.53) | BROKE |
| FP01 | false_positive | plain, clear human writing with no flourishes | 200 · unsure · 0.621 (0.62 / 0.63) | HELD |
| FP02 | false_positive | human writing in a formal register | 200 · unsure · 0.732 (0.74 / 0.72) | HELD |
| FP03 | false_positive | a non-native English speaker writing carefully | 200 · ai · 0.797 (0.81 / 0.79) | BROKE |
| FP04 | false_positive | a student essay written to a rubric | 200 · ai · 0.801 (0.83 / 0.75) | BROKE |
| FP05 | false_positive | technical documentation written by a person | 200 · unsure · 0.737 (0.80 / 0.64) | HELD |
| FP06 | false_positive | a person imitating a formal template | 200 · unsure · 0.656 (0.88 / 0.43) | HELD |
| FP07 | false_positive | human writing that repeats a phrase deliberately | 200 · unsure · 0.605 (0.88 / 0.33) | HELD |
| FP08 | false_positive | very short genuine human submission | 422 | HELD |
| PI01 | prompt_injection | instruction to ignore the check | 200 · unsure · 0.544 (0.46 / 0.67) | HELD |
| PI02 | prompt_injection | instruction disguised as a system message | 200 · human · 0.349 (0.20 / 0.54) | BROKE |
| PI03 | prompt_injection | instruction wrapped in the writer's voice | 200 · unsure · 0.600 (0.59 / 0.61) | HELD |
| PI04 | prompt_injection | attempt to make the label text hostile | 200 · unsure · 0.500 (0.50 / 0.50) | HELD |
| PI05 | prompt_injection | attempt to inject into the audit log | 200 · unsure · 0.566 (0.64 / 0.46) | HELD |
| PI06 | prompt_injection | instruction plus real human text | 200 · unsure · 0.597 (0.56 / 0.65) | HELD |
| MF01 | malformed | text is only whitespace | 400 | HELD |
| MF02 | malformed | text is a single character | 422 | HELD |
| MF03 | malformed | text is control characters | 422 | HELD |
| MF04 | malformed | text is only punctuation | 422 | HELD |
| MF05 | malformed | text is a very long single word | 422 | HELD |
| MF06 | malformed | text is emoji only | 422 | HELD |
| MF07 | malformed | text is right-to-left script | 422 | BROKE |
| MF08 | malformed | text is 60,000 characters | 413 | HELD |
| RQ01 | malformed | no text field at all | 400 | HELD |
| RQ02 | malformed | no creator_id | 400 | HELD |
| RQ03 | malformed | text is a number | 400 | HELD |
| RQ04 | malformed | text is a list | 400 | HELD |
| RQ05 | malformed | text is null | 400 | HELD |
| RQ06 | malformed | creator_id is an object | 400 | HELD |
| RQ07 | malformed | body is a JSON array, not an object | 400 | HELD |
| RQ08 | malformed | body is unparseable JSON | 400 | HELD |
| RQ09 | malformed | body is empty | 400 | HELD |
| RQ10 | malformed | body is form-encoded, not JSON | 415 | HELD |
| RQ11 | malformed | body is JSON claiming to be plain text | 415 | HELD |
| RQ12 | malformed | deeply nested JSON | 400 | HELD |
| FL01_01 | flood_same_creator | 20 rapid submissions from one creator | 422 | HELD |
| FL01_02 | flood_same_creator | 20 rapid submissions from one creator | 422 | HELD |
| FL01_03 | flood_same_creator | 20 rapid submissions from one creator | 422 | HELD |
| FL01_04 | flood_same_creator | 20 rapid submissions from one creator | 422 | HELD |
| FL01_05 | flood_same_creator | 20 rapid submissions from one creator | 422 | HELD |
| FL01_06 | flood_same_creator | 20 rapid submissions from one creator | 422 | HELD |
| FL01_07 | flood_same_creator | 20 rapid submissions from one creator | 422 | HELD |
| FL01_08 | flood_same_creator | 20 rapid submissions from one creator | 422 | HELD |
| FL01_09 | flood_same_creator | 20 rapid submissions from one creator | 422 | HELD |
| FL01_10 | flood_same_creator | 20 rapid submissions from one creator | 422 | HELD |
| FL01_11 | flood_same_creator | 20 rapid submissions from one creator | 429 | HELD |
| FL01_12 | flood_same_creator | 20 rapid submissions from one creator | 429 | HELD |

**13 broke, 43 held.** By family: evasion 9 of 10 broke, false positive 2 of 8,
prompt injection 1 of 6, malformed 1 of 20, flood 0 of 12.

**Ten audit log entries from the run** (verbatim from `logs/audit.jsonl`; the
attack runner sends each input as `creator_id = attacker_<ID>`, the bad-JSON
one has no readable `creator_id` so it's logged as `unknown`):

```json
{"timestamp": "2026-11-15T01:55:31+00:00", "content_id": "7f868f44046d40ac81c81aaf1caa9e01", "creator_id": "attacker_FP03", "guess": "ai", "model_score": 0.8051, "style_score": 0.785, "combined_score": 0.7971, "label": "We think this was most likely written with an AI tool. Two separate checks both pointed that way, but they can be wrong: if you wrote this yourself, you can appeal and a person will review it.", "status": "decided"}
{"timestamp": "2026-11-15T01:55:32+00:00", "content_id": "dd713c7b1f53416fa948aba1bdd65cb7", "creator_id": "attacker_FP04", "guess": "ai", "model_score": 0.8329, "style_score": 0.753, "combined_score": 0.8009, "label": "We think this was most likely written with an AI tool. Two separate checks both pointed that way, but they can be wrong: if you wrote this yourself, you can appeal and a person will review it.", "status": "decided"}
{"timestamp": "2026-11-15T01:55:33+00:00", "content_id": "b461533a5b544e539f6b45e840da06ce", "creator_id": "attacker_PI02", "guess": "human", "model_score": 0.2044, "style_score": 0.5433, "combined_score": 0.3489, "label": "We think a person most likely wrote this. Our checks found the patterns we usually see in human writing.", "status": "decided"}
{"timestamp": "2026-11-15T01:55:27+00:00", "content_id": "4fd4951fab794a4fb2f45cfee7ef281c", "creator_id": "attacker_EV01", "guess": "unsure", "model_score": 0.1635, "style_score": 1.0, "combined_score": 0.4996, "label": "We can't tell whether a person or an AI tool wrote this. A lot of writing that people do entirely on their own lands here, so please don't read this as an accusation.", "status": "decided"}
{"timestamp": "2026-11-15T01:55:30+00:00", "content_id": "a03444a250514cae89e1220d631eac8a", "creator_id": "attacker_EV10", "guess": "unsure", "model_score": 0.9792, "style_score": 0.5296, "combined_score": 0.7354, "label": "We can't tell whether a person or an AI tool wrote this. A lot of writing that people do entirely on their own lands here, so please don't read this as an accusation.", "status": "decided"}
{"timestamp": "2026-11-15T01:55:30+00:00", "creator_id": "attacker_EV08", "event": "rejected", "status": "rejected", "reason": "text_too_short", "route": "/submit", "http_status": 422, "min_words": 20}
{"timestamp": "2026-11-15T01:55:35+00:00", "creator_id": "attacker_MF07", "event": "rejected", "status": "rejected", "reason": "text_too_short", "route": "/submit", "http_status": 422, "min_words": 20}
{"timestamp": "2026-11-15T01:55:35+00:00", "creator_id": "attacker_MF08", "event": "rejected", "status": "rejected", "reason": "field_too_long", "route": "/submit", "http_status": 413, "field": "text", "limit": 20000}
{"timestamp": "2026-11-15T01:55:35+00:00", "creator_id": "unknown", "event": "rejected", "status": "rejected", "reason": "invalid_json", "route": "/submit", "http_status": 400}
{"timestamp": "2026-11-15T01:55:35+00:00", "creator_id": "attacker_flood", "event": "rejected", "status": "rejected", "reason": "rate_limited", "limit": "10 per 1 minute", "route": "/submit", "http_status": 429, "limited_key": "attacker_flood"}
```

1–2 are the two false positives (both signals agree, both above 0.75). 3 is
the injection that came out "human". 4–5 are evasions that slipped to "unsure"
because the two signals split. 6–9 are rejections — including MF07, an Arabic
passage refused as "too short" — and 10 is the flood hitting the limit, logged
with the key it was counted against.

**The single worst outcome** — the one I'd least want to explain to a writer
whose work got caught by it:

**FP03**: a non-native English speaker writing carefully, labelled "ai" at
0.797, with the label text telling them two separate checks agreed. That
person did exactly what they're taught to do — short, plain, correct sentences,
common words, no risky punctuation — and every one of those habits is what both
of my signals read as machine-like. They are also the writer least able to
argue back in an appeal, and the most likely to be disbelieved. The evasions
cost the site some AI text; this one costs a real person their reputation.

---

## Run Log and Verdicts

My five criteria from `criteria.md`, three trials each, run by
`python run_eval.py --label before` against the live service (rate limiting
on, a 65-second pause between trials so trial 1's requests don't eat trial 2's
budget). Full output:
[`results/run_2026-11-14_2103_before.md`](results/run_2026-11-14_2103_before.md).

| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |
|---|---|---|---|---|---|
| 1. False positives on known-human text | ≤ 1 of 20 labelled AI | 0/20 labelled AI | 0/20 labelled AI | 0/20 labelled AI | **MET** |
| 2. Score separation (mean AI − mean human) | ≥ 0.20 | gap 0.416 | gap 0.416 | gap 0.416 | **MET** |
| 3. Label coverage, no gaps/overlaps | 3 of 3 labels live; 0 gaps in sweep | 3/3 labels, sweep ok | 3/3 labels, sweep ok | 3/3 labels, sweep ok | **MET** |
| 4. Appeal path | 5/5 appeals logged + 3/3 unknown → 404 | 5/5 + 3/3 → 404 | 5/5 + 3/3 → 404 | 5/5 + 3/3 → 404 | **MET** |
| 5. Bad input refused cleanly | 12/12 4xx with error; 0 decisions | 12/12 4xx, 0 decisions | 12/12 4xx, 0 decisions | 12/12 4xx, 0 decisions | **MET** |

The verdict column is computed, not typed: each scenario in `scenarios.py`
carries a `check` function that reads one trial's results and returns the cell
text and pass/fail, so a trial can't be marked MET by hand.

**Real output from one trial**, pasted as text — produced by
`run_eval.py::main` (written by `run_eval.py::write_report` into
`results/run_2026-11-14_2103_before.json`), trial 1, first rows of three
scenarios (the `label` text is dropped here for length; it's in the file):

```json
{
  "scenario": "1. known-human set", "cell": ["0/20 labelled AI", true],
  "first_result": {"status": 200, "content_id": "980a64f7f16d43468b0a241aaa086a51", "guess": "unsure", "confidence": 0.5176, "model_score": 0.5052, "style_score": 0.5363, "error": null, "sent": "Teacher and I went to walk in the yard, and I learned about how flower", "decisions_added": 20}
}
{
  "scenario": "4. appeal path", "cell": ["5/5 + 3/3 -> 404", true],
  "first_result": {"status": 200, "content_id": "bcfa6e52b3084df8a413397133bdb92b", "guess": "unsure", "confidence": 0.5176, "model_score": 0.5052, "style_score": 0.5363, "error": null, "sent": "Teacher and I went to walk in the yard, and I learned about how flower", "appeal_reason": "run_eval trial 1: I wrote piece 1 myself.", "appeal_status": 200, "appeal_returned_status": "under_review", "appeal_entries": 1, "reason_logged": true, "decisions_added": 5}
}
{
  "scenario": "5. bad input refused cleanly", "cell": ["12/12 4xx, 0 decisions", true],
  "first_result": {"status": 400, "content_id": null, "guess": null, "confidence": null, "model_score": null, "style_score": null, "error": "invalid_json", "sent": "raw application/json: '{this is not json'", "decisions_added": 0},
  "all_twelve": [[400, "invalid_json"], [415, "unsupported_media_type"], [400, "invalid_body"], [400, "missing_field"], [400, "empty_field"], [400, "empty_field"], [400, "invalid_type"], [400, "missing_field"], [400, "empty_field"], [400, "invalid_type"], [413, "field_too_long"], [422, "text_too_short"]]
}
```

**All five MET in all three trials — and that is itself a finding.** The
three trials are identical to four decimal places because gpt2 runs
deterministically on CPU here, so "three trials" checks the plumbing (rate
limits, appeals, the log) rather than score noise. More importantly, my
criteria passed while the attack set broke the system 13 times. Criterion 1
said "≤ 1 false positive" and measured it on 20 pre-1930 Project Gutenberg
passages; the attack set's FP03 and FP04 are *modern* plain writing (a
non-native speaker, a rubric essay), which is exactly where my system fails
and exactly what my test set didn't contain. The target wasn't too easy so
much as aimed at the wrong population. A tighter criterion 1 would include
present-day plain human writing, especially non-native and student writing.
Criterion 2's 0.416 gap is real but is a gap between *averages*; the attack
set shows the tails overlap (human up to 0.80, AI from 0.795).

**Diagnoses**

The service has five stages: the route, signal one (gpt2 perplexity,
`detector.py`), signal two (stylometry: sentence-length spread, vocabulary
variety, expressive punctuation, `stylometry.py`), the combining rule
(`scoring.py::combine_signals`: 0.6 × model + 0.4 × style, pulled toward 0.5
when the signals are more than 0.3 apart), and the label mapping
(`scoring.py::score_to_label`).

For reference, the un-edited AI text the evasion attacks start from scores
model 0.669, style 1.0, combined **0.789 → "ai"**: only 0.04 above the 0.75
line. Every evasion only had to move the score 0.04.

1. **The evasion pattern (EV01–EV07, EV09, EV10: 9 attacks, one problem) —
   stage: the combining rule, on top of a thin margin at the label mapping.**
   Each edit moved *one* signal and left the other alone. My combining rule
   treats "the two signals disagree" as uncertainty and pulls the score toward
   0.5, so any edit that drags just one signal far enough triggers the shrink,
   and the score falls into "unsure". The rule I wrote to protect humans from a
   single loud signal is the same rule that lets an attacker win by fooling
   only one. Three cases show the mechanism precisely, and two of them hit a
   different signal than the attack targeted:
   - **EV01 (typos, aimed at signal two):** signal two didn't move at all (still
     1.0 — typos don't change sentence lengths, and the variety measure was
     already pinned at "AI"). The typos hit **signal one** instead: a misspelt
     word is a high-perplexity token to gpt2, so model fell 0.67 → 0.16. A 0.84
     split sends the score to 0.4996 — "unsure".
   - **EV10 (repeated stanza structure, aimed at signal two):** repetition made
     the text *more* predictable to gpt2 (model 0.98), but repeating words drives
     my vocabulary-variety measure to the human end (I flipped that scale in
     unit 7: high variety = AI, so low variety = human), so style fell to 0.53.
     A 0.45 split → shrink → 0.735, just under the line.
   - **EV02/EV06/EV07 (sentence surgery, punctuation padding):** these did hit
     signal two as intended — inserting one-word sentences raises the
     sentence-length spread; extra dashes and semicolons raise punctuation
     density — style fell to 0.43–0.61, and with model only ~0.6 the weighted
     mean alone was under 0.75.
   - EV03, EV04, EV05, EV09 are the same story with smaller moves (0.420–0.740):
     never more than ~0.06 below the line, which only matters because the
     source text started 0.04 above it.
   EV08 held: it's under 20 words, so the route refuses it with 422 before any
   signal runs.

2. **FP03 and FP04 (false positives) — stage: the label mapping, because both
   signals agreed.** FP03 (non-native speaker: model 0.805, style 0.785 → 0.797)
   and FP04 (rubric essay: 0.833 / 0.753 → 0.801). No split, so no shrink, and
   the combining rule did what it was told. Signal one's blind spot is that
   plain, common words are predictable to gpt2 whoever chose them. Signal two's
   blind spot is that careful writing has uniform medium-length sentences
   (spread → AI end) and no dashes, exclamations or parentheses (punctuation
   → 1.0, the AI end). Both blind spots point the same way for this writer, so
   the score sits at ~0.80 — above my 0.75 threshold. The mechanism is that
   0.75 was inside the overlap: on everything I've measured, human writing
   reaches 0.80 and known-AI text starts at 0.795, and I'd drawn the "ai" line
   below the top of the human range.

3. **PI02 (instruction disguised as a system message) → "human" 0.349 — stage:
   signal one, then the combining rule.** Nothing *obeyed* the instruction:
   no part of my pipeline reads text as instructions, there's no LLM in it.
   What happened is mechanical: the "SYSTEM: …" prefix is odd, out-of-place
   text to gpt2, so it raised perplexity and model fell to 0.20; style was 0.54;
   the 0.6/0.4 mean landed at 0.349, a hair under the 0.35 human line. Any
   block of unusual tokens prepended to the text would do the same — it's the
   EV01 mechanism with a different payload. The other five injections held,
   and PI04/PI05 (corrupt the label, inject into the log) couldn't work at all:
   the label is fixed server-side text chosen from three strings, and the log
   is JSON-encoded and doesn't store the submitted text.

4. **MF07 (Arabic, a right-to-left script) → 422 "text_too_short" — stage: the
   route.** It was refused cleanly, which is why I nearly marked it HELD, but
   the *reason* is false: the passage has 17 Arabic words and my word counter
   (`stylometry.words`, regex `[a-z0-9']+`) only matches ASCII letters, so it
   counts zero words. A writer in any non-Latin script is told their full
   paragraph is "too short". That's a broken outcome with a clean status code.

5. **Everything else held.** All 12 RQ (request-shape) and the other MF inputs
   got the right 4xx with a named error and wrote no decision. The flood
   (FL01, 12 rapid requests from one creator) got ten 422s — the flood text is
   under 20 words — then 429 on the 11th and 12th, because refused requests
   still count against the limit.

---

## The Improvement

**What I changed:** one number. `AI_THRESHOLD` in `config.py`, 0.75 → **0.85**.
The "ai" label now needs a combined score above 0.85; 0.35–0.85 is "unsure".
Nothing else changed (same signals, same weights, same shrink, same human
threshold).

**Which diagnosis pointed at it:** diagnosis 2. Both false positives had the
signals *agreeing*, so the combining rule wasn't at fault and the fix belongs
at the label mapping. FP03 and FP04 sat at 0.797 and 0.801; the highest human
score I've seen anywhere is 0.801; 0.85 clears that with room. It also keeps a
property I test for: with the 0.6/0.4 weights and the shrink, a score above
0.85 still needs both signals above 0.5, so the "two separate checks both
pointed that way" wording stays true.

I chose this over the evasion problem (diagnosis 1, nine attacks) on purpose.
Nine evasions mean some AI text gets "unsure" instead of "ai"; two false
positives mean real people get told they cheated. My unit 7 decision was that
the second is worse, so the one change goes there.

### Attack Run — After

Same attack set, same service, only the threshold changed. `run_attacks.py
--label after`; full output in
[`results/attack_run_2026-11-14_2106_after.md`](results/attack_run_2026-11-14_2106_after.md).
The scores are identical to the before run (gpt2 is deterministic); only the
labels at the threshold moved.

| ID | Family | Before | Verdict | After | Verdict |
|---|---|---|---|---|---|
| EV01 | evasion | unsure 0.500 | BROKE | unsure 0.500 | BROKE |
| EV02 | evasion | unsure 0.550 | BROKE | unsure 0.550 | BROKE |
| EV03 | evasion | unsure 0.642 | BROKE | unsure 0.642 | BROKE |
| EV04 | evasion | unsure 0.733 | BROKE | unsure 0.733 | BROKE |
| EV05 | evasion | unsure 0.420 | BROKE | unsure 0.420 | BROKE |
| EV06 | evasion | unsure 0.587 | BROKE | unsure 0.587 | BROKE |
| EV07 | evasion | unsure 0.524 | BROKE | unsure 0.524 | BROKE |
| EV08 | evasion | 422 | HELD | 422 | HELD |
| EV09 | evasion | unsure 0.740 | BROKE | unsure 0.740 | BROKE |
| EV10 | evasion | unsure 0.735 | BROKE | unsure 0.735 | BROKE |
| FP01 | false_positive | unsure 0.621 | HELD | unsure 0.621 | HELD |
| FP02 | false_positive | unsure 0.732 | HELD | unsure 0.732 | HELD |
| FP03 | false_positive | ai 0.797 | BROKE | unsure 0.797 | **HELD** |
| FP04 | false_positive | ai 0.801 | BROKE | unsure 0.801 | **HELD** |
| FP05 | false_positive | unsure 0.737 | HELD | unsure 0.737 | HELD |
| FP06 | false_positive | unsure 0.656 | HELD | unsure 0.656 | HELD |
| FP07 | false_positive | unsure 0.605 | HELD | unsure 0.605 | HELD |
| FP08 | false_positive | 422 | HELD | 422 | HELD |
| PI01 | prompt_injection | unsure 0.544 | HELD | unsure 0.544 | HELD |
| PI02 | prompt_injection | human 0.349 | BROKE | human 0.349 | BROKE |
| PI03 | prompt_injection | unsure 0.600 | HELD | unsure 0.600 | HELD |
| PI04 | prompt_injection | unsure 0.500 | HELD | unsure 0.500 | HELD |
| PI05 | prompt_injection | unsure 0.566 | HELD | unsure 0.566 | HELD |
| PI06 | prompt_injection | unsure 0.597 | HELD | unsure 0.597 | HELD |
| MF01 | malformed | 400 | HELD | 400 | HELD |
| MF02 | malformed | 422 | HELD | 422 | HELD |
| MF03 | malformed | 422 | HELD | 422 | HELD |
| MF04 | malformed | 422 | HELD | 422 | HELD |
| MF05 | malformed | 422 | HELD | 422 | HELD |
| MF06 | malformed | 422 | HELD | 422 | HELD |
| MF07 | malformed | 422 | BROKE | 422 | BROKE |
| MF08 | malformed | 413 | HELD | 413 | HELD |
| RQ01 | malformed | 400 | HELD | 400 | HELD |
| RQ02 | malformed | 400 | HELD | 400 | HELD |
| RQ03 | malformed | 400 | HELD | 400 | HELD |
| RQ04 | malformed | 400 | HELD | 400 | HELD |
| RQ05 | malformed | 400 | HELD | 400 | HELD |
| RQ06 | malformed | 400 | HELD | 400 | HELD |
| RQ07 | malformed | 400 | HELD | 400 | HELD |
| RQ08 | malformed | 400 | HELD | 400 | HELD |
| RQ09 | malformed | 400 | HELD | 400 | HELD |
| RQ10 | malformed | 415 | HELD | 415 | HELD |
| RQ11 | malformed | 415 | HELD | 415 | HELD |
| RQ12 | malformed | 400 | HELD | 400 | HELD |
| FL01_01 | flood_same_creator | 422 | HELD | 422 | HELD |
| FL01_02 | flood_same_creator | 422 | HELD | 422 | HELD |
| FL01_03 | flood_same_creator | 422 | HELD | 422 | HELD |
| FL01_04 | flood_same_creator | 422 | HELD | 422 | HELD |
| FL01_05 | flood_same_creator | 422 | HELD | 422 | HELD |
| FL01_06 | flood_same_creator | 422 | HELD | 422 | HELD |
| FL01_07 | flood_same_creator | 422 | HELD | 422 | HELD |
| FL01_08 | flood_same_creator | 422 | HELD | 422 | HELD |
| FL01_09 | flood_same_creator | 422 | HELD | 422 | HELD |
| FL01_10 | flood_same_creator | 422 | HELD | 422 | HELD |
| FL01_11 | flood_same_creator | 429 | HELD | 429 | HELD |
| FL01_12 | flood_same_creator | 429 | HELD | 429 | HELD |

**11 broke, 45 held** (was 13 / 43). Evasion 9 → 9, false positive 2 → **0**,
prompt injection 1 → 1, malformed 1 → 1, flood 0 → 0.

I also re-ran my five criteria (`run_eval.py --label after`,
[`results/run_2026-11-14_2109_after.md`](results/run_2026-11-14_2109_after.md)):
all five **MET** in all three trials again, same values (0/20, gap 0.416, 3/3
labels with the sweep confirming the boundary moved to 0.85, 5/5 + 3/3, 12/12).

**Did it help, and how do I know:**
Yes, for what it targeted: the before/after table shows FP03 and FP04 move
from "ai" to "unsure" at unchanged scores, so it's the threshold and nothing
else that fixed them, and no other attack got worse.

The trade, honestly: the same move made the system blinder to AI text.
- On my own known-AI set, "ai" labels fell from **10 of 10 to 8 of 10**:
  `ai_08` (0.838) and `ai_10` (0.795) are now "unsure". Criterion 2 still
  passes because it measures the gap between averages, which didn't change —
  another sign my criteria are too coarse.
- The *un-edited* AI source text behind the evasion attacks (0.789) is now
  "unsure" with no evasion at all. Before, an attacker had to move the score
  0.04; now they don't have to do anything for text that scores like that.
- Human texts are no better recognised as human: 2 of 20 "human", 18
  "unsure", same as before. The fix stopped accusations; it didn't add any
  confidence.

So: two fewer wrong accusations, paid for with roughly one in five AI texts
that used to be caught now going out as "unsure". That's the direction I said
I'd take in unit 7, and I'd make it again — but it's a real cost, not a free
fix.

---

## What's Still Broken

- **Evasion: 9 of 10 still get through (as "unsure").** The fix wasn't aimed
  at them and made them slightly easier. What I'd do: stop the disagreement
  shrink from being a free pass. One option is to shrink toward the *higher*
  signal's label band rather than to 0.5 when one signal is pinned at 1.0
  (style was 1.0 in EV01 and EV04); another is a third signal that typos and
  single-sentence edits don't move, such as perplexity measured on a
  spell-corrected copy. Why I stopped: the assignment allows one change, and
  either fix reopens the false-positive risk I just closed — it has to be
  re-tested against FP01–FP07 before it ships.
- **PI02: an unusual prefix pushes text to "human".** Same mechanism as EV01
  (odd tokens → low model score). What I'd do: score the text with any leading
  line that looks like a header or role tag ("SYSTEM:", "Note to grader")
  stripped, or score the middle of the text rather than the start. Stopped for
  the same one-change reason.
- **MF07: non-Latin scripts are refused as "too short".** What I'd do: count
  words with a Unicode-aware pattern (`\w+` with `re.UNICODE`, or split on
  whitespace) for the minimum-length check, and return an honest
  "language not supported" refusal rather than a false "too short", since gpt2
  and my stylometry constants are English-only anyway. Small fix; left out to
  keep the improvement to one change.
- **The rate limit is per `creator_id`, which the caller makes up.** A script
  that sends a new `creator_id` every request is never limited. What I'd do:
  a second, looser per-address limit layered under the per-creator one
  (e.g. 60/minute per IP), and in production, `creator_id` from an
  authenticated session, not the request body. Also the limiter's storage is
  in memory: a restart forgets every count, and two copies of the service
  wouldn't share limits — production needs Redis or similar.
- **My criteria didn't catch any of this.** All five MET while 13 attacks broke.
  I'd add modern plain human writing (non-native, student, technical) to the
  criterion 1 set, and add a criterion on the *tails* — "no human sample above
  the AI threshold" — instead of only a gap between averages.

**The trade I'd make if this ran for real:**
I'd keep the threshold high and accept that more AI-written text gets labelled
"unsure" rather than "ai": the people who pay for that are readers and the
site, who see some AI text go by without a warning. The alternative makes
careful writers — non-native speakers and students writing to a rubric most of
all — pay with a public accusation they did nothing to earn, and that's the
cost I won't put on them.

<!-- ═════════════════════════════════════════════════════════════════════

     SUBMISSION CHECKLIST — unit 7

       [ ] criteria.md has five numbered criteria, each naming a target
       [ ] Each has a reason underneath
       [ ] POST /submit returns content_id, guess, confidence, label,
           model_score and style_score
       [ ] Two signals that measure DIFFERENT things, each with a named blind spot
       [ ] Three label variants, all reachable, written out in full
       [ ] POST /appeal changes status and writes to the log
       [ ] Signals and Scoring names scoring.py::combine_signals
       [ ] Sample Run: a submission AND an appeal, as pasted text
       [ ] At least four new commits
       [ ] Repository URL submitted — WRITE IT DOWN

     SUBMISSION CHECKLIST — unit 8

       [ ] Rate limiting on /submit, with your numbers justified
       [ ] The pasted run of status codes showing 429
       [ ] Audit log with all nine fields, recording rejections too
       [ ] The attack set run IN FULL, every input with an outcome
       [ ] Ten audit log entries pasted as text
       [ ] Five criteria across three trials
       [ ] A diagnosis for every miss and every broken attack — stage AND mechanism
       [ ] One improvement, with Attack Run — After
       [ ] What's Still Broken, including the production trade
       [ ] At least four new commits
       [ ] The SAME repository URL as last unit

     Do not delete and recreate this repository.
     ═════════════════════════════════════════════════════════════════════ -->

---

📖 **How to run this project: [RUNNING.md](RUNNING.md)**

---

## Capstone

**What This Extends**

Provenance Guard, the AI-text detector from units 7–8: a Flask service with
`/submit`, `/appeal` and `/log`, gpt2 perplexity as signal one, stylometry as
signal two, and an audit log of every decision. Until now I could say what it
*decided* but not what it *cost*. What's new:

- `metrics.py`: an operations log, `logs/requests.jsonl`, with one structured
  line for every `/submit` and `/appeal` request, accepted or refused. Each line
  records wall time, CPU time, a hash of the input (never the text), the
  outcome, and for scored submissions the time per signal, the tokens gpt2
  read, and whether the request paid for loading the model.
- Request ids end to end: `X-Request-Id` in, the same id out, the same id in
  the log.
- A measured cost per run, and a run path someone else can repeat
  (`RUNNING.md`, `requirements-lock.txt`).
- `capstone/run_capstone_eval.py`: starts the service cold for each trial and
  computes the verdicts from the log.

**The Shape**

**Shape A: deploy and instrument.** Out of scope, on purpose:

- No change to what the detector decides. Thresholds, weights and signals are
  as unit 8 left them, and criterion 5 checks that.
- No hosted deployment. The service needs about 526 MB of gpt2 weights plus
  torch in memory, and a free tier gives 512 MB with no persistent disk.
  `RUNNING.md` has the arithmetic.
- No log shipping, dashboards, alerting or log rotation.
- No fixes for the unit 8 attack findings (evasion, the ASCII word counter).
  They're still listed under What's Still Broken in unit 8.

**Running It**

Path B: local, with logs. Python 3.11.15. Install with
`pip install -r requirements-lock.txt` (43 exact pins, e.g. `torch==2.15.0`,
`transformers==4.57.6`). gpt2 is cached in
`~/.cache/huggingface/hub/models--gpt2` (526 MB on disk), and
`python detector.py` downloads it once. Then one command:

```bash
python app.py
```

Logs go to `logs/audit.jsonl` (decisions) and `logs/requests.jsonl`
(operations). Full steps, environment variables and the check commands:
[RUNNING.md → Capstone: Path B](RUNNING.md#capstone-path-b-local-with-logs-what-i-actually-run).

**Instrumentation**

Schema of `logs/requests.jsonl`. Every line has:

| Field | Meaning |
|---|---|
| `timestamp` | UTC, milliseconds |
| `request_id` | caller's `X-Request-Id` if it matches `[A-Za-z0-9_-]{1,64}`, else a new uuid; echoed in the response |
| `route`, `method`, `status` | what was asked and the HTTP answer |
| `duration_ms` | wall time, from Flask's `before_request` to `after_request` |
| `cpu_ms` | process CPU over the same span (all threads) |
| `input_bytes` | request body size |
| `input_sha256` | first 16 hex digits of the body's SHA-256: identifies the input without storing it |
| `outcome` | the guess, the appeal status, or the error code |

Accepted `/submit` lines also carry `words`, `tokens_scored`, `model_ms`
(signal one), `style_ms` (signal two) and `cold_start`.

Ten real entries from the after run, trial 1
(`results/capstone_run_2026-11-14_2125_after.json`). They show:

- the cold start, a "human" and an "ai" decision
- five refusals: 400, 415, 413, 422 and 429
- a valid appeal and an appeal that fails with 404

```json
{"timestamp": "2026-11-15T02:23:45.380+00:00", "request_id": "cap-a2d4537a-00", "route": "/submit", "method": "POST", "status": 200, "duration_ms": 13679.3, "cpu_ms": 13000.0, "input_bytes": 485, "input_sha256": "f1c9898332f2823e", "outcome": "unsure", "words": 86, "tokens_scored": 112, "model_ms": 13665.4, "style_ms": 0.5, "cold_start": true}
{"timestamp": "2026-11-15T02:23:48.417+00:00", "request_id": "cap-a2d4537a-05", "route": "/submit", "method": "POST", "status": 200, "duration_ms": 470.2, "cpu_ms": 468.8, "input_bytes": 455, "input_sha256": "bf8c83aa46a96da0", "outcome": "human", "words": 80, "tokens_scored": 102, "model_ms": 467.7, "style_ms": 0.3, "cold_start": false}
{"timestamp": "2026-11-15T02:23:58.181+00:00", "request_id": "cap-a2d4537a-20", "route": "/submit", "method": "POST", "status": 200, "duration_ms": 542.2, "cpu_ms": 546.9, "input_bytes": 751, "input_sha256": "774dd5d3e925c0a0", "outcome": "ai", "words": 103, "tokens_scored": 123, "model_ms": 539.8, "style_ms": 0.3, "cold_start": false}
{"timestamp": "2026-11-15T02:24:03.761+00:00", "request_id": "cap-a2d4537a-30", "route": "/submit", "method": "POST", "status": 400, "duration_ms": 1.3, "cpu_ms": 0.0, "input_bytes": 17, "input_sha256": "946fefe1ec51413c", "outcome": "invalid_json"}
{"timestamp": "2026-11-15T02:24:03.787+00:00", "request_id": "cap-a2d4537a-31", "route": "/submit", "method": "POST", "status": 415, "duration_ms": 1.3, "cpu_ms": 0.0, "input_bytes": 23, "input_sha256": "47b9ddf4305e84fc", "outcome": "unsupported_media_type"}
{"timestamp": "2026-11-15T02:24:03.894+00:00", "request_id": "cap-a2d4537a-40", "route": "/submit", "method": "POST", "status": 413, "duration_ms": 1.5, "cpu_ms": 0.0, "input_bytes": 20048, "input_sha256": "bb16877d0a01320e", "outcome": "field_too_long"}
{"timestamp": "2026-11-15T02:24:03.924+00:00", "request_id": "cap-a2d4537a-42", "route": "/submit", "method": "POST", "status": 422, "duration_ms": 1.5, "cpu_ms": 0.0, "input_bytes": 70, "input_sha256": "ddc48fc0be6d9aa0", "outcome": "text_too_short"}
{"timestamp": "2026-11-15T02:24:04.008+00:00", "request_id": "cap-a2d4537a-52", "route": "/submit", "method": "POST", "status": 429, "duration_ms": 1.0, "cpu_ms": 0.0, "input_bytes": 70, "input_sha256": "ddc48fc0be6d9aa0", "outcome": "rate_limited"}
{"timestamp": "2026-11-15T02:24:04.050+00:00", "request_id": "cap-a2d4537a-54", "route": "/appeal", "method": "POST", "status": 200, "duration_ms": 15.0, "cpu_ms": 0.0, "input_bytes": 96, "input_sha256": "bf7e6e491270b8ad", "outcome": "under_review"}
{"timestamp": "2026-11-15T02:24:04.069+00:00", "request_id": "cap-a2d4537a-55", "route": "/appeal", "method": "POST", "status": 404, "duration_ms": 14.9, "cpu_ms": 0.0, "input_bytes": 68, "input_sha256": "a9b8cf870e76c8f3", "outcome": "unknown_content_id"}
```

Three things in there I didn't know before:

- The 429 and the 422 before it have the same `input_sha256`. The log can show
  a burst of identical inputs without ever having held the text.
- An appeal costs 15 ms against about 1 ms for a refusal. `/appeal` re-reads
  the whole audit log to find the decision, so it gets slower as the log grows.
- The cold start is one request that takes 13.7 s, all of it inside signal
  one: `model_ms` 13665 of 13679.

**What It Costs**

There's no API spend: gpt2 runs on this machine (16 logical CPUs, CPU-only
torch). The cost is compute, measured as process CPU-seconds per scored
submission.

Method: `capstone/run_capstone_eval.py --cost 10` starts the service, sends
one throwaway submission so the model is loaded, then sends 10 real ones
(5 human passages, 5 AI passages, 85–143 tokens each). It reads `cpu_ms` and
`duration_ms` back from `logs/requests.jsonl`. Full tables:
[`results/capstone_cost_2026-11-14_2126_after_1thread.md`](results/capstone_cost_2026-11-14_2126_after_1thread.md)
(the running configuration) and
[`..._before_8threads.md`](results/capstone_cost_2026-11-14_2125_before_8threads.md).

As it runs now (1 torch thread):

```
total CPU   = 0.641 + 0.562 + 0.562 + 0.688 + 0.469 + 0.625 + 0.656 + 0.656 + 0.688 + 0.688 = 6.234 CPU-s
per run     = 6.234 / 10 = 0.623 CPU-s   (wall 0.630 s, 120 tokens)
100 a day   = 100 x 0.623 = 62.3 CPU-s = 1.04 CPU-min of compute
            + 1 cold start a day (13.6 CPU-s) = 76.0 CPU-s
tokens/day  = 100 x 120 = 12030 tokens through gpt2
API spend   = $0 (gpt2 runs locally; no hosted API is called)
```

Before the improvement (torch's default of 8 threads), the same 10 inputs
cost 30.516 CPU-s: 3.052 per run, 305.2 CPU-s a day plus a 19.1 CPU-s cold
start, so **324.2 CPU-s a day**. One thread does the same work for 76.0 CPU-s,
**4.3× less**.

At 100 a day either number is small. One core has 86,400 CPU-s a day, and
this uses 0.09% of one. Two other costs are bigger than the per-request
compute:

- memory: gpt2 and torch stay resident the whole time the service is up
- the 13–15 s cold start after every restart

Refused requests (400/413/415/422/429) cost about 1 ms of wall time and
under the CPU clock's resolution, so a flood of junk is cheap to turn away.

**Run Log and Verdicts**

Criteria are in [`capstone/criteria.md`](capstone/criteria.md), committed
before anything ran. Each trial starts the service cold and sends the same
58 requests:

- the 30 evaluation texts
- 12 malformed bodies
- a 12-request burst from one creator: 10 × 422, then 2 × 429
- 2 appeals
- 2 extra submissions

Before the improvement
([`results/capstone_run_2026-11-14_2121_before.md`](results/capstone_run_2026-11-14_2121_before.md)):

| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |
|---|---|---|---|---|---|
| 1. Every request leaves one complete entry | 58/58 matched, 0 incomplete | 58/58 matched, 0 incomplete | 58/58 matched, 0 incomplete | 58/58 matched, 0 incomplete | **MET** |
| 2. Timings trustworthy | 100% bounded, ≥95% ≤50 ms, stages 100% | 58/58 bounded, 100% ≤50 ms, stages 32/32 | 58/58 bounded, 100% ≤50 ms, stages 32/32 | 58/58 bounded, 100% ≤50 ms, stages 32/32 | **MET** |
| 3. No writer text in the log | 0 6-grams found | 0 of 3076 found | 0 of 3076 found | 0 of 3076 found | **MET** |
| 4. Latency and CPU budget | warm p95 ≤2000 ms, CPU ≤3000 ms, cold ≤30 s | p95 408 ms, CPU 2963 ms, cold 12.9 s | p95 369 ms, CPU 3020 ms, cold 14.1 s | p95 429 ms, CPU 3135 ms, cold 14.3 s | **MISSED** |
| 5. Decisions unchanged | 30/30 identical, same 8 keys | 30/30 identical, keys same | 30/30 identical, keys same | 30/30 identical, keys same | **MET** |

**Diagnosis of the miss (criterion 4).**

- **Stage:** signal one (`detector.py::perplexity`, the gpt2 forward pass).
- **What the log shows:** across 93 warm submissions, `model_ms` is 290–326
  ms of a 293–330 ms request. `style_ms` is 0.5 ms, and routing, scoring and
  logging take the remaining ~3 ms. So the cost lives entirely in signal one.
- **The mechanism:** the CPU was 2963–3135 ms per request against about
  300 ms of wall time, roughly 10× more CPU than wall clock. torch's default
  on this machine is 8 intra-op threads. A ~130-token gpt2 pass is too small
  to split eight ways usefully, so most of those threads spin waiting on
  each other.
- **Confirmation:** I measured perplexity on the same 10 texts directly at
  different thread counts:

  | torch threads | wall per text | CPU per text | CPU ÷ wall |
  |---|---|---|---|
  | 16 | 419 ms | 3944 ms | 9.4 |
  | 8 (default) | 324 ms | 2405 ms | 7.4 |
  | 4 | 367 ms | 1311 ms | 3.6 |
  | 2 | 555 ms | 1083 ms | 1.9 |
  | 1 | 631 ms | 620 ms | 1.0 |

  Going from 1 thread to 8 buys 0.3 s of latency for 3.9× the CPU.
- **Why it MISSED and wasn't only "close":** the budget was set to keep 100
  a day under 5 CPU-minutes, and trial 1 passed only by 37 ms. That's a
  service sitting on the line, and two of three trials crossed it.

The other four held, and the log shows why:

- **Criterion 1:** the 429s are logged too. `metrics.start` runs before
  Flask-Limiter's check fires, and the 429 handler's response still passes
  through `after_request`.
- **Criterion 2:** the client-minus-server gap was at most a few
  milliseconds; the per-trial detail in the results file has max and median.
- **Criterion 5:** the decisions match unit 8 to four decimals.

**The Improvement**

**What changed:** `config.DETECTOR_THREADS = 1` (overridable with
`AI201_TORCH_THREADS`), applied with `torch.set_num_threads` in
`detector.py::_load`. That's one setting, chosen from the thread table above.
One thread is the cheapest per request and still keeps warm p95 under half the
2 s budget. On a shared machine it also leaves the other cores free for
concurrent requests, instead of eight threads fighting over them.

**Why:** the diagnosis put all the cost in signal one's thread count, not in
my code. Nothing else in the request costs more than 1 ms.

After
([`results/capstone_run_2026-11-14_2125_after.md`](results/capstone_run_2026-11-14_2125_after.md)),
side by side with before:

| Criterion | Before: Run 1 / 2 / 3 | Before | After: Run 1 / 2 / 3 | After |
|---|---|---|---|---|
| 1. One complete entry per request | 58/58, 0 incomplete ×3 | MET | 58/58, 0 incomplete ×3 | **MET** |
| 2. Timings trustworthy | 58/58 bounded, 100% ≤50 ms, 32/32 ×3 | MET | 58/58 bounded, 100% ≤50 ms, 32/32 ×3 | **MET** |
| 3. No writer text | 0 of 3076 ×3 | MET | 0 of 3076 ×3 | **MET** |
| 4. Latency and CPU budget | p95 408 / 369 / 429 ms; CPU 2963 / 3020 / 3135 ms; cold 12.9 / 14.1 / 14.3 s | MISSED | p95 890 / 844 / 1093 ms; CPU 617 / 614 / 656 ms; cold 13.7 / 13.9 / 12.9 s | **MET** |
| 5. Decisions unchanged | 30/30, keys same ×3 | MET | 30/30, keys same ×3 | **MET** |

**The trade:** CPU per scored submission fell from about 3.0 s to about 0.63 s
(4.8× less). Warm p95 latency roughly doubled, from about 0.4 s to 0.9–1.1 s.
A writer now waits about half a second longer, in exchange for a service that
uses a fifth of the compute. That's still under half the 2 s budget, but it's
a real cost. On a machine where only one writer is ever waiting, 4 threads
(367 ms wall, 1311 ms CPU) would be the better setting. The decisions didn't
move: 30/30 identical, so a single thread gives the same scores to four
decimals.

**What's Still Broken**

- **CPU time below about 16 ms reads as 0.** `time.process_time` on Windows
  ticks in 15.625 ms steps, so every refusal logs `cpu_ms: 0.0` (see the ten
  entries) and the per-run CPU numbers are quantised: 562.5, 656.2. My
  criteria didn't catch this because none of them checks CPU resolution. The
  scored-request totals are still right to about ±16 ms, so the cost math
  holds. Next step: measure per-thread CPU with `time.thread_time` or
  `psutil`, or log `null` with a note below the clock's resolution instead of
  a confident 0.0. I stopped because it doesn't change any verdict or the cost
  conclusion.
- **`cpu_ms` is process-wide.** I measured with one request at a time.
  Under concurrent load, two requests' CPU would overlap and each line would
  over-count. The fix is per-thread timing (as above) or a single worker per
  process. That isn't a problem at 100 a day, but it would be under a flood.
- **Cold start is 13–15 s.** Criterion 4 allows 30 s, so it's MET, but the
  first writer after every restart waits that long, and the log shows all of
  it is gpt2 loading. Next step: load the model at start-up
  (`detector.warm_up()` before `app.run`) so no request pays for it. I didn't
  do it because the capstone allows one improvement, and the CPU miss was the
  one that failed a criterion.
- **Memory isn't instrumented.** The log has no RSS, so I can't show the
  "won't fit a 512 MB host" claim from my own numbers. That claim rests on the
  526 MB on-disk model size alone. Next step: log the process RSS at start-up
  and after the first request.
- **`/appeal` scans the whole audit log** (15 ms now) and gets slower as the
  log grows. Next step: an index of content ids, or SQLite.
- **The request log grows forever.** There's no rotation or retention. At 100
  requests a day that's about 30 KB a day, so not urgent, but `logs/` has no
  limit.
- **Everything from unit 8's What's Still Broken still stands**: evasion
  through the disagreement shrink, ASCII-only word counting, and a rate limit
  keyed on a self-asserted `creator_id`. The capstone measured the service; it
  didn't change what it decides.

**How I Used AI**

As in units 7–8, Claude (Anthropic's Claude Opus 5.5, in Claude Code) built
this. It chose the shape, wrote the criteria, `metrics.py`, the harness, the
improvement and this write-up. Every number above comes from real runs on my
machine. It's not my independent work, and I'm saying so.

- **Moment 1, writing criteria before code.** I asked for the capstone end
  to end on any project. Claude picked Shape A on Provenance Guard because the
  audit log and local model made cost measurable. It wrote and committed
  `capstone/criteria.md` (commit `9171dea`) before `metrics.py` existed,
  including a 3 CPU-second budget derived from "100 a day under 5
  CPU-minutes". That budget is the one the first run missed. If the criteria
  had been written after seeing the numbers, the 3135 ms would probably have
  been called fine.
- **Moment 2, diagnosing the miss instead of loosening the target.** When
  criterion 4 missed by 20–135 ms, the easy move was to raise the budget.
  Claude instead used the log's own fields to locate the cost: `model_ms` was
  99% of `duration_ms`, while `cpu_ms` was 10× `duration_ms`. It then measured
  gpt2 directly at 1/2/4/8/16 threads to confirm the mechanism before changing
  one setting. It also reported the cost of the fix (latency about doubled)
  rather than only the win. The thing I'd check myself is the choice of 1
  thread over 4. That's a judgement about whether this service is CPU-bound
  or latency-bound, and the numbers support either.
