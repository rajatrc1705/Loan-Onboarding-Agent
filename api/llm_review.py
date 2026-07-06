from __future__ import annotations

import json
from typing import Any, Iterable

from openai import AsyncOpenAI

from .settings import (
    LLM_REQUEST_TIMEOUT_SECONDS,
    OPENAI_EVALUATOR_MODEL,
    OPENAI_SUMMARY_MODEL,
)


ANSWER_STATUSES = {"answered", "unclear", "not_answered"}


def _extract_json_object(content: str) -> dict[str, Any]:
    try:
        value = json.loads(content)
    except json.JSONDecodeError:
        start = content.find("{")
        end = content.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise
        value = json.loads(content[start : end + 1])
    if not isinstance(value, dict):
        raise ValueError("Expected a JSON object")
    return value


def normalize_evaluation(raw: dict[str, Any]) -> dict[str, Any]:
    status = str(raw.get("answer_status", "unclear")).strip().lower()
    if status not in ANSWER_STATUSES:
        status = "unclear"
    return {
        "answer_status": status,
        "evidence_quote": str(raw.get("evidence_quote") or "").strip(),
        "evaluator_notes": str(raw.get("evaluator_notes") or "").strip(),
        "follow_up_question": str(raw.get("follow_up_question") or "").strip(),
    }


async def evaluate_answer(
    question_text: str,
    answer_text: str,
    *,
    model: str | None = None,
) -> dict[str, Any]:
    client = AsyncOpenAI(timeout=LLM_REQUEST_TIMEOUT_SECONDS)
    response = await client.chat.completions.create(
        model=model or OPENAI_EVALUATOR_MODEL,
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
                "content": (
                    "You evaluate whether a customer's spoken answer satisfies "
                    "one internal risk clarification question. Infer completeness "
                    "from the question text. Return only JSON with keys: "
                    "answer_status, evidence_quote, evaluator_notes, "
                    "follow_up_question. answer_status must be answered, unclear, "
                    "or not_answered. If incomplete, write one concise follow-up "
                    "question. If complete, follow_up_question must be empty."
                ),
            },
            {
                "role": "user",
                "content": json.dumps(
                    {
                        "question_text": question_text,
                        "customer_answer": answer_text,
                    }
                ),
            },
        ],
    )
    content = response.choices[0].message.content or "{}"
    return normalize_evaluation(_extract_json_object(content))


def build_fallback_review_packet(
    questions: Iterable[dict[str, Any]],
    answers_by_question_id: dict[str, dict[str, Any]],
    customer_questions: Iterable[dict[str, Any]],
) -> dict[str, Any]:
    answer_rows = []
    follow_up_needed = []
    for question in questions:
        question_id = str(question.get("id") or "")
        answer = answers_by_question_id.get(question_id, {})
        status = answer.get("answer_status") or "not_answered"
        row = {
            "question_id": question_id,
            "question_text": question.get("question_text") or "",
            "answer_text": answer.get("answer_text") or "",
            "answer_status": status,
            "evidence_quote": answer.get("evidence_quote") or "",
            "follow_up_asked": bool(answer.get("follow_up_asked")),
            "evaluator_notes": answer.get("evaluator_notes") or "",
        }
        answer_rows.append(row)
        if status != "answered":
            follow_up_needed.append(row)
    customer_question_rows = list(customer_questions)
    return {
        "short_summary": "Review the captured answers and customer questions.",
        "answers": answer_rows,
        "customer_questions": customer_question_rows,
        "follow_up_needed": follow_up_needed,
        "summary_warnings": [],
    }


async def summarize_call(
    *,
    questions: list[dict[str, Any]],
    answers: list[dict[str, Any]],
    customer_questions: list[dict[str, Any]],
    transcript: list[dict[str, Any]],
    model: str | None = None,
) -> dict[str, Any]:
    answers_by_question_id: dict[str, dict[str, Any]] = {}
    for answer in answers:
        answers_by_question_id[str(answer.get("question_id"))] = answer

    fallback = build_fallback_review_packet(
        questions, answers_by_question_id, customer_questions
    )
    client = AsyncOpenAI(timeout=LLM_REQUEST_TIMEOUT_SECONDS)
    response = await client.chat.completions.create(
        model=model or OPENAI_SUMMARY_MODEL,
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
                "content": (
                    "Create an internal review packet for a risk team from an RFI "
                    "voice call. Do not decide approval or underwriting outcomes. "
                    "Return only JSON with keys: short_summary, answers, "
                    "customer_questions, follow_up_needed, summary_warnings. "
                    "Preserve answer_status values and flag unclear or unanswered "
                    "items in follow_up_needed."
                ),
            },
            {
                "role": "user",
                "content": json.dumps(
                    {
                        "questions": questions,
                        "answers": answers,
                        "customer_questions": customer_questions,
                        "transcript": transcript,
                        "fallback_shape": fallback,
                    }
                ),
            },
        ],
    )
    content = response.choices[0].message.content or "{}"
    packet = _extract_json_object(content)
    for key, value in fallback.items():
        packet.setdefault(key, value)
    return packet


def review_packet_to_text(packet: dict[str, Any]) -> str:
    lines = [str(packet.get("short_summary") or "Review packet")]
    answers = packet.get("answers") or []
    if answers:
        lines.append("")
        lines.append("Answers")
        for item in answers:
            question = item.get("question_text") or item.get("question_id") or "Question"
            status = item.get("answer_status") or "unknown"
            answer = item.get("answer_text") or "No answer captured."
            lines.append(f"- {question} [{status}]: {answer}")
    customer_questions = packet.get("customer_questions") or []
    if customer_questions:
        lines.append("")
        lines.append("Customer questions")
        for item in customer_questions:
            question = item.get("question_text") or ""
            follow_up = "needs follow-up" if item.get("needs_human_followup") else "answered"
            lines.append(f"- {question} [{follow_up}]")
    follow_up_needed = packet.get("follow_up_needed") or []
    if follow_up_needed:
        lines.append("")
        lines.append("Follow-up needed")
        for item in follow_up_needed:
            lines.append(f"- {item.get('question_text') or item.get('question_id')}")
    return "\n".join(lines)
