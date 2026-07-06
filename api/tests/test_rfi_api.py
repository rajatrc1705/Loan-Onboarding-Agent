import os
import tempfile
import unittest

db_file = tempfile.NamedTemporaryFile(delete=False)
db_file.close()
os.environ["DATABASE_URL"] = f"sqlite:///{db_file.name}"
os.environ["AUTO_CREATE_TABLES"] = "true"

from fastapi.testclient import TestClient  # noqa: E402

from api.main import app  # noqa: E402


class RfiApiTest(unittest.TestCase):
    def test_structured_call_review_records_are_exposed_on_detail(self) -> None:
        with TestClient(app) as client:
            created = client.post(
                "/rfi",
                json={"customer_email": "customer@example.com", "application_id": None},
            )
            self.assertEqual(created.status_code, 200, created.text)
            rfi_id = created.json()["id"]

            questions_response = client.put(
                f"/rfi/{rfi_id}/questions",
                json={
                    "questions": [
                        {
                            "order_index": 1,
                            "question_text": "Why did revenue dip last quarter?",
                        }
                    ]
                },
            )
            self.assertEqual(questions_response.status_code, 200, questions_response.text)
            question_id = questions_response.json()[0]["id"]

            answers_response = client.post(
                f"/rfi/{rfi_id}/answers",
                json={
                    "answers": [
                        {
                            "question_id": question_id,
                            "answer_text": "A major customer delayed payment.",
                            "answer_status": "answered",
                            "evidence_quote": "major customer delayed payment",
                            "follow_up_asked": False,
                            "evaluator_notes": "Directly answers the question.",
                            "captured_by": "agent",
                        }
                    ]
                },
            )
            self.assertEqual(answers_response.status_code, 200, answers_response.text)

            customer_questions_response = client.post(
                f"/rfi/{rfi_id}/customer-questions",
                json={
                    "questions": [
                        {
                            "question_text": "When will the team review this?",
                            "agent_response": "The team will review it after the call.",
                            "needs_human_followup": False,
                        }
                    ]
                },
            )
            self.assertEqual(
                customer_questions_response.status_code,
                200,
                customer_questions_response.text,
            )

            transcript_response = client.post(
                f"/rfi/{rfi_id}/transcript",
                json={
                    "turns": [
                        {
                            "speaker": "customer",
                            "text": "A major customer delayed payment.",
                        }
                    ]
                },
            )
            self.assertEqual(transcript_response.status_code, 200, transcript_response.text)

            summary_response = client.post(
                f"/rfi/{rfi_id}/summary",
                json={
                    "summary_text": "Revenue dip was explained.",
                    "structured_json": {
                        "short_summary": "Revenue dip was explained.",
                        "answers": [],
                        "customer_questions": [],
                        "follow_up_needed": [],
                    },
                    "needs_review": False,
                    "review_reason": None,
                },
            )
            self.assertEqual(summary_response.status_code, 200, summary_response.text)

            detail_response = client.get(f"/rfi/{rfi_id}")
            self.assertEqual(detail_response.status_code, 200, detail_response.text)
            detail = detail_response.json()
            self.assertEqual(detail["status"], "DELIVERED")
            self.assertEqual(detail["answers"][0]["answer_status"], "answered")
            self.assertEqual(detail["customer_questions"][0]["question_text"], "When will the team review this?")
            self.assertEqual(detail["transcript"][0]["speaker"], "customer")
            self.assertFalse(detail["needs_review"])


if __name__ == "__main__":
    unittest.main()
