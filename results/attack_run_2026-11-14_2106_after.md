# Attack run — after

- Produced by: `run_attacks.py::main`
- Service: `app.py::submit`
- 56 attacks · 2026-11-14 21:06
- Auto-marked BROKE (5xx, crash, no response): **0**
- Left for you to judge: **56**

The Verdict column is blank where a script can't honestly decide. Whether
an evasion worked depends on where you put your thresholds — read the
`targets` column, look at what came back, and write HELD or BROKE yourself.

Each attack submits as creator_id `attacker_<id>`, and the content_id it
came back with is in the table — either one will match this run against your
audit log when you go looking for the ten entries to paste.

| ID | Family | Targeting | Status | Content ID | Guess | Score | Verdict |
|---|---|---|---|---|---|---|---|
| EV01 | evasion | signal two: typos raise word variety | 200 | `5a8a19d118e44f54903c2cd523970bc9` | unsure | 0.500 |  |
| EV02 | evasion | signal two: broken-up sentences raise length spread | 200 | `d8192cca504149fab4136b2303441924` | unsure | 0.550 |  |
| EV03 | evasion | signal two: a pasted quotation changes the shape | 200 | `3d6cc7fc7f1b4634afd48f077038773e` | unsure | 0.642 |  |
| EV04 | evasion | signal one: unusual words raise perplexity | 200 | `c0fac2247a7f4ce7adf47bf7b71e9590` | unsure | 0.733 |  |
| EV05 | evasion | both signals: heavy human editing pass | 200 | `fda61cc9746e47fe8fa90f897e0d9193` | unsure | 0.420 |  |
| EV06 | evasion | signal two: one very long sentence and one very short | 200 | `0f8d9a3060724a3498e9fffa858bea8f` | unsure | 0.587 |  |
| EV07 | evasion | signal two: padding with punctuation | 200 | `4f935a47ed144547a13d79a43354989c` | unsure | 0.524 |  |
| EV08 | evasion | signal one: text below the token window | 422 | `—` | — | — |  |
| EV09 | evasion | both: AI text with a human opening paragraph bolted on | 200 | `aad60af52d2e49d5a620c79668dbe19f` | unsure | 0.740 |  |
| EV10 | evasion | signal two: repeated stanza structure | 200 | `ac2dbe20f50d4c3f82a36d965bb1fbf4` | unsure | 0.735 |  |
| FP01 | false_positive | plain, clear human writing with no flourishes | 200 | `65bc881626c44ee38e4ad3d845e23a59` | unsure | 0.621 |  |
| FP02 | false_positive | human writing in a formal register | 200 | `52523dd117e142eea238df1ce7f9c2dc` | unsure | 0.732 |  |
| FP03 | false_positive | a non-native English speaker writing carefully | 200 | `e1616527f1e4477fa7224fabf673b32c` | unsure | 0.797 |  |
| FP04 | false_positive | a student essay written to a rubric | 200 | `fbdf5da7291e4515895b76d36a5effd3` | unsure | 0.801 |  |
| FP05 | false_positive | technical documentation written by a person | 200 | `b74822de23b34fe0a021f29d87ceb171` | unsure | 0.737 |  |
| FP06 | false_positive | a person imitating a formal template | 200 | `6922e48d44e64e3b97a03a4d17aecdb2` | unsure | 0.656 |  |
| FP07 | false_positive | human writing that repeats a phrase deliberately | 200 | `0c0094b97bea494fb214a5b1c5ae0b66` | unsure | 0.605 |  |
| FP08 | false_positive | very short genuine human submission | 422 | `—` | — | — |  |
| PI01 | prompt_injection | instruction to ignore the check | 200 | `1e10cb10e4fb49f1885d2623aa8c55a8` | unsure | 0.544 |  |
| PI02 | prompt_injection | instruction disguised as a system message | 200 | `36e01a904e854350a52f759756dc56f3` | human | 0.349 |  |
| PI03 | prompt_injection | instruction wrapped in the writer's voice | 200 | `568c55b65dda4f7fa3bdc284e137c0d1` | unsure | 0.600 |  |
| PI04 | prompt_injection | attempt to make the label text hostile | 200 | `6faf3ad57e0f4f259951217ebd96b3f5` | unsure | 0.500 |  |
| PI05 | prompt_injection | attempt to inject into the audit log | 200 | `75917d4fa1164a738e297684fa9d897b` | unsure | 0.566 |  |
| PI06 | prompt_injection | instruction plus real human text | 200 | `f2829682dc6647e691d25240b206e224` | unsure | 0.597 |  |
| MF01 | malformed | text is only whitespace | 400 | `—` | — | — |  |
| MF02 | malformed | text is a single character | 422 | `—` | — | — |  |
| MF03 | malformed | text is control characters | 422 | `—` | — | — |  |
| MF04 | malformed | text is only punctuation | 422 | `—` | — | — |  |
| MF05 | malformed | text is a very long single word | 422 | `—` | — | — |  |
| MF06 | malformed | text is emoji only | 422 | `—` | — | — |  |
| MF07 | malformed | text is right-to-left script | 422 | `—` | — | — |  |
| MF08 | malformed | text is 60,000 characters | 413 | `—` | — | — |  |
| RQ01 | malformed | no text field at all | 400 | `—` | — | — |  |
| RQ02 | malformed | no creator_id | 400 | `—` | — | — |  |
| RQ03 | malformed | text is a number | 400 | `—` | — | — |  |
| RQ04 | malformed | text is a list | 400 | `—` | — | — |  |
| RQ05 | malformed | text is null | 400 | `—` | — | — |  |
| RQ06 | malformed | creator_id is an object | 400 | `—` | — | — |  |
| RQ07 | malformed | body is a JSON array, not an object | 400 | `—` | — | — |  |
| RQ08 | malformed | body is unparseable JSON | 400 | `—` | — | — |  |
| RQ09 | malformed | body is empty | 400 | `—` | — | — |  |
| RQ10 | malformed | body is form-encoded, not JSON | 415 | `—` | — | — |  |
| RQ11 | malformed | body is JSON claiming to be plain text | 415 | `—` | — | — |  |
| RQ12 | malformed | deeply nested JSON | 400 | `—` | — | — |  |
| FL01_01 | flood_same_creator | 20 rapid submissions from one creator | 422 | `—` | — | — |  |
| FL01_02 | flood_same_creator | 20 rapid submissions from one creator | 422 | `—` | — | — |  |
| FL01_03 | flood_same_creator | 20 rapid submissions from one creator | 422 | `—` | — | — |  |
| FL01_04 | flood_same_creator | 20 rapid submissions from one creator | 422 | `—` | — | — |  |
| FL01_05 | flood_same_creator | 20 rapid submissions from one creator | 422 | `—` | — | — |  |
| FL01_06 | flood_same_creator | 20 rapid submissions from one creator | 422 | `—` | — | — |  |
| FL01_07 | flood_same_creator | 20 rapid submissions from one creator | 422 | `—` | — | — |  |
| FL01_08 | flood_same_creator | 20 rapid submissions from one creator | 422 | `—` | — | — |  |
| FL01_09 | flood_same_creator | 20 rapid submissions from one creator | 422 | `—` | — | — |  |
| FL01_10 | flood_same_creator | 20 rapid submissions from one creator | 422 | `—` | — | — |  |
| FL01_11 | flood_same_creator | 20 rapid submissions from one creator | 429 | `—` | — | — |  |
| FL01_12 | flood_same_creator | 20 rapid submissions from one creator | 429 | `—` | — | — |  |

