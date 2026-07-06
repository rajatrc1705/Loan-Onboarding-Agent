import asyncio
import contextlib
import json
import logging
import os
from typing import Any, List

import httpx
from dotenv import load_dotenv
from livekit import agents, rtc
from livekit.agents import AgentServer, AgentSession, Agent, room_io, function_tool
from livekit.plugins import openai, noise_cancellation, bey
from openai.types.beta.realtime.session import TurnDetection

from api.llm_review import (
    build_fallback_review_packet,
    evaluate_answer,
    review_packet_to_text,
    summarize_call,
)

load_dotenv(".env.local")

API_URL = os.getenv("API_URL", "http://localhost:8000")
BEYOND_PRESENCE_API_KEY = os.getenv("BEYOND_PRESENCE_API_KEY")
BEY_AVATAR_ID = os.getenv("BEY_AVATAR_ID")
ANSWER_TIMEOUT_SECONDS = int(os.getenv("ANSWER_TIMEOUT_SECONDS", "45"))
CUSTOMER_QUESTION_TIMEOUT_SECONDS = int(
    os.getenv("CUSTOMER_QUESTION_TIMEOUT_SECONDS", "30")
)

logger = logging.getLogger("rfi-agent-worker")


def decide_answer_action(evaluation: dict[str, Any], follow_up_count: int) -> dict[str, Any]:
    status = evaluation.get("answer_status") or "unclear"
    follow_up_question = evaluation.get("follow_up_question") or ""
    if status == "answered":
        return {
            "is_final": True,
            "answer_status": "answered",
            "follow_up_question": "",
        }
    if follow_up_count < 1 and follow_up_question:
        return {
            "is_final": False,
            "answer_status": status,
            "follow_up_question": follow_up_question,
        }
    return {
        "is_final": True,
        "answer_status": status,
        "follow_up_question": "",
    }


async def fetch_rfi_detail(rfi_id: str) -> dict:
    """Fetch an RFI case from the API."""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{API_URL}/rfi/{rfi_id}")
        response.raise_for_status()
        return response.json()


async def post_answers(rfi_id: str, answers: List[dict]) -> None:
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{API_URL}/rfi/{rfi_id}/answers", json={"answers": answers}
        )
        response.raise_for_status()


async def post_customer_questions(rfi_id: str, questions: List[dict]) -> None:
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{API_URL}/rfi/{rfi_id}/customer-questions",
            json={"questions": questions},
        )
        response.raise_for_status()


async def post_transcript_turns(rfi_id: str, turns: List[dict]) -> None:
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{API_URL}/rfi/{rfi_id}/transcript",
            json={"turns": turns},
        )
        response.raise_for_status()


async def post_summary(
    rfi_id: str,
    summary_text: str,
    structured_json: dict,
    *,
    needs_review: bool,
    review_reason: str | None = None,
) -> None:
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{API_URL}/rfi/{rfi_id}/summary",
            json={
                "summary_text": summary_text,
                "structured_json": structured_json,
                "needs_review": needs_review,
                "review_reason": review_reason,
            },
        )
        response.raise_for_status()


async def mark_needs_review(rfi_id: str, reason: str) -> None:
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{API_URL}/rfi/{rfi_id}/needs-review",
            json={"reason": reason},
        )
        response.raise_for_status()


async def complete_call(
    rfi_id: str, *, needs_review: bool, review_reason: str | None = None
) -> None:
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{API_URL}/rfi/{rfi_id}/complete-call",
            json={"needs_review": needs_review, "review_reason": review_reason},
        )
        response.raise_for_status()


