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

Thresholds: `HUMAN_THRESHOLD = 0.35`, `AI_THRESHOLD = 0.75`. A consequence I
test for (`tests/test_scoring.py::test_ai_label_requires_both_signals_above_half`):
a score above 0.75 is only reachable when *both* signals are above 0.5.

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
| unsure | 0.35 ≤ score ≤ 0.75 | We can't tell whether a person or an AI tool wrote this. A lot of writing that people do entirely on their own lands here, so please don't read this as an accusation. |
| high-confidence AI | 0.75 < score ≤ 1.00 | We think this was most likely written with an AI tool. Two separate checks both pointed that way, but they can be wrong: if you wrote this yourself, you can appeal and a person will review it. |

Both boundary values (0.35 and 0.75) belong to "unsure", so there's no gap and
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

<!-- ═══════════════════════ UNIT 8 — THE TEST ═══════════════════════ -->

---

## Rate Limiting

**My limits:** ___ per minute, ___ per day

**Why those numbers and not others:**
<!-- Think about two people: a real writer submitting their own work a few
     times an hour, and a script sending a thousand variations to map your
     thresholds. Your numbers have to be liveable for the first and hostile to
     the second. -->

**What a caller counts as:** <!-- per address, or per creator_id? They fail
differently — one script can look like a thousand callers, and one household
can look like one. -->

**The run of status codes when I pushed past it:**

<!-- python run_attacks.py --flood 15 -->

```

```

---

## Attack Run — Before

<!-- Every attack with its outcome and a held-or-broke mark.
     `run_attacks.py --label before` produces the table. -->



**Ten audit log entries from the run**

<!-- Choose entries that show the interesting failures, not the ten easiest. -->

```json

```

**The single worst outcome** — the one I'd least want to explain to a writer
whose work got caught by it:



---

## Run Log and Verdicts

<!-- Your five criteria across three trials. `run_eval.py --label before`. -->

| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |
|---|---|---|---|---|---|
| 1.  |  |  |  |  |  |
| 2.  |  |  |  |  |  |
| 3.  |  |  |  |  |  |
| 4.  |  |  |  |  |  |
| 5.  |  |  |  |  |  |

**Real output from one trial**, pasted as text, naming the file and function
that produced it:

```json

```

**Diagnoses**

<!-- For each miss AND each broken attack: the stage and the mechanism.

     Your service has five stages: the route, signal one, signal two, the
     combining rule, and the label mapping.

     Not a diagnosis:  "The evasion attacks got through."
     A diagnosis:      "Four evasion inputs got through. All four had typos
                        added to AI-generated text. My second signal measures
                        word variety, and typos raise word variety — so it read
                        them as more human. My combining rule weights that
                        signal at 0.6, so it dragged the whole score down."

     Look for a pattern. Five failures on one signal is one problem, not five. -->



---

## The Improvement

**What I changed:**

**Which diagnosis pointed at it:**

### Attack Run — After

<!-- Same format. `run_attacks.py --label after` -->



**Did it help, and how do I know:**

<!-- Widening the unsure band usually fixes one problem and creates another.
     Reporting that trade honestly is worth full credit. -->



---

## What's Still Broken

<!-- For each attack still getting through and each criterion still missed:
     what you'd do, and why you stopped. -->



**The trade I'd make if this ran for real:**

<!-- Two sentences. Fewer wrong accusations means more AI text getting through.
     Say which way you'd go and WHO PAYS FOR IT. -->



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
