"""Validate examples.jsonl against taxonomy.json. Exit code 1 on any error.

    python data/intent/validate.py
"""
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).parent


def main() -> int:
    tax = json.loads((HERE / "taxonomy.json").read_text())
    intents = set(tax["intents"])
    labels = set(tax["entity_labels"])
    splits, langs, sources = set(tax["splits"]), set(tax["langs"]), set(tax["sources"])
    reschedule_only = {"NEW_DATE", "NEW_TIME"}

    errors, seen_ids = [], set()
    group_splits = defaultdict(set)
    text_splits = defaultdict(set)
    counts = Counter()

    for n, line in enumerate((HERE / "examples.jsonl").read_text().splitlines(), 1):
        if not line.strip():
            continue

        try:
            r = json.loads(line)
        except json.JSONDecodeError as e:
            errors.append(f"line {n}: invalid JSON ({e})")
            continue

        where = f"line {n} ({r.get('id', '?')})"

        for key in ("id", "text", "lang", "intent", "entities", "group", "split", "source"):
            if key not in r:
                errors.append(f"{where}: missing '{key}'")
        if any(k not in r for k in ("text", "intent", "entities", "split", "group")):
            continue

        if r["id"] in seen_ids:
            errors.append(f"{where}: duplicate id")
        seen_ids.add(r["id"])

        if r["intent"] not in intents:
            errors.append(f"{where}: unknown intent '{r['intent']}'")
        if r["split"] not in splits:
            errors.append(f"{where}: bad split '{r['split']}'")
        if r["lang"] not in langs:
            errors.append(f"{where}: bad lang '{r['lang']}'")
        if r["source"] not in sources:
            errors.append(f"{where}: bad source '{r['source']}'")
        if not r["text"].strip() or r["text"] != r["text"].strip():
            errors.append(f"{where}: text empty or has leading/trailing whitespace")

        spans = []
        for e in r["entities"]:
            s, t, lab = e["start"], e["end"], e["label"]

            if lab not in labels:
                errors.append(f"{where}: unknown entity label '{lab}'")
            if not (0 <= s < t <= len(r["text"])):
                errors.append(f"{where}: span [{s},{t}) out of range")
                continue
            if r["text"][s:t] != e["text"]:
                errors.append(f"{where}: offsets [{s},{t}) give {r['text'][s:t]!r}, entity says {e['text']!r}")
            if lab in reschedule_only and r["intent"] != "reschedule_class":
                errors.append(f"{where}: {lab} is only allowed in reschedule_class")
            spans.append((s, t))

        spans.sort()
        for (s1, t1), (s2, t2) in zip(spans, spans[1:]):
            if s2 < t1:
                errors.append(f"{where}: overlapping entities")

        if r["intent"] == "out_of_scope" and r["entities"]:
            errors.append(f"{where}: out_of_scope must have no entities")

        group_splits[r["group"]].add(r["split"])
        text_splits[r["text"].lower()].add(r["split"])
        counts[(r["intent"], r["split"])] += 1

    # Leakage: paraphrases of one base sentence must not straddle splits.
    for g, ss in group_splits.items():
        if len(ss) > 1:
            errors.append(f"group '{g}' appears in multiple splits {sorted(ss)} (leakage)")
    for t, ss in text_splits.items():
        if len(ss) > 1:
            errors.append(f"identical text in multiple splits {sorted(ss)}: {t!r}")

    print(f"{'intent':28s} " + " ".join(f"{s:>5s}" for s in sorted(splits)))
    for intent in sorted(intents):
        print(f"{intent:28s} " + " ".join(f"{counts[(intent, s)]:5d}" for s in sorted(splits)))
        missing = [s for s in sorted(splits) if counts[(intent, s)] == 0]
        if missing:
            print(f"  warning: no examples in {missing}")

    if errors:
        print(f"\n{len(errors)} ERROR(S):")
        for e in errors:
            print("  -", e)
        return 1

    print("\nOK: dataset is valid.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