def create_assistant(
    questions: List[dict],
    record_answer_tool: callable,
    record_customer_question_tool: callable,
    finish_customer_questions_tool: callable,
) -> Agent:
    @function_tool
    async def get_questions() -> str:
        """Get the list of questions that the risk analyst wants to ask the customer."""
        if not questions:
            return "No questions have been configured for this session."
        formatted = "\n".join(
            f"{q['order_index'] + 1}. {q['question_text']}" for q in questions
        )
        return f"Questions to ask the customer:\n{formatted}"

    return Agent(
        instructions=(
            "You are an onboarding clarification agent. "
            "Lead with the exact greeting provided by the system prompt. Do not add any other words. "
            "Use the get_questions tool to retrieve the questions, and ONLY ask those questions. "
            "Do not invent additional risk questions beyond the tool-provided list. "
            "Ask each question one by one, waiting for the customer's answer before moving on. "
            "Only call record_answer after the customer has spoken. Never fabricate answers. "
            "After each answer, call record_answer with the captured response and follow the tool result. "
            "If the tool asks for a follow-up, ask only that follow-up and then call record_answer again. "
            "Never ask more than one follow-up for the same internal question. "
            "Customer questions are allowed, but only answer basic process questions. "
            "For approval, underwriting, legal, pricing, policy, or case-specific decision questions, "
            "say the internal team will follow up and call record_customer_question with needs_human_followup=true. "
            "At the end of the internal questions, ask whether the customer has questions for the team. "
            "If they ask a question, call record_customer_question. If they have no questions, call finish_customer_questions. "
            "If the customer is not able or willing to answer, politely ask them to come back when ready and end the call. "
            "IMPORTANT: If the user interrupts you while you are speaking, stop immediately and listen to what they have to say. "
            "Acknowledge their input naturally (e.g., 'Sure, go ahead' or 'Yes?') and respond to their question or comment before continuing. "
            "If they ask to skip a question, move to the next one. If they want to go back to a previous question, accommodate that request."
        ),
        tools=[
            get_questions,
            record_answer_tool,
            record_customer_question_tool,
            finish_customer_questions_tool,
        ],
    )


def _parse_metadata(ctx: agents.JobContext) -> dict:
    raw = ctx.job.metadata or "{}"
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        logger.warning("Invalid job metadata JSON: %s", raw)
        return {}


server = AgentServer()


