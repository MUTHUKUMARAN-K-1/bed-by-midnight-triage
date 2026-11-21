import unittest
from triage import triage

class TriageTests(unittest.TestCase):
    def ticket(self, message, request="refund"):
        return triage(dict(ticket_id="synthetic", guest_message=message, guest_requested=request))

    def test_each_safety_trigger_overrides_refund(self):
        examples = {
            "injury_or_medical_need": "I'm injured.",
            "threat_or_violence": "The host threatened me.",
            "nowhere_safe_to_wait": "I have nowhere safe to wait.",
            "unaccompanied_minor": "The child is alone.",
            "fear_of_a_person": "I'm afraid of the host.",
        }
        for key, message in examples.items():
            with self.subTest(signal=key):
                x = self.ticket(message)
                self.assertEqual(x["ticket_type"], "safety")
                self.assertEqual(x["route"], "handoff_to_safety_agent")
                self.assertEqual(x["matched_signals"], [key])
                self.assertFalse(x["hold_allowed"])
                self.assertFalse(x["refund_allowed"])

    def test_safety_overrides_rebooking(self):
        self.assertEqual(self.ticket("I was attacked.", "rebook")["ticket_type"], "safety")

    def test_routine_refund(self):
        self.assertEqual(self.ticket("The trip was cancelled.")["ticket_type"], "refund")

    def test_routine_rebooking(self):
        self.assertEqual(self.ticket("Our booking was cancelled.", "rebook")["ticket_type"], "rebooking")

    def test_ambiguous_or_missing_routes_to_human(self):
        for message, request in [("Cancelled.", "rebook or refund"), ("", "refund"), ("Need help.", "")]:
            with self.subTest(message=message, request=request):
                self.assertEqual(self.ticket(message, request)["route"], "human_review")

    def test_contextual_safety_paraphrases(self):
        examples = [
            ("My sibling has diabetes and feels shaky after they missed a meal.", "injury_or_medical_need"),
            ("A stranger keeps following us. We are frightened.", "fear_of_a_person"),
            ("I am 13 years old. I need to wait here without a guardian.", "unaccompanied_minor"),
            ("I'm 17 and staying here by myself.", "unaccompanied_minor"),
        ]
        for message, signal in examples:
            with self.subTest(signal=signal):
                for request in ("refund", "rebook", ""):
                    r = self.ticket(message, request=request)
                    self.assertEqual(r["ticket_type"], "safety")
                    self.assertEqual(r["route"], "handoff_to_safety_agent")
                    self.assertIn(signal, r["matched_signals"])
                    self.assertEqual(r["next_action"], "no_action_executed")
                    self.assertFalse(r["hold_allowed"])
                    self.assertFalse(r["refund_allowed"])

    def test_ordinary_anger_callback_and_isolated_words_are_not_safety(self):
        examples = [
            "I am furious about the cancellation. Have a manager call me back.",
            "I have diabetes. Please call when the replacement is ready.",
            "A person followed the directions but the property was closed.",
            "I am 29 years old and I am travelling by myself.",
            "I am 14 minutes late and standing here by myself.",
            "I am 15 years old and I am here with my parent.",
        ]
        for message in examples:
            with self.subTest(message=message):
                self.assertEqual(self.ticket(message)["ticket_type"], "refund")
                self.assertEqual(self.ticket(message, request="")["route"], "human_review")

    def test_label_not_used(self):
        result = triage(dict(ticket_id="synthetic", guest_message="Need help.", guest_requested="",
                             expected_outcome="refund"))
        self.assertEqual(result["ticket_type"], "unresolved")

if __name__ == "__main__":
    unittest.main()
