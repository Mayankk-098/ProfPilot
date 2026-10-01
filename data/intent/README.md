# ProfPilot intent + entity dataset (format spec)

One file trains **two heads** from the same sentences:

1. **Intent classification** - what does the lecturer want? (13 classes, `taxonomy.json`)
2. **Entity extraction** - which spans carry the parameters? (10 labels)

The model only outputs *spans and labels*. Turning "tomorrow" into a date, or "DBMS" into
`course_id="dbms"`, is **deterministic code** that uses the academic context. That split
is the one your synopsis promises ("learned intelligence vs deterministic logic").

## Files

| File | Purpose |
|---|---|
| `taxonomy.json` | The allowed intents, entity labels, splits, languages, sources. Source of truth. |
| `examples_marked.tsv` | **Edit this one.** One example per line, entities written inline as `[[text\|LABEL]]`. |
| `examples.jsonl` | Generated from the TSV (don't hand-edit). What training code reads. |
| `from_markup.py` | TSV -> JSONL, computes character offsets for you. |
| `validate.py` | Checks offsets, labels, overlaps, leakage. Run before every commit. |

```bash
python data/intent/from_markup.py   # regenerate examples.jsonl
python data/intent/validate.py      # must print "OK"
```

## Record format (`examples.jsonl`, one JSON object per line)

```json
{
  "id": "ex-0003",
  "text": "will I finish AI before 7 December",
  "lang": "en",
  "intent": "query_course_completion",
  "entities": [
    {"start": 14, "end": 16, "label": "COURSE", "text": "AI"},
    {"start": 24, "end": 34, "label": "DATE",   "text": "7 December"}
  ],
  "group": "qcc2",
  "split": "dev",
  "source": "handwritten"
}
```

- `start`/`end` are **character offsets into `text`, end-exclusive** (`text[start:end] == entities[i].text`;
  the validator enforces this, so offsets can't silently drift).
- `group` = the base sentence this row is a paraphrase of. **All rows of a group must be in the same split.**
  Otherwise a rewording of a training sentence lands in test and your F1 is fake.
- `lang`: `en` or `hinglish` (Indian university lecturers will really say "kal DBMS ki class cancel kar do").
- `source`: `handwritten`, `synthetic` (template-generated), or `student_contributed`.

## Intents

| Intent | Action? | Maps to today |
|---|---|---|
| `query_course_completion` | no | finish-date block in `ai_service.py` |
| `what_if_schedule_change` | no | what-if block (currently cancel-only) |
| `query_next_class` | no | next-class block |
| `query_last_lecture` | no | "what did I teach" block |
| `query_course_status` | no | course-status block |
| `query_attendance_low` | no | low-attendance block |
| `query_memory_events` | no | recent-events block |
| `explain_delay` | no | "why am I behind" block |
| `cancel_class` | **yes** | not built yet |
| `reschedule_class` | **yes** | not built yet |
| `notify_batch` | **yes** | not built yet |
| `log_lecture` | **yes** | not built yet |
| `out_of_scope` | no | generic fallback |

`is_action: true` intents must go through the confirmation flow (synopsis: "lecturer
confirmation before consequential actions"). The `what_if_*` intent is deliberately *not* an
action: it simulates, it never changes the timetable. Getting those two confused is the
classic bug, so keep them separate in the data.

## Annotation rules (agree on these as a team)

1. Label the span **as written**, not normalised: `DBMS`, not `Database Management Systems`.
2. Exclude possessive `'s` from the span: `[[tomorrow|DATE]]'s class`.
3. Include the unit in `DURATION` (`45 minutes`) and the `%` in `THRESHOLD` (`75%`).
4. `reschedule_class`: the original slot is `DATE`/`TIME`, the target is `NEW_DATE`/`NEW_TIME`.
   `NEW_*` labels are **invalid in any other intent** (validator enforces).
5. `out_of_scope` has **no entities**, even if it contains a date ("who won the match yesterday").
6. Don't annotate words like "next", "last", "recent" as `DATE`; they are intent cues, not values.
7. Ambiguous sentence? Write it down and decide together once, then stay consistent.

## Growing it (honest sizing)

The 54 seed rows exist to fix the **format** and prove the tooling, not to train on. Some guidance:

- For fine-tuning a small transformer, aim for roughly **40-60 examples per intent**
  (~500-800 total) before trusting the numbers; with fewer, F1 on a tiny test set swings wildly.
- **Keep the test split handwritten.** Template/synthetic rows are fine for `train`, but if test
  comes from the same templates you'll measure template memorisation, not understanding.
- Collect real phrasing from classmates/teachers (`source: student_contributed`) for `test`.
- **Never put real student names, roll numbers or real attendance data in this file.**
  Use made-up values; this repo is public.
- The Hinglish rows were written quickly: have a native speaker on the team review spelling/phrasing.

## Baselines to report (your synopsis asks for baseline comparison)

1. **Keyword rules** = the current `if "x" in message` chain in `ai_service.py` (run it on `dev`/`test`).
2. **TF-IDF + logistic regression** for intent (a few lines of scikit-learn).
3. **Fine-tuned small transformer** (e.g. DistilBERT) for joint intent + token tagging.

Report intent accuracy / macro-F1 and entity span-level precision/recall/F1 for each, on `test` only.