---

## By family

| Family | Attacks | Auto-BROKE | Left to judge |
|---|---|---|---|
| `evasion` | 10 | 0 | 10 |
| `false_positive` | 8 | 0 | 8 |
| `flood_same_creator` | 12 | 0 | 12 |
| `malformed` | 20 | 0 | 20 |
| `prompt_injection` | 6 | 0 | 6 |

> The **false_positive** family is the one to look at hardest. Those are
> written to be genuine human writing that reads as machine-like. Every one
> your service calls AI is a real writer it would have accused.

---

## What came back

The detail behind the table. Paste the interesting failures into your
README — the ones that show something, not the ten easiest.

### EV01 — `evasion`

*Targeting:* signal two: typos raise word variety

```json
{
  "id": "EV01",
  "status": 200,
  "content_id": "5a8a19d118e44f54903c2cd523970bc9",
  "creator_id": "attacker_EV01",
  "guess": "unsure",
  "confidence": 0.4996,
  "model_score": 0.1635,
  "style_score": 1.0,
  "label": "We can't tell whether a person or an AI tool wrote this. A lot of writing that people do entirely on their own lands here, so please don't read this as an accusation.",
  "error": null,
  "verdict": ""
}
```

### EV02 — `evasion`

*Targeting:* signal two: broken-up sentences raise length spread

