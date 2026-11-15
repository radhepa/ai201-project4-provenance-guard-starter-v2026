# Attack run — before

- Produced by: `run_attacks.py::main`
- Service: `app.py::submit`
- 56 attacks · 2026-11-14 20:55
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
| EV01 | evasion | signal two: typos raise word variety | 200 | `4fd4951fab794a4fb2f45cfee7ef281c` | unsure | 0.500 |  |
| EV02 | evasion | signal two: broken-up sentences raise length spread | 200 | `d08b90e22a004b84af1a54e748bad6a2` | unsure | 0.550 |  |
| EV03 | evasion | signal two: a pasted quotation changes the shape | 200 | `87828ff9c0a2406ca859138b8754de23` | unsure | 0.642 |  |
| EV04 | evasion | signal one: unusual words raise perplexity | 200 | `28d0458a324a4dada13f7db8ae0a8770` | unsure | 0.733 |  |
| EV05 | evasion | both signals: heavy human editing pass | 200 | `fb18361c79d2426e9f7c58e553a5ce80` | unsure | 0.420 |  |
| EV06 | evasion | signal two: one very long sentence and one very short | 200 | `4f6e888411c44171ab963d90a297fe18` | unsure | 0.587 |  |
| EV07 | evasion | signal two: padding with punctuation | 200 | `aa24ed8fe8a04db1ab8529b96c7ab802` | unsure | 0.524 |  |
| EV08 | evasion | signal one: text below the token window | 422 | `—` | — | — |  |
| EV09 | evasion | both: AI text with a human opening paragraph bolted on | 200 | `b9147ec3b5b647848539dabcf2d5e965` | unsure | 0.740 |  |
| EV10 | evasion | signal two: repeated stanza structure | 200 | `a03444a250514cae89e1220d631eac8a` | unsure | 0.735 |  |
| FP01 | false_positive | plain, clear human writing with no flourishes | 200 | `e118ba0b31f64ca8a80243a7069019e9` | unsure | 0.621 |  |
| FP02 | false_positive | human writing in a formal register | 200 | `803524a80499485b8aeb2f44d77a21c0` | unsure | 0.732 |  |
| FP03 | false_positive | a non-native English speaker writing carefully | 200 | `7f868f44046d40ac81c81aaf1caa9e01` | ai | 0.797 |  |
| FP04 | false_positive | a student essay written to a rubric | 200 | `dd713c7b1f53416fa948aba1bdd65cb7` | ai | 0.801 |  |
| FP05 | false_positive | technical documentation written by a person | 200 | `49f7b25ca65446d1a8bb7b5a37bde46f` | unsure | 0.737 |  |
| FP06 | false_positive | a person imitating a formal template | 200 | `5b60ff42dc044a0ea6b255354f1dc70b` | unsure | 0.656 |  |
| FP07 | false_positive | human writing that repeats a phrase deliberately | 200 | `5e00b45b98c140ec9cd649cd69ae43c1` | unsure | 0.605 |  |
| FP08 | false_positive | very short genuine human submission | 422 | `—` | — | — |  |
| PI01 | prompt_injection | instruction to ignore the check | 200 | `7554570414064136af8fa3811591db38` | unsure | 0.544 |  |
| PI02 | prompt_injection | instruction disguised as a system message | 200 | `b461533a5b544e539f6b45e840da06ce` | human | 0.349 |  |
| PI03 | prompt_injection | instruction wrapped in the writer's voice | 200 | `64abfdd1a5544982b163a6f97c57d93c` | unsure | 0.600 |  |
| PI04 | prompt_injection | attempt to make the label text hostile | 200 | `5418157f82ea4ef281e0665fb0528c81` | unsure | 0.500 |  |
| PI05 | prompt_injection | attempt to inject into the audit log | 200 | `2c4aeef7e84f445a91a648074ad047ed` | unsure | 0.566 |  |
| PI06 | prompt_injection | instruction plus real human text | 200 | `1da356e2519547f8a8d6b381aa161d81` | unsure | 0.597 |  |
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
  "content_id": "4fd4951fab794a4fb2f45cfee7ef281c",
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
  "content_id": "d08b90e22a004b84af1a54e748bad6a2",
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
  "content_id": "87828ff9c0a2406ca859138b8754de23",
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
  "content_id": "28d0458a324a4dada13f7db8ae0a8770",
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
  "content_id": "fb18361c79d2426e9f7c58e553a5ce80",
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
  "content_id": "4f6e888411c44171ab963d90a297fe18",
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
  "content_id": "aa24ed8fe8a04db1ab8529b96c7ab802",
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
  "content_id": "b9147ec3b5b647848539dabcf2d5e965",
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
  "content_id": "a03444a250514cae89e1220d631eac8a",
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
  "content_id": "e118ba0b31f64ca8a80243a7069019e9",
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
  "content_id": "803524a80499485b8aeb2f44d77a21c0",
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
  "content_id": "7f868f44046d40ac81c81aaf1caa9e01",
  "creator_id": "attacker_FP03",
  "guess": "ai",
  "confidence": 0.7971,
  "model_score": 0.8051,
  "style_score": 0.785,
  "label": "We think this was most likely written with an AI tool. Two separate checks both pointed that way, but they can be wrong: if you wrote this yourself, you can appeal and a person will review it.",
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
  "content_id": "dd713c7b1f53416fa948aba1bdd65cb7",
  "creator_id": "attacker_FP04",
  "guess": "ai",
  "confidence": 0.8009,
  "model_score": 0.8329,
  "style_score": 0.753,
  "label": "We think this was most likely written with an AI tool. Two separate checks both pointed that way, but they can be wrong: if you wrote this yourself, you can appeal and a person will review it.",
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
  "content_id": "49f7b25ca65446d1a8bb7b5a37bde46f",
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
  "content_id": "5b60ff42dc044a0ea6b255354f1dc70b",
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
  "content_id": "5e00b45b98c140ec9cd649cd69ae43c1",
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
  "content_id": "7554570414064136af8fa3811591db38",
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
  "content_id": "b461533a5b544e539f6b45e840da06ce",
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
  "content_id": "64abfdd1a5544982b163a6f97c57d93c",
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
  "content_id": "5418157f82ea4ef281e0665fb0528c81",
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
  "content_id": "2c4aeef7e84f445a91a648074ad047ed",
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
  "content_id": "1da356e2519547f8a8d6b381aa161d81",
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
