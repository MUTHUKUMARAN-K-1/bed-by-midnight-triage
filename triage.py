"""Stage 1 local routing prototype. No external integrations or actions."""
import argparse
import csv
import json
import re
from pathlib import Path

# Evidence in the guest message overrides the requested remedy.
# Multi-cue rules require context, not just a health condition, a callback,
# an age, or a stand-alone word such as "followed".
SAFETY = {
    "injury_or_medical_need": (
        r"\b(?:injured|bleeding|medical (?:help|emergency)|need an ambulance|can't breathe|cannot breathe)\b"
        r"|^(?=.*\b(?:diabet(?:ic|es)|low blood sugar)\b)"
        r"(?=.*\b(?:pale|shaky|faint|confused|dizzy|passed out)\b)"
        r".*\b(?:(?:has|have|had) ?(?:n't| not) eaten|missed (?:a|his|her|their) meal|"
        r"went without food|need(?:s|ed)? to lie down)\b"
    ),
    "threat_or_violence": r"\b(?:threaten(?:ed|ing|s)?|attacked|assault(?:ed)?|violent|has a weapon)\b",
    "nowhere_safe_to_wait": r"\b(?:nowhere safe|no safe place|not safe to wait|no(?:where)? safe (?:place )?to wait)\b",
    "unaccompanied_minor": (
        r"\b(?:unaccompanied minor|child (?:is )?alone|minor (?:is )?alone|(?:[1-9]|1[0-7])[- ]year[- ]old (?:is )?alone)\b"
        r"|^(?=.*\b(?:(?:i'm|i am)\s+(?:[1-9]|1[0-7])\s*(?:years? old\b|(?:and|but)\b|[.,;!?:]|$)|"
        r"(?:aged?|(?:i'm|i am) aged)\s+(?:[1-9]|1[0-7])\b))"
        r".*\b(?:on my own|by myself|alone|without (?:a|an|my) (?:adult|guardian|parent))\b"
    ),
    "fear_of_a_person": (
        r"\b(?:afraid|scared|terrified) of (?:the |my |a )?(?:host|person|man|woman|driver|him|her|them)\b"
        r"|^(?=.*\b(?:afraid|scared|terrified|frightened)\b)"
        r".*\b(?:someone|(?:a|the|some|that) (?:man|woman|person|stranger|driver))"
        r"\s+(?:(?:has|is|was|keeps)\s+)?follow(?:ed|ing|s)\s+(?:me|us)\b"
    ),
}
ROUTINE = {
    "rebooking": r"\b(?:rebook(?:ing)?|replacement|alternative (?:stay|accommodation)|another (?:room|place|listing|stay)|new place)\b",
    "refund": r"\b(?:refund(?:ed)?|reimburse(?:ment)?|money back)\b",
}

def triage(row):
    message = str(row.get("guest_message") or "").casefold().replace("’", "'")
    requested = str(row.get("guest_requested") or "").casefold()
    signals = [name for name, pattern in SAFETY.items() if re.search(pattern, message, re.DOTALL)]
    result = {"ticket_id": row.get("ticket_id"), "next_action": "no_action_executed"}
    if signals:
        return dict(result, ticket_type="safety", route="handoff_to_safety_agent",
                    matched_signals=signals, hold_allowed=False, refund_allowed=False)
    matches = [name for name, pattern in ROUTINE.items() if re.search(pattern, requested)]
    if len(matches) == 1 and message:
        return dict(result, ticket_type=matches[0], route="routine_review", matched_signals=[])
    return dict(result, ticket_type="unresolved", route="human_review", matched_signals=[],
                hold_allowed=False, refund_allowed=False)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("tickets", type=Path)
    args = parser.parse_args()
    with args.tickets.open(encoding="utf-8-sig", newline="") as f:
        rows = csv.DictReader(f)
        required = {"ticket_id", "guest_requested", "guest_message"}
        if not required.issubset(rows.fieldnames or []):
            raise SystemExit("CSV must have ticket_id, guest_requested and guest_message columns.")
        print(json.dumps([triage(row) for row in rows], indent=2, ensure_ascii=False))
