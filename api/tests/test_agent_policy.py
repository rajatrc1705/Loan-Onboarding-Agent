import os
import tempfile
import unittest

db_file = tempfile.NamedTemporaryFile(delete=False)
db_file.close()
os.environ.setdefault("DATABASE_URL", f"sqlite:///{db_file.name}")
os.environ.setdefault("AUTO_CREATE_TABLES", "true")

from agent import decide_answer_action


class AgentPolicyTest(unittest.TestCase):
    def test_complete_answer_finishes_question(self) -> None:
        action = decide_answer_action(
            {"answer_status": "answered", "follow_up_question": ""},
            follow_up_count=0,
        )

        self.assertTrue(action["is_final"])
        self.assertEqual(action["answer_status"], "answered")

    def test_incomplete_answer_gets_one_follow_up(self) -> None:
        action = decide_answer_action(
            {
                "answer_status": "unclear",
                "follow_up_question": "Can you give the exact month?",
            },
            follow_up_count=0,
        )

        self.assertFalse(action["is_final"])
        self.assertEqual(action["follow_up_question"], "Can you give the exact month?")

    def test_second_incomplete_answer_finishes_as_unclear(self) -> None:
        action = decide_answer_action(
            {
                "answer_status": "unclear",
                "follow_up_question": "Can you give the exact month?",
            },
            follow_up_count=1,
        )

        self.assertTrue(action["is_final"])
        self.assertEqual(action["answer_status"], "unclear")
        self.assertEqual(action["follow_up_question"], "")


if __name__ == "__main__":
    unittest.main()
