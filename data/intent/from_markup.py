"""Convert examples_marked.tsv (easy for humans to edit) into examples.jsonl
(what the model trains on), computing character offsets automatically.

Write entities inline as [[text|LABEL]]:
    cancel [[tomorrow|DATE]]'s [[DBMS|COURSE]] class

Run from anywhere:  python data/intent/from_markup.py
"""
import json
import re
from pathlib import Path

HERE = Path(__file__).parent
MARK = re.compile(r"\[\[(.+?)\|([A-Z_]+)\]\]")


def parse(marked: str):
    text_parts, entities, cursor, out_len = [], [], 0, 0

    for m in MARK.finditer(marked):
        plain = marked[cursor:m.start()]
        text_parts.append(plain)
        out_len += len(plain)

        span, label = m.group(1), m.group(2)
        entities.append(
            {"start": out_len, "end": out_len + len(span), "label": label, "text": span}
        )
        text_parts.append(span)
        out_len += len(span)
        cursor = m.end()

    text_parts.append(marked[cursor:])
    return "".join(text_parts), entities


def main():
    records = []

    for line_no, line in enumerate((HERE / "examples_marked.tsv").read_text().splitlines(), 1):
        if not line.strip() or line.startswith("#"):
            continue

        cols = line.split("\t")
        if len(cols) != 6:
            raise SystemExit(f"line {line_no}: expected 6 tab-separated columns, got {len(cols)}")

        split, group, source, lang, intent, marked = cols
        text, entities = parse(marked)

        records.append(
            {
                "id": f"ex-{len(records) + 1:04d}",
                "text": text,
                "lang": lang,
                "intent": intent,
                "entities": entities,
                "group": group,
                "split": split,
                "source": source,
            }
        )

    with open(HERE / "examples.jsonl", "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    print(f"wrote {len(records)} examples -> {HERE / 'examples.jsonl'}")


if __name__ == "__main__":
    main()