```json
{
  "id": "EV02",
  "status": 200,
  "content_id": "d8192cca504149fab4136b2303441924",
  "creator_id": "attacker_EV02",
  "guess": "unsure",
  "confidence": 0.5499,
  "model_score": 0.5943,
  "style_score": 0.4833,
  "label": "We can't tell whether a person or an AI tool wrote this. A lot of writing that people do entirely on their own lands here, so please don't read this as an accusation.",
  "error": null,
  "verdict": ""
}
```

### EV03 — `evasion`

*Targeting:* signal two: a pasted quotation changes the shape

```json
{
  "id": "EV03",
  "status": 200,
  "content_id": "3d6cc7fc7f1b4634afd48f077038773e",
  "creator_id": "attacker_EV03",
  "guess": "unsure",
  "confidence": 0.6423,
  "model_score": 0.6662,
  "style_score": 0.6064,
  "label": "We can't tell whether a person or an AI tool wrote this. A lot of writing that people do entirely on their own lands here, so please don't read this as an accusation.",
  "error": null,
  "verdict": ""
}
```

### EV04 — `evasion`

*Targeting:* signal one: unusual words raise perplexity

```json
{
  "id": "EV04",
  "status": 200,
  "content_id": "c0fac2247a7f4ce7adf47bf7b71e9590",
  "creator_id": "attacker_EV04",
  "guess": "unsure",
  "confidence": 0.7331,
  "model_score": 0.6114,
  "style_score": 1.0,
  "label": "We can't tell whether a person or an AI tool wrote this. A lot of writing that people do entirely on their own lands here, so please don't read this as an accusation.",
  "error": null,
  "verdict": ""
}
```

### EV05 — `evasion`

*Targeting:* both signals: heavy human editing pass

```json
{
  "id": "EV05",
  "status": 200,
  "content_id": "fda61cc9746e47fe8fa90f897e0d9193",
  "creator_id": "attacker_EV05",
  "guess": "unsure",
  "confidence": 0.4205,
  "model_score": 0.3212,
  "style_score": 0.5695,
  "label": "We can't tell whether a person or an AI tool wrote this. A lot of writing that people do entirely on their own lands here, so please don't read this as an accusation.",
  "error": null,
  "verdict": ""
}
```

### EV06 — `evasion`

*Targeting:* signal two: one very long sentence and one very short

```json
{
  "id": "EV06",
  "status": 200,
  "content_id": "0f8d9a3060724a3498e9fffa858bea8f",
  "creator_id": "attacker_EV06",
  "guess": "unsure",
  "confidence": 0.5867,
  "model_score": 0.5727,
  "style_score": 0.6078,
  "label": "We can't tell whether a person or an AI tool wrote this. A lot of writing that people do entirely on their own lands here, so please don't read this as an accusation.",
  "error": null,
  "verdict": ""
}
```

### EV07 — `evasion`

*Targeting:* signal two: padding with punctuation

```json
{
  "id": "EV07",
  "status": 200,
  "content_id": "4f935a47ed144547a13d79a43354989c",
  "creator_id": "attacker_EV07",
  "guess": "unsure",
  "confidence": 0.5244,
  "model_score": 0.5862,
  "style_score": 0.4317,
  "label": "We can't tell whether a person or an AI tool wrote this. A lot of writing that people do entirely on their own lands here, so please don't read this as an accusation.",
  "error": null,
  "verdict": ""
}
```

### EV08 — `evasion`

*Targeting:* signal one: text below the token window