@server.rtc_session(agent_name="rfi-agent")
async def my_agent(ctx: agents.JobContext):
    await ctx.connect()
    metadata = _parse_metadata(ctx)
    rfi_id = metadata.get("rfi_id")
    if not rfi_id:
        logger.warning("Missing rfi_id in job metadata.")
        ctx.shutdown("missing rfi_id")
        return

    persist_answers = metadata.get("persist_answers", True)
    generate_summary = metadata.get("generate_summary", True)
    end_call_on_complete = metadata.get("end_call_on_complete", True)

    room_closed = asyncio.Event()

    def _on_room_disconnected(_: rtc.DisconnectReason) -> None:
        room_closed.set()

    ctx.room.on("disconnected", _on_room_disconnected)

    session = AgentSession(
        llm=openai.realtime.RealtimeModel(
            voice="coral",
            turn_detection=TurnDetection(
                type="server_vad",
                threshold=0.6,  # Sensitivity: higher = requires louder audio
                prefix_padding_ms=300,  # Audio to include before detected speech
                silence_duration_ms=500,  # How long silence before turn ends
                create_response=True,  # Auto-create response after user stops
                interrupt_response=True,  # Allow user to interrupt agent mid-speech
            ),
        )
    )
    close_task: asyncio.Task | None = None

    detail = await fetch_rfi_detail(rfi_id)
    questions = detail.get("questions", []) if detail else []
    question_by_id = {str(question.get("id")): question for question in questions}
    recorded_answers: dict[str, dict[str, Any]] = {}
    customer_questions: list[dict[str, Any]] = []
    transcript_turns: list[dict[str, Any]] = []
    answer_events: dict[str, asyncio.Event] = {}
    follow_up_counts: dict[str, int] = {}
    evaluator_failed = asyncio.Event()
    customer_question_done = asyncio.Event()

    async def record_transcript_turn(speaker: str, text: str) -> None:
        cleaned = text.strip()
        if not cleaned:
            return
        turn = {"speaker": speaker, "text": cleaned}
        transcript_turns.append(turn)
        try:
            await post_transcript_turns(rfi_id, [turn])
        except Exception as exc:  # noqa: BLE001 - transcript should not break call
            logger.warning("Failed to persist transcript turn: %s", exc)

    async def persist_answer(
        question_id: str,
        answer_text: str,
        evaluation: dict[str, Any],
        *,
        follow_up_asked: bool,
    ) -> None:
        answer_payload = {
            "question_id": question_id,
            "answer_text": answer_text,
            "answer_status": evaluation.get("answer_status", "unclear"),
            "evidence_quote": evaluation.get("evidence_quote") or "",
            "follow_up_asked": follow_up_asked,
            "evaluator_notes": evaluation.get("evaluator_notes") or "",
            "captured_by": "agent",
        }
        recorded_answers[question_id] = answer_payload
        if persist_answers:
            await post_answers(rfi_id, [answer_payload])

    @function_tool
    async def record_answer(
        question_id: str, answer_text: str, evidence_quote: str = ""
    ) -> str:
        """Record a customer answer and run the separate completeness evaluator."""
        cleaned = answer_text.strip()
        if not cleaned or len(cleaned.split()) < 3:
            return "No answer captured yet. Ask the customer to respond."
        question = question_by_id.get(str(question_id))
        if not question:
            return "Unknown question id. Ask the current question again."
        question_text = str(question.get("question_text") or "")
        if cleaned.lower() == question_text.strip().lower():
            return "No answer captured yet. Ask the customer to respond."

        await record_transcript_turn("customer", cleaned)

        follow_up_count = follow_up_counts.get(str(question_id), 0)
        try:
            evaluation = await evaluate_answer(question_text, cleaned)
        except Exception as exc:  # noqa: BLE001 - evaluator failure is critical
            reason = f"Answer evaluator failed during call: {exc}"
            logger.warning(reason)
            evaluator_failed.set()
            evaluation = {
                "answer_status": "unclear",
                "evidence_quote": evidence_quote or cleaned,
                "evaluator_notes": reason,
                "follow_up_question": "",
            }
            await persist_answer(
                str(question_id),
                cleaned,
                evaluation,
                follow_up_asked=follow_up_count > 0,
            )
            with contextlib.suppress(Exception):
                await mark_needs_review(rfi_id, reason)
            answer_events.setdefault(str(question_id), asyncio.Event()).set()
            return (
                "The evaluator failed. Apologize and tell the customer the team "
                "will review the partial answers and follow up."
            )

        if evidence_quote and not evaluation.get("evidence_quote"):
            evaluation["evidence_quote"] = evidence_quote

        action = decide_answer_action(evaluation, follow_up_count)
        if action["is_final"] and action["answer_status"] == "answered":
            await persist_answer(
                str(question_id),
                cleaned,
                evaluation,
                follow_up_asked=follow_up_count > 0,
            )
            answer_events.setdefault(str(question_id), asyncio.Event()).set()
            return "Answer recorded as complete. Briefly confirm and continue."

        if not action["is_final"]:
            follow_up_counts[str(question_id)] = follow_up_count + 1
            await persist_answer(
                str(question_id),
                cleaned,
                evaluation,
                follow_up_asked=False,
            )
            follow_up_question = action["follow_up_question"]
            await record_transcript_turn("agent", follow_up_question)
            return (
                "The answer is incomplete. Ask exactly this one follow-up question "
                f"and no other follow-up: {follow_up_question}"
            )

        evaluation["answer_status"] = action["answer_status"] or "unclear"
        await persist_answer(
            str(question_id),
            cleaned,
            evaluation,
            follow_up_asked=follow_up_count > 0,
        )
        answer_events.setdefault(str(question_id), asyncio.Event()).set()
        return (
            "No more follow-ups are allowed for this question. Mark it unclear, "
            "briefly acknowledge, and continue."
        )

    @function_tool
    async def record_customer_question(
        question_text: str,
        agent_response: str = "",
        needs_human_followup: bool = True,
    ) -> str:
        """Record a question asked by the customer during the call."""
        cleaned = question_text.strip()
        if not cleaned:
            return "No customer question captured yet."
        row = {
            "question_text": cleaned,
            "agent_response": agent_response.strip() or None,
            "needs_human_followup": needs_human_followup,
        }
        customer_questions.append(row)
        await record_transcript_turn("customer", cleaned)
        if agent_response.strip():
            await record_transcript_turn("agent", agent_response.strip())
        try:
            await post_customer_questions(rfi_id, [row])
        except Exception as exc:  # noqa: BLE001 - keep the call moving if possible
            logger.warning("Failed to persist customer question: %s", exc)
        return (
            "Customer question recorded. If it needs human follow-up, tell the "
            "customer the team will follow up, then ask whether they have any "
            "other questions. If they have no more questions, call finish_customer_questions."
        )

    @function_tool
    async def finish_customer_questions() -> str:
        """Record that the customer has no questions for the team."""
        customer_question_done.set()
        return "No customer questions recorded. Thank the customer and finish the call."

    async def _close_on_room_disconnect() -> None:
        await room_closed.wait()
        await session.aclose()

    reply_lock = asyncio.Lock()

    async def _safe_generate_reply(
        instructions: str, step: str, transcript_text: str | None = None
    ) -> bool:
        if room_closed.is_set():
            return False
        async with reply_lock:
            try:
                await session.generate_reply(instructions=instructions)
                if transcript_text:
                    await record_transcript_turn("agent", transcript_text)
                return True
            except Exception as exc:  # noqa: BLE001 - handle realtime timeouts
                logger.warning("generate_reply failed at %s: %s", step, exc)
                return False

    async def _wait_for_answer(question_id: str) -> bool:
        event = answer_events.setdefault(question_id, asyncio.Event())
        try:
            done, pending = await asyncio.wait(
                [
                    asyncio.create_task(event.wait()),
                    asyncio.create_task(evaluator_failed.wait()),
                ],
                timeout=ANSWER_TIMEOUT_SECONDS,
                return_when=asyncio.FIRST_COMPLETED,
            )
            for task in pending:
                task.cancel()
            return bool(done and event.is_set() and not evaluator_failed.is_set())
        except asyncio.TimeoutError:
            return False

    close_task = asyncio.create_task(_close_on_room_disconnect())

    try:
        if BEYOND_PRESENCE_API_KEY:
            os.environ.setdefault("BEY_API_KEY", BEYOND_PRESENCE_API_KEY)
            try:
                avatar = bey.AvatarSession(avatar_id=BEY_AVATAR_ID)
                await avatar.start(session, room=ctx.room)
            except Exception as exc:  # noqa: BLE001 - avoid failing the call
                logger.warning("Beyond Presence avatar start failed: %s", exc)

        await session.start(
            room=ctx.room,
            agent=create_assistant(
                questions,
                record_answer,
                record_customer_question,
                finish_customer_questions,
            ),
            room_options=room_io.RoomOptions(
                audio_input=room_io.AudioInputOptions(
                    noise_cancellation=lambda params: noise_cancellation.BVCTelephony()
                    if params.participant.kind == rtc.ParticipantKind.PARTICIPANT_KIND_SIP
                    else noise_cancellation.BVC(),
                ),
            ),
        )

        if room_closed.is_set():
            return

        greeted = await _safe_generate_reply(
            instructions=(
                "Say: "
                "\"Hello! I'm the onboarding agent. The Risk Team has a few questions to clarify "
                "about your application. I'll ask them one at a time and confirm your answers as we go.\""
            ),
            step="greeting",
            transcript_text=(
                "Hello! I'm the onboarding agent. The Risk Team has a few questions "
                "to clarify about your application. I'll ask them one at a time and "
                "confirm your answers as we go."
            ),
        )
        if not greeted:
            return

        for question in questions:
            if room_closed.is_set():
                return
            question_id = question.get("id")
            question_text = question.get("question_text")
            if not question_id or not question_text:
                continue
            ok = await _safe_generate_reply(
                instructions=(
                    "Ask ONLY the following question, with no preface or filler, then wait for their response. "
                    "Once they answer, call the record_answer tool with question_id "
                    f"'{question_id}' and answer_text set to the customer's response. "
                    "If the tool returns a follow-up question, ask only that follow-up. "
                    "If the tool says the answer is complete or unclear after the allowed follow-up, briefly acknowledge and continue. "
                    f"Question: {question_text}"
                ),
                step=f"question:{question_id}",
                transcript_text=question_text,
            )
            if not ok:
                break
            answered = await _wait_for_answer(question_id)
            if evaluator_failed.is_set():
                if room_closed.is_set():
                    return
                await _safe_generate_reply(
                    instructions=(
                        "Say: \"I'm sorry, we need to pause here. The team will review "
                        "what we captured and follow up with you.\""
                    ),
                    step=f"evaluator-failed:{question_id}",
                    transcript_text=(
                        "I'm sorry, we need to pause here. The team will review what "
                        "we captured and follow up with you."
                    ),
                )
                ctx.shutdown("evaluator failed")
                return
            if not answered:
                if room_closed.is_set():
                    return
                reason = f"Customer did not answer question {question_id} before timeout."
                with contextlib.suppress(Exception):
                    await post_answers(
                        rfi_id,
                        [
                            {
                                "question_id": str(question_id),
                                "answer_text": "",
                                "answer_status": "not_answered",
                                "follow_up_asked": False,
                                "evaluator_notes": reason,
                                "captured_by": "agent",
                            }
                        ],
                    )
                    await mark_needs_review(rfi_id, reason)
                await _safe_generate_reply(
                    instructions=(
                        "No worries. Please come back when you're ready to answer the questions. "
                        "We can continue then."
                    ),
                    step=f"no-answer:{question_id}",
                    transcript_text=(
                        "No worries. Please come back when you're ready to answer the questions. "
                        "We can continue then."
                    ),
                )
                ctx.shutdown("no answer")
                return

        if questions and not room_closed.is_set():
            customer_question_done.clear()
            asked_for_questions = await _safe_generate_reply(
                instructions=(
                    "Ask exactly: \"Do you have any questions for our team?\" "
                    "If the customer asks a question, call record_customer_question. "
                    "If they say no or they have nothing else, call finish_customer_questions."
                ),
                step="customer-questions",
                transcript_text="Do you have any questions for our team?",
            )
            if asked_for_questions:
                with contextlib.suppress(asyncio.TimeoutError):
                    await asyncio.wait_for(
                        customer_question_done.wait(),
                        timeout=CUSTOMER_QUESTION_TIMEOUT_SECONDS,
                    )

            await _safe_generate_reply(
                instructions=(
                    "Thank the customer for their time and say their responses will be "
                    "forwarded to the team for review."
                ),
                step="thank-you",
                transcript_text=(
                    "Thank you for your time. Your responses will be forwarded to the "
                    "team for review."
                ),
            )

        if generate_summary and not room_closed.is_set():
            review_reason = None
            needs_review = any(
                answer.get("answer_status") != "answered"
                for answer in recorded_answers.values()
            ) or any(
                question.get("needs_human_followup") for question in customer_questions
            )
            try:
                packet = await summarize_call(
                    questions=questions,
                    answers=list(recorded_answers.values()),
                    customer_questions=customer_questions,
                    transcript=transcript_turns,
                )
            except Exception as exc:  # noqa: BLE001 - persist raw review data
                logger.warning("Summary LLM failed: %s", exc)
                packet = build_fallback_review_packet(
                    questions, recorded_answers, customer_questions
                )
                packet.setdefault("summary_warnings", []).append(
                    "Summary LLM failed; review raw captured answers."
                )
                needs_review = True
                review_reason = f"Summary LLM failed: {exc}"
            summary_text = review_packet_to_text(packet)
            await post_summary(
                rfi_id,
                summary_text,
                packet,
                needs_review=needs_review,
                review_reason=review_reason,
            )
        else:
            await complete_call(rfi_id, needs_review=False)

        if end_call_on_complete:
            if ctx.room.isconnected():
                await ctx.room.disconnect()
            ctx.shutdown("complete")
            return

        await asyncio.sleep(600)
        ctx.shutdown("timeout")
    finally:
        if close_task is not None:
            close_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await close_task
        await session.aclose()


if __name__ == "__main__":
    agents.cli.run_app(server)
