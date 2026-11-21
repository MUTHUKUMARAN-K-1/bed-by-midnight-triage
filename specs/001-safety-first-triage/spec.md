# Feature Specification: Safety-first booking support triage

**Feature branch**: `001-safety-first-triage`
**Status**: Draft for review
**Scope**: Offline routing recommendations using synthetic fixtures only. This specification is a proposed target, not a claim about the current implementation.

## User Scenarios & Testing

### User Story 1 — Reach a live safety agent before any remedy (P1)

A guest whose message or permitted booking context indicates actual or possible danger gets a live safety-agent recommendation, even if they request a rebooking, refund or callback. The recommendation does not itself send a message, make a booking hold or issue a refund.

**Independent test**: Submit a synthetic conversation for each signal, paired separately with requests for rebooking and refund. All must propose the safety queue and mark both actions disallowed.

| Reason code | Signal family | Why it comes before routine remedies |
|---|---|---|
| `injury_or_medical_need` | Current injury or indication that medical attention may be needed | Booking changes cannot assess the guest's health or provide urgent human assistance. |
| `threat_or_violence` | A threat, violence, coercion or a credible indication of imminent harm | A financial or inventory action does not address ongoing danger and could delay intervention. |
| `nowhere_safe_to_wait` | No safe place to wait, including uncertainty about safe shelter | The guest needs immediate human assessment of where they can wait safely, not merely a transaction. |
| `unaccompanied_minor` | A minor appears to be on their own without responsible adult support | This requires safeguarding assessment by a person rather than a standard remedy workflow. |
| `fear_of_a_person` | Guest says or implies they fear a person relevant to the situation | A person may pose a present risk even without an explicit report of a threat or assault. |

**Acceptance scenarios**

1. **Given** a refund request and a current injury signal, **when** triage reads the case, **then** it recommends live safety handoff before either remedy.
2. **Given** a rebooking request and ambiguous but plausible danger, **when** triage cannot safely rule it out, **then** it recommends live safety review and blocks any routine remedy recommendation pending review.
3. **Given** several signals, **when** triage routes the case, **then** it retains each supported reason, does not invent a reason from the requested remedy, and still returns one safety route.
4. **Given** clearly historical or explicitly negated unsafe wording and no credible current danger in context, **when** triage evaluates it, **then** it must not treat the isolated keyword alone as evidence. Genuine doubt about current safety still goes to live safety review.
5. **Given** routing evidence is absent, unavailable, or unreadable, **when** safety cannot be assessed, **then** do not authorize any routine remedy. Route to human review, or live safety review if known details suggest a credible safety concern.

### User Story 2 — Route routine rebook or refund without making a commitment (P2)

A guest with no safety concern and a clear routine request is sent to the appropriate review path. A recommendation is not an authorization or a promise of remedy. Eligibility depends on separately confirmed policies and booking state.

**Independent test**: With synthetic requests and no known safety issue, verify one rebook case and one refund case route to routine review with different remedy labels and no action executed.

1. **Given** a confirmed routine request for replacement accommodation or rebook, **when** safety is clear, **then** propose rebooking review; do not make or hold a booking.
2. **Given** a confirmed routine request for refund and no safety signal, **when** routed, **then** propose refund review; do not issue or promise a refund.
3. **Given** anger, strong dissatisfaction or a callback request alone, **when** there is no independent safety evidence, **then** do not classify as safety. Use the clear routine remedy if one exists; otherwise human review.
4. **Given** a blank, conflicting or uncertain remedy and no credible safety concern, **when** triage runs, **then** offer human review without either remedy.

### User Story 3 — Audit the routing suggestion (P3)

A reviewer can understand how a synthetic case was routed without needing private guest data or trusting an unexplained label.

**Independent test**: Verify that each synthetic case returns an opaque synthetic ticket ID, route and specific reason code, and that changing an evaluation-only expected label cannot change the result. Nominal cases and near misses remain reproducible.

## Requirements

- **FR-001**: Apply this priority: credible or plausibly ambiguous safety → live safety agent; otherwise one clear routine request → rebooking or refund review; otherwise human review.
- **FR-002**: Differentiate safety uncertainty from ordinary remedy uncertainty. Both block execution, but the former is higher priority and requires a live safety-capable reviewer.
- **FR-003**: Use the supplied conversation and minimal permitted booking context, when available, to evaluate current danger and review eligibility. Never infer facts from absent context. Comparison of latest message, history and booking flags is a future capability, not present in the keyword baseline.
- **FR-004**: On potential safety, do not create a booking or hold, issue or promise a refund, or send any communication automatically. Do not require the guest to prove danger as a condition for review.
- **FR-005**: Treat angry tone and the request to be called as non-safety signals by themselves. They must not override credible accompanying safety facts.
- **FR-006**: Return a recommendation, a stable reason or matched reasons, and a marker that no action was executed. Distinguish a routine suggestion from confirmation of eligibility.
- **FR-007**: Keep any `expected_outcome` field isolated from routing inputs to prevent label leakage.
- **FR-008**: Use only synthetic fixtures in the repo, development, evaluation and demos. Do not copy guest names, actual conversations, booking IDs, credentials or proprietary evaluation data. Do not connect to guest messaging, payment, booking or live queue systems.
- **FR-009**: Record prototype limitations honestly. Any future context-aware classifier must be separately evaluated with synthetic masked wording, paraphrases, negation, historical mentions, mixed signals and missing-context cases. No production rollout or accuracy guarantee is part of this spec.

### Key Entities

- **Ticket**: Opaque ID, stated remedy if any, normalized guest message and, in future revisions only, minimal permitted booking context.
- **Routing recommendation**: Safety, rebooking review, refund review or human review; matched reason codes; no action executed.
- **Synthetic test case**: Fabricated ticket inputs and a separately held expected route; no real case details.

## Success Criteria

- **SC-001**: Each of the five synthetic safety families, paired with both rebook and refund, produces a live safety review recommendation with neither remedy allowed; zero synthetic safety cases may enter the routine route.
- **SC-002**: The synthetic mixed corpus correctly distinguishes clear routine remedies, angry/callback-only cases, ambiguous safety, and ambiguous remedies. Review every safety false negative before declaring the planned classifier ready.
- **SC-003**: Repeating each synthetic case with altered evaluation-only metadata does not change its route. No case executes a booking, refund, notification, or external call.
- **SC-004**: Tests and docs clearly distinguish the passing keyword baseline from future acceptance cases for contextual inference; do not claim future acceptance coverage based on current test pass count.

## Out of Scope

Booking/payment execution, live notifications, safety policy operations, use of real records, selecting or deploying an LLM, and evaluating production accuracy. The current Python prototype is unchanged by this specification.