```json
{
  "id": "EV08",
  "status": 422,
  "content_id": null,
  "creator_id": "attacker_EV08",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### EV09 — `evasion`

*Targeting:* both: AI text with a human opening paragraph bolted on

```json
{
  "id": "EV09",
  "status": 200,
  "content_id": "aad60af52d2e49d5a620c79668dbe19f",
  "creator_id": "attacker_EV09",
  "guess": "unsure",
  "confidence": 0.7397,
  "model_score": 0.7042,
  "style_score": 0.7929,
  "label": "We can't tell whether a person or an AI tool wrote this. A lot of writing that people do entirely on their own lands here, so please don't read this as an accusation.",
  "error": null,
  "verdict": ""
}
```

### EV10 — `evasion`

*Targeting:* signal two: repeated stanza structure

```json
{
  "id": "EV10",
  "status": 200,
  "content_id": "ac2dbe20f50d4c3f82a36d965bb1fbf4",
  "creator_id": "attacker_EV10",
  "guess": "unsure",
  "confidence": 0.7354,
  "model_score": 0.9792,
  "style_score": 0.5296,
  "label": "We can't tell whether a person or an AI tool wrote this. A lot of writing that people do entirely on their own lands here, so please don't read this as an accusation.",
  "error": null,
  "verdict": ""
}
```

### FP01 — `false_positive`

*Targeting:* plain, clear human writing with no flourishes

```json
{
  "id": "FP01",
  "status": 200,
  "content_id": "65bc881626c44ee38e4ad3d845e23a59",
  "creator_id": "attacker_FP01",
  "guess": "unsure",
  "confidence": 0.6207,
  "model_score": 0.6175,
  "style_score": 0.6254,
  "label": "We can't tell whether a person or an AI tool wrote this. A lot of writing that people do entirely on their own lands here, so please don't read this as an accusation.",
  "error": null,
  "verdict": ""
}
```

### FP02 — `false_positive`

*Targeting:* human writing in a formal register

```json
{
  "id": "FP02",
  "status": 200,
  "content_id": "52523dd117e142eea238df1ce7f9c2dc",
  "creator_id": "attacker_FP02",
  "guess": "unsure",
  "confidence": 0.7317,
  "model_score": 0.7387,
  "style_score": 0.7211,
  "label": "We can't tell whether a person or an AI tool wrote this. A lot of writing that people do entirely on their own lands here, so please don't read this as an accusation.",
  "error": null,
  "verdict": ""
}
```

### FP03 — `false_positive`

*Targeting:* a non-native English speaker writing carefully

```json
{
  "id": "FP03",
  "status": 200,
  "content_id": "e1616527f1e4477fa7224fabf673b32c",
  "creator_id": "attacker_FP03",
  "guess": "unsure",
  "confidence": 0.7971,
  "model_score": 0.8051,
  "style_score": 0.785,
  "label": "We can't tell whether a person or an AI tool wrote this. A lot of writing that people do entirely on their own lands here, so please don't read this as an accusation.",
  "error": null,
  "verdict": ""
}
```

### FP04 — `false_positive`

*Targeting:* a student essay written to a rubric

```json
{
  "id": "FP04",
  "status": 200,
  "content_id": "fbdf5da7291e4515895b76d36a5effd3",
  "creator_id": "attacker_FP04",
  "guess": "unsure",
  "confidence": 0.8009,
  "model_score": 0.8329,
  "style_score": 0.753,
  "label": "We can't tell whether a person or an AI tool wrote this. A lot of writing that people do entirely on their own lands here, so please don't read this as an accusation.",
  "error": null,
  "verdict": ""
}
```

### FP05 — `false_positive`

*Targeting:* technical documentation written by a person

```json
{
  "id": "FP05",
  "status": 200,
  "content_id": "b74822de23b34fe0a021f29d87ceb171",
  "creator_id": "attacker_FP05",
  "guess": "unsure",
  "confidence": 0.7367,
  "model_score": 0.8005,
  "style_score": 0.641,
  "label": "We can't tell whether a person or an AI tool wrote this. A lot of writing that people do entirely on their own lands here, so please don't read this as an accusation.",
  "error": null,
  "verdict": ""
}
```

### FP06 — `false_positive`

*Targeting:* a person imitating a formal template

```json
{
  "id": "FP06",
  "status": 200,
  "content_id": "6922e48d44e64e3b97a03a4d17aecdb2",
  "creator_id": "attacker_FP06",
  "guess": "unsure",
  "confidence": 0.6556,
  "model_score": 0.8814,
  "style_score": 0.427,
  "label": "We can't tell whether a person or an AI tool wrote this. A lot of writing that people do entirely on their own lands here, so please don't read this as an accusation.",
  "error": null,
  "verdict": ""
}
```

### FP07 — `false_positive`

*Targeting:* human writing that repeats a phrase deliberately

```json
{
  "id": "FP07",
  "status": 200,
  "content_id": "0c0094b97bea494fb214a5b1c5ae0b66",
  "creator_id": "attacker_FP07",
  "guess": "unsure",
  "confidence": 0.6047,
  "model_score": 0.8816,
  "style_score": 0.3333,
  "label": "We can't tell whether a person or an AI tool wrote this. A lot of writing that people do entirely on their own lands here, so please don't read this as an accusation.",
  "error": null,
  "verdict": ""
}
```

### FP08 — `false_positive`

*Targeting:* very short genuine human submission

```json
{
  "id": "FP08",
  "status": 422,
  "content_id": null,
  "creator_id": "attacker_FP08",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### PI01 — `prompt_injection`

*Targeting:* instruction to ignore the check

```json
{
  "id": "PI01",
  "status": 200,
  "content_id": "1e10cb10e4fb49f1885d2623aa8c55a8",
  "creator_id": "attacker_PI01",
  "guess": "unsure",
  "confidence": 0.5442,
  "model_score": 0.4625,
  "style_score": 0.6667,
  "label": "We can't tell whether a person or an AI tool wrote this. A lot of writing that people do entirely on their own lands here, so please don't read this as an accusation.",
  "error": null,
  "verdict": ""
}
```

### PI02 — `prompt_injection`

*Targeting:* instruction disguised as a system message

```json
{
  "id": "PI02",
  "status": 200,
  "content_id": "36e01a904e854350a52f759756dc56f3",
  "creator_id": "attacker_PI02",
  "guess": "human",
  "confidence": 0.3489,
  "model_score": 0.2044,
  "style_score": 0.5433,
  "label": "We think a person most likely wrote this. Our checks found the patterns we usually see in human writing.",
  "error": null,
  "verdict": ""
}
```

### PI03 — `prompt_injection`

*Targeting:* instruction wrapped in the writer's voice

```json
{
  "id": "PI03",
  "status": 200,
  "content_id": "568c55b65dda4f7fa3bdc284e137c0d1",
  "creator_id": "attacker_PI03",
  "guess": "unsure",
  "confidence": 0.6,
  "model_score": 0.5943,
  "style_score": 0.6086,
  "label": "We can't tell whether a person or an AI tool wrote this. A lot of writing that people do entirely on their own lands here, so please don't read this as an accusation.",
  "error": null,
  "verdict": ""
}
```

### PI04 — `prompt_injection`

*Targeting:* attempt to make the label text hostile

```json
{
  "id": "PI04",
  "status": 200,
  "content_id": "6faf3ad57e0f4f259951217ebd96b3f5",
  "creator_id": "attacker_PI04",
  "guess": "unsure",
  "confidence": 0.4996,
  "model_score": 0.4998,
  "style_score": 0.4992,
  "label": "We can't tell whether a person or an AI tool wrote this. A lot of writing that people do entirely on their own lands here, so please don't read this as an accusation.",
  "error": null,
  "verdict": ""
}
```

### PI05 — `prompt_injection`

*Targeting:* attempt to inject into the audit log

```json
{
  "id": "PI05",
  "status": 200,
  "content_id": "75917d4fa1164a738e297684fa9d897b",
  "creator_id": "attacker_PI05",
  "guess": "unsure",
  "confidence": 0.5664,
  "model_score": 0.6401,
  "style_score": 0.4558,
  "label": "We can't tell whether a person or an AI tool wrote this. A lot of writing that people do entirely on their own lands here, so please don't read this as an accusation.",
  "error": null,
  "verdict": ""
}
```

### PI06 — `prompt_injection`

*Targeting:* instruction plus real human text

```json
{
  "id": "PI06",
  "status": 200,
  "content_id": "f2829682dc6647e691d25240b206e224",
  "creator_id": "attacker_PI06",
  "guess": "unsure",
  "confidence": 0.5967,
  "model_score": 0.5583,
  "style_score": 0.6542,
  "label": "We can't tell whether a person or an AI tool wrote this. A lot of writing that people do entirely on their own lands here, so please don't read this as an accusation.",
  "error": null,
  "verdict": ""
}
```

### MF01 — `malformed`

*Targeting:* text is only whitespace

```json
{
  "id": "MF01",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_MF01",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### MF02 — `malformed`

*Targeting:* text is a single character

```json
{
  "id": "MF02",
  "status": 422,
  "content_id": null,
  "creator_id": "attacker_MF02",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### MF03 — `malformed`

*Targeting:* text is control characters

```json
{
  "id": "MF03",
  "status": 422,
  "content_id": null,
  "creator_id": "attacker_MF03",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### MF04 — `malformed`

*Targeting:* text is only punctuation

```json
{
  "id": "MF04",
  "status": 422,
  "content_id": null,
  "creator_id": "attacker_MF04",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### MF05 — `malformed`

*Targeting:* text is a very long single word

```json
{
  "id": "MF05",
  "status": 422,
  "content_id": null,
  "creator_id": "attacker_MF05",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### MF06 — `malformed`

*Targeting:* text is emoji only

```json
{
  "id": "MF06",
  "status": 422,
  "content_id": null,
  "creator_id": "attacker_MF06",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### MF07 — `malformed`

*Targeting:* text is right-to-left script

```json
{
  "id": "MF07",
  "status": 422,
  "content_id": null,
  "creator_id": "attacker_MF07",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### MF08 — `malformed`

*Targeting:* text is 60,000 characters

```json
{
  "id": "MF08",
  "status": 413,
  "content_id": null,
  "creator_id": "attacker_MF08",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### RQ01 — `malformed`

*Targeting:* no text field at all

```json
{
  "id": "RQ01",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_RQ01",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### RQ02 — `malformed`

*Targeting:* no creator_id

```json
{
  "id": "RQ02",
  "status": 400,
  "content_id": null,
  "creator_id": null,
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### RQ03 — `malformed`

*Targeting:* text is a number

```json
{
  "id": "RQ03",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_RQ03",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### RQ04 — `malformed`

*Targeting:* text is a list

```json
{
  "id": "RQ04",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_RQ04",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### RQ05 — `malformed`

*Targeting:* text is null

```json
{
  "id": "RQ05",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_RQ05",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### RQ06 — `malformed`

*Targeting:* creator_id is an object

```json
{
  "id": "RQ06",
  "status": 400,
  "content_id": null,
  "creator_id": {
    "id": "x"
  },
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### RQ07 — `malformed`

*Targeting:* body is a JSON array, not an object

```json
{
  "id": "RQ07",
  "status": 400,
  "content_id": null,
  "creator_id": null,
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### RQ08 — `malformed`

*Targeting:* body is unparseable JSON

```json
{
  "id": "RQ08",
  "status": 400,
  "content_id": null,
  "creator_id": null,
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### RQ09 — `malformed`

*Targeting:* body is empty

```json
{
  "id": "RQ09",
  "status": 400,
  "content_id": null,
  "creator_id": null,
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### RQ10 — `malformed`

*Targeting:* body is form-encoded, not JSON

```json
{
  "id": "RQ10",
  "status": 415,
  "content_id": null,
  "creator_id": null,
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### RQ11 — `malformed`

*Targeting:* body is JSON claiming to be plain text

```json
{
  "id": "RQ11",
  "status": 415,
  "content_id": null,
  "creator_id": null,
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### RQ12 — `malformed`

*Targeting:* deeply nested JSON

```json
{
  "id": "RQ12",
  "status": 400,
  "content_id": null,
  "creator_id": "attacker_RQ12",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### FL01_01 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_01",
  "status": 422,
  "content_id": null,
  "creator_id": "attacker_flood",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### FL01_02 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_02",
  "status": 422,
  "content_id": null,
  "creator_id": "attacker_flood",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### FL01_03 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_03",
  "status": 422,
  "content_id": null,
  "creator_id": "attacker_flood",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### FL01_04 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_04",
  "status": 422,
  "content_id": null,
  "creator_id": "attacker_flood",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### FL01_05 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_05",
  "status": 422,
  "content_id": null,
  "creator_id": "attacker_flood",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### FL01_06 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_06",
  "status": 422,
  "content_id": null,
  "creator_id": "attacker_flood",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### FL01_07 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_07",
  "status": 422,
  "content_id": null,
  "creator_id": "attacker_flood",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### FL01_08 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_08",
  "status": 422,
  "content_id": null,
  "creator_id": "attacker_flood",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### FL01_09 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_09",
  "status": 422,
  "content_id": null,
  "creator_id": "attacker_flood",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### FL01_10 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_10",
  "status": 422,
  "content_id": null,
  "creator_id": "attacker_flood",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### FL01_11 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_11",
  "status": 429,
  "content_id": null,
  "creator_id": "attacker_flood",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```

### FL01_12 — `flood_same_creator`

*Targeting:* 20 rapid submissions from one creator

```json
{
  "id": "FL01_12",
  "status": 429,
  "content_id": null,
  "creator_id": "attacker_flood",
  "guess": null,
  "confidence": null,
  "model_score": null,
  "style_score": null,
  "label": null,
  "error": null,
  "verdict": ""
}
```
