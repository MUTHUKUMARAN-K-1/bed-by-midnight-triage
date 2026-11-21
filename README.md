# Bed by Midnight Stage 1 local prototype

This is a small, offline starting point for ticket triage. Run with Python 3:
```
python -m unittest -v
python triage.py /path/to/tickets.csv
```

The second command expects `ticket_id`, `guest_requested`, and `guest_message`. It produces JSON routing suggestions. It deliberately ignores `expected_outcome`; that field can be used for later evaluation but must not influence classification. The package contains synthetic tests only and no guest records.

Safety signals override the requested remedy. Injury/medical need, threat/violence, nowhere safe to wait, an unaccompanied minor, or stated fear of a person must go to a live safety agent. The prototype cannot book, issue holds, issue refunds or send any messages. Blank or conflicting requests go to human review.

This is a keyword baseline, not a deployable safety classifier. It can miss paraphrases or misread context, negation, and other languages. It does not yet use structured booking context to determine whether routine remedies are eligible. The synthetic tests and labeled worksheet checks below are not substitutes for independent safety testing.

## Offline evaluation

```sh
python evaluate.py /path/to/tickets.csv
python evaluate.py /path/to/tickets.csv --private-rows /private/path/results.private.json
```

Use a private UTF-8 CSV with `ticket_id`, `guest_requested`, `guest_message`, and `expected_outcome`. Use a unique, non-empty ticket ID in each data row. Expected labels are `safety` (also `safety handoff` or `handoff to safety agent`), `rebooking` (also `rebook`), or `refund`. Labels are case-insensitive and treat underscores and hyphens as spaces. Blank or unknown expected labels, duplicate IDs, malformed rows and an empty dataset fail evaluation instead of disappearing from the denominator. Expected labels are used only to score predictions, never to make them.

Only aggregate JSON goes to standard output. Confusion matrix rows are expected categories; columns are predictions, including `unresolved`. Safety recall is the fraction of expected safety cases correctly routed and is `null` when there are no expected safety cases. A safety case predicted as unresolved still counts as a safety false negative. Equal class totals do not establish accuracy. A high score on one set does not validate a safety system for real guests.

The optional second command writes a **new, private local file** containing `ticket_id`, `expected`, `ticket_type`, and `route`, but no guest message or request text. Keep the source and that file outside the checkout, do not share them, and commit only synthetic examples or approved aggregates. Common worksheet formats and private JSON exports are ignored by Git.

### Labeled worksheet baseline

The unchanged keyword classifier at commit [`7b90aaf`](https://github.com/MUTHUKUMARAN-K-1/bed-by-midnight-triage/commit/7b90aaf19d114da5d542a31159c4e592cc6fedc4) was run offline on all 60 unique rows of a supplied labeled worksheet. The raw worksheet and per-ticket baseline predictions are not included.

| Expected ↓ / Predicted → | Safety | Rebooking | Refund | Unresolved | Expected total |
| --- | ---: | ---: | ---: | ---: | ---: |
| Safety | 3 | 1 | 1 | 1 | 6 |
| Rebooking | 0 | 28 | 0 | 6 | 34 |
| Refund | 0 | 0 | 20 | 0 | 20 |
| Predicted total | 3 | 29 | 21 | 7 | 60 |

The baseline matched 51/60 labels (85% accuracy). It caught only 3/6 safety cases (50% recall): three safety false negatives, including two routed to routine remedy review and one routed to generic human review. It produced no safety false positives on this worksheet. This is one small evaluation of a keyword baseline, not a production safety validation; do not use the result to justify automatic routing or remedies for real guests. [Aggregate JSON](evaluation/worksheet-baseline.json).

### Targeted safety update: in-sample replay

After reviewing the three missed safety labels, the rules were extended to recognize three combinations: a blood-sugar/diabetes cue alongside acute symptoms and relevant context; fear alongside a person following the guest; and a person identifying themselves as under 18 and alone. Anger and a callback request alone are not safety triggers. These rules still act on message text and do not execute remedies.

| Measure on the same 60 rows | Original baseline | After targeted update |
| --- | ---: | ---: |
| Correct labels | 51/60 (85%) | 54/60 (90%) |
| Safety recall | 3/6 (50%) | 6/6 (100%) |
| Safety false negatives | 3 | 0 |
| Safety false positives | 0 | 0 |
| Rebooking labels matched | 28/34 | 28/34 |
| Refund labels matched | 20/20 | 20/20 |

The six remaining misses were expected rebookings routed to generic human review. The after result is **in-sample**: it uses the same worksheet that informed the changes, not a holdout set or evidence of production readiness. See the [replay aggregate](evaluation/worksheet-tuned.json).

The [review routing list](evaluation/worksheet-routing-results.json) preserves the 60 original scenario ticket IDs and the worksheet order. Each row contains only `ticket_id`, `ticket_type`, and `route`. All six rows classified as safety use `handoff_to_safety_agent`. The raw worksheet, guest messages, guest names and booking references are not included. The earlier [shuffled study results](evaluation/worksheet-study-results.json) remain for reference.

## Spec Kit (Claude Code)

This repository is scaffolded with [official GitHub Spec Kit v1.4.3](https://github.com/github/spec-kit/releases/tag/v1.4.3), using the Claude Code integration and PowerShell scripts. The starting draft is [Safety-first booking support triage](specs/001-safety-first-triage/spec.md). The specification is not implemented or evaluated by adding these files.

To plan against the existing draft on Windows, start PowerShell at the repository root and set:
```powershell
$env:SPECIFY_FEATURE_DIRECTORY = 'specs/001-safety-first-triage'
claude
```
Inside Claude Code, review the draft and invoke `/speckit-plan` with any decisions or constraints you want captured. Run `/speckit-tasks` only after reviewing that plan. Claude Code is a separate tool and must already be installed and signed in; it was not run to scaffold this repository.

For reproducibility, the scaffold was initialized using the official tagged source:
```powershell
uvx --from 'git+https://github.com/github/spec-kit.git@v1.4.3' specify init --here --force --non-interactive --ignore-agent-tools --integration claude --script ps --integration-options='--events false'
```
Use that init command only for a fresh, isolated copy or after reviewing the files it may merge or replace. Project-local event hooks were disabled at setup.
