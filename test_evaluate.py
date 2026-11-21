import contextlib
import csv
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from evaluate import EvaluationError, evaluate, main


HEADER = "ticket_id,guest_requested,guest_message,expected_outcome\n"
SWAPPED = HEADER + (
    "SYN-1,rebook,I cannot stay here because of what just happened,safety\n"
    "SYN-2,rebook,A stranger attacked me,rebooking\n"
    "SYN-3,refund,The booking was cancelled,Refund\n"
)


def read(content):
    return csv.DictReader(io.StringIO(content), strict=True)


class EvaluationTests(unittest.TestCase):
    def test_matching_totals_do_not_hide_missed_safety(self):
        report, rows = evaluate(read(SWAPPED))
        expected = report["expected_counts"]
        self.assertEqual(report["predicted_counts"], dict(expected, unresolved=0))
        self.assertEqual(report["correct"], 1)
        self.assertEqual(report["confusion_matrix"]["safety"]["rebooking"], 1)
        self.assertEqual(report["safety"], {
            "actual_positives": 1, "true_positives": 0, "false_negatives": 1,
            "false_positives": 1, "recall": 0.0,
        })
        self.assertEqual(rows, [])
        self.assertNotIn("SYN-", json.dumps(report))

    def test_expected_label_and_extra_fields_are_never_features(self):
        content = HEADER.rstrip() + ",notes\nSYN-1,,The property was cancelled,Safety_Handoff,medical emergency\n"
        with patch("evaluate.triage", return_value={"ticket_type": "unresolved"}) as classifier:
            report, _ = evaluate(read(content))
        classifier.assert_called_once_with({
            "ticket_id": "SYN-1", "guest_requested": "", "guest_message": "The property was cancelled",
        })
        self.assertEqual(report["confusion_matrix"]["safety"]["unresolved"], 1)
        self.assertEqual(report["safety"]["false_negatives"], 1)

    def test_no_safety_cases_has_undefined_recall(self):
        report, _ = evaluate(read(HEADER + "SYN-1,rebook,The address is unavailable,rebook\n"))
        self.assertIsNone(report["safety"]["recall"])
        self.assertEqual(report["accuracy"], 1.0)

    def test_invalid_csv_fails_without_echoing_ids_or_labels(self):
        sample = "SYN-1,rebook,The address is unavailable,rebooking\n"
        cases = (
            (HEADER, "no ticket rows"),
            (HEADER + sample + sample, "missing or duplicate"),
            (HEADER + sample + " SYN-1 ,refund,Cancelled,refund\n", "missing or duplicate"),
            (HEADER + ",rebook,The address is unavailable,rebooking\n", "missing or duplicate"),
            (HEADER + "SYN-2,refund,Cancelled,\n", "missing or unknown"),
            (HEADER + "SYN-2,refund,Cancelled,EXTRA-PRIVATE\n", "missing or unknown"),
            (HEADER + "SYN-1,refund,Cancelled\n", "inconsistent"),
            (HEADER + "SYN-1,refund,Cancelled,refund,extra\n", "inconsistent"),
            ("ticket_id,guest_requested,guest_message,ticket_id\n", "unique headers"),
        )
        for content, reason in cases:
            with self.subTest(reason=reason):
                with self.assertRaisesRegex(EvaluationError, reason) as result:
                    evaluate(read(content))
                self.assertNotIn("SYN-", str(result.exception))
                self.assertNotIn("EXTRA-PRIVATE", str(result.exception))

    def test_private_output_is_optional_and_does_not_overwrite(self):
        with tempfile.TemporaryDirectory() as dirname:
            source = Path(dirname) / "tickets.csv"
            private = Path(dirname) / "results.private.json"
            source.write_text(SWAPPED, encoding="utf-8-sig")
            with contextlib.redirect_stdout(io.StringIO()) as stdout:
                self.assertEqual(main([str(source)]), 0)
            self.assertFalse(private.exists())
            self.assertNotIn(str(source), stdout.getvalue())
            self.assertNotIn("SYN-", stdout.getvalue())
            with contextlib.redirect_stdout(io.StringIO()) as stdout:
                self.assertEqual(main([str(source), "--private-rows", str(private)]), 0)
            self.assertEqual(json.loads(stdout.getvalue())["row_count"], 3)
            saved = private.read_text()
            self.assertEqual(json.loads(saved)[0], {
                "ticket_id": "SYN-1", "expected": "safety", "ticket_type": "rebooking",
                "route": "routine_review",
            })
            self.assertNotIn("A stranger attacked me", saved)
            with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                main([str(source), "--private-rows", str(private)])
            self.assertEqual(private.read_text(), saved)
