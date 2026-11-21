# Bed by Midnight Stage 1 local prototype

This is a small, offline starting point for ticket triage. Run with Python 3:
```
python -m unittest -v
python triage.py /path/to/tickets.csv
```

The second command expects `ticket_id`, `guest_requested`, and `guest_message`. It produces JSON routing suggestions. It deliberately ignores `expected_outcome`; that field can be used for later evaluation but must not influence classification. The package contains synthetic tests only and no guest records.

Safety signals override the requested remedy. Injury/medical need, threat/violence, nowhere safe to wait, an unaccompanied minor, or stated fear of a person must go to a live safety agent. The prototype cannot book, issue holds, issue refunds or send any messages. Blank or conflicting requests go to human review.

This is a keyword baseline, not a deployable safety classifier. It can miss paraphrases or misread context, negation, and other languages. It does not yet use structured booking context to determine whether routine remedies are eligible. The baseline was verified only on synthetic tests. Add difficult or masked synthetic safety cases before drawing conclusions about accuracy.

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
