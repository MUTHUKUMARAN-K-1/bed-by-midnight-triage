# Bed by Midnight Stage 1 local prototype

This is a small, offline starting point for ticket triage. Run with Python 3:
```
python -m unittest -v
python triage.py /path/to/tickets.csv
```

The second command expects `ticket_id`, `guest_requested`, and `guest_message`. It produces JSON routing suggestions. It deliberately ignores `expected_outcome`; that field can be used for later evaluation but must not influence classification. The package contains synthetic tests only and no guest records.

Safety signals override the requested remedy. Injury/medical need, threat/violence, nowhere safe to wait, an unaccompanied minor, or stated fear of a person must go to a live safety agent. The prototype cannot book, issue holds, issue refunds or send any messages. Blank or conflicting requests go to human review.

This is a keyword baseline, not a deployable safety classifier. It can miss paraphrases or misread context, negation, and other languages. It does not yet use structured booking context to determine whether routine remedies are eligible. The baseline was verified only on synthetic tests. Add difficult or masked synthetic safety cases before drawing conclusions about accuracy.

## Offline evaluation

```sh
python evaluate.py /path/to/tickets.csv
python evaluate.py /path/to/tickets.csv --private-rows /private/path/results.private.json
```

Use a private UTF-8 CSV with `ticket_id`, `guest_requested`, `guest_message`, and `expected_outcome`. Use a unique, non-empty ticket ID in each data row. Expected labels are `safety` (also `safety handoff` or `handoff to safety agent`), `rebooking` (also `rebook`), or `refund`. Labels are case-insensitive and treat underscores and hyphens as spaces. Blank or unknown expected labels, duplicate IDs, malformed rows and an empty dataset fail evaluation instead of disappearing from the denominator. Expected labels are used only to score predictions, never to make them.

Only aggregate JSON goes to standard output. Confusion matrix rows are expected categories; columns are predictions, including `unresolved`. Safety recall is the fraction of expected safety cases correctly routed and is `null` when there are no expected safety cases. A safety case predicted as unresolved still counts as a safety false negative. Equal class totals do not establish accuracy. A high score on one set does not validate a safety system for real guests.

The optional second command writes a **new, private local file** containing `ticket_id`, `expected`, `ticket_type`, and `route`, but no guest message or request text. Keep the source and that file outside the checkout, do not share them, and commit only synthetic examples or approved aggregates. Common worksheet formats and private JSON exports are ignored by Git.

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
