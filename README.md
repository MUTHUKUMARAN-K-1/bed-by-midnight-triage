# Bed by Midnight Stage 1 local prototype

This is a small, offline starting point for ticket triage. Run with Python 3:
```
python -m unittest -v
python triage.py /path/to/tickets.csv
```

The second command expects `ticket_id`, `guest_requested`, and `guest_message`. It produces JSON routing suggestions. It deliberately ignores `expected_outcome`; that field can be used for later evaluation but must not influence classification. The package contains synthetic tests only and no guest records.

Safety signals override the requested remedy. Injury/medical need, threat/violence, nowhere safe to wait, an unaccompanied minor, or stated fear of a person must go to a live safety agent. The prototype cannot book, issue holds, issue refunds or send any messages. Blank or conflicting requests go to human review.

This is a keyword baseline, not a deployable safety classifier. It can miss paraphrases or misread context, negation, and other languages. It does not yet use structured booking context to determine whether routine remedies are eligible. The original 60-ticket worksheet was previewed separately in Zero; the original rows were not used to evaluate this code. Review and label the full worksheet and test difficult or masked safety cases before drawing conclusions about accuracy.
