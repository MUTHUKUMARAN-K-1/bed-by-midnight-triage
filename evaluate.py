"""Compare the existing triage baseline with labeled tickets, entirely offline."""
import argparse
import csv
import json
import re
from pathlib import Path

from triage import triage

EXPECTED = ("safety", "rebooking", "refund")
PREDICTED = (*EXPECTED, "unresolved")
FEATURES = ("ticket_id", "guest_requested", "guest_message")
REQUIRED = (*FEATURES, "expected_outcome")
ALIASES = {
    "safety": "safety",
    "safety handoff": "safety",
    "handoff to safety agent": "safety",
    "rebooking": "rebooking",
    "rebook": "rebooking",
    "refund": "refund",
}


class EvaluationError(ValueError):
    """An invalid input; error text deliberately excludes private cell contents."""


def evaluate(reader, include_rows=False):
    headers = reader.fieldnames or []
    if len(headers) != len(set(headers)) or not set(REQUIRED).issubset(headers):
        raise EvaluationError("CSV needs unique headers including " + ", ".join(REQUIRED) + ".")
    matrix = {actual: dict.fromkeys(PREDICTED, 0) for actual in EXPECTED}
    seen = set()
    private = []
    for row_number, row in enumerate(reader, 1):
        if None in row or any(value is None for value in row.values()):
            raise EvaluationError(f"Data row {row_number}: inconsistent number of columns.")
        ticket_id = row["ticket_id"].strip()
        if not ticket_id or ticket_id in seen:
            raise EvaluationError(f"Data row {row_number}: missing or duplicate ticket ID.")
        seen.add(ticket_id)
        raw_label = row["expected_outcome"].strip().casefold()
        label = re.sub(r"[_\-\s]+", " ", raw_label)
        actual = ALIASES.get(label)
        if not actual:
            raise EvaluationError(f"Data row {row_number}: missing or unknown expected_outcome.")

        result = triage({key: row[key] for key in FEATURES})
        predicted = result["ticket_type"]
        if predicted not in PREDICTED:
            raise EvaluationError(f"Data row {row_number}: classifier returned an unknown category.")
        matrix[actual][predicted] += 1
        if include_rows:
            private.append({"ticket_id": ticket_id, "expected": actual,
                            "ticket_type": predicted, "route": result["route"]})

    n = len(seen)
    if not n:
        raise EvaluationError("CSV had no ticket rows.")
    expected_counts = {actual: sum(matrix[actual].values()) for actual in EXPECTED}
    predicted_counts = {prediction: sum(line[prediction] for line in matrix.values()) for prediction in PREDICTED}
    correct = sum(matrix[label][label] for label in EXPECTED)
    safety_total = expected_counts["safety"]
    safety_tp = matrix["safety"]["safety"]
    report = {
        "row_count": n,
        "expected_counts": expected_counts,
        "predicted_counts": predicted_counts,
        "confusion_matrix": matrix,
        "correct": correct,
        "accuracy": correct / n,
        "safety": {
            "actual_positives": safety_total,
            "true_positives": safety_tp,
            "false_negatives": safety_total - safety_tp,
            "false_positives": predicted_counts["safety"] - safety_tp,
            "recall": safety_tp / safety_total if safety_total else None,
        },
    }
    return report, private


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("tickets", type=Path)
    parser.add_argument("--private-rows", type=Path, metavar="FILE.private.json",
                        help="Opt in to a new ID-bearing local JSON file (not for sharing).")
    args = parser.parse_args(argv)
    if args.private_rows and not args.private_rows.name.endswith(".private.json"):
        parser.error("--private-rows filename must end in .private.json.")
    try:
        with args.tickets.open(encoding="utf-8-sig", newline="") as source:
            report, private = evaluate(csv.DictReader(source, strict=True), bool(args.private_rows))
        if args.private_rows:
            # Exclusive creation: never overwrite an existing file or the source.
            with args.private_rows.open("x", encoding="utf-8") as destination:
                json.dump(private, destination, indent=2)
                destination.write("\n")
    except EvaluationError as exc:
        parser.exit(2, f"Evaluation failed: {exc}\n")
    except (OSError, UnicodeError, csv.Error):
        parser.exit(2, "Evaluation failed: could not read valid UTF-8 CSV or create the private results file.\n")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
