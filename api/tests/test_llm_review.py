import os
import tempfile
import unittest

db_file = tempfile.NamedTemporaryFile(delete=False)
db_file.close()
os.environ.setdefault("DATABASE_URL", f"sqlite:///{db_file.name}")
os.environ.setdefault("AUTO_CREATE_TABLES", "true")

from api.llm_review import build_fallback_review_packet, normalize_evaluation


class LlmReviewTest(unittest.TestCase):
    def test_normalize_evaluation_defaults_unknown_status_to_unclear(self) -> None:
        normalized = normalize_evaluation(
            {
                "answer_status": "maybe",
                "evidence_quote": " customer quote ",
                "evaluator_notes": " needs detail ",
                "follow_up_question": " Can you clarify? ",
            }
        )

        self.assertEqual(normalized["answer_status"], "unclear")
        self.assertEqual(normalized["evidence_quote"], "customer quote")
        self.assertEqual(normalized["evaluator_notes"], "needs detail")
        self.assertEqual(normalized["follow_up_question"], "Can you clarify?")

    def test_fallback_review_packet_flags_incomplete_answers(self) -> None:
        packet = build_fallback_review_packet(
            [{"id": "q1", "question_text": "What changed?"}],
            {
                "q1": {
                    "answer_text": "Not sure",
                    "answer_status": "unclear",
                    "follow_up_asked": True,
                }
            },
            [{"question_text": "When will I hear back?", "needs_human_followup": True}],
        )

        self.assertEqual(packet["answers"][0]["answer_status"], "unclear")
        self.assertEqual(packet["follow_up_needed"][0]["question_id"], "q1")
        self.assertEqual(packet["customer_questions"][0]["question_text"], "When will I hear back?")


if __name__ == "__main__":
    unittest.main()
