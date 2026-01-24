import asyncio
import contextlib
import logging
import os
from typing import Dict, List

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from livekit import rtc
from livekit.agents import Agent, AgentSession, room_io, function_tool
from livekit.plugins import openai, noise_cancellation
from livekit.plugins import bey

load_dotenv(".env.local")

LIVEKIT_URL = os.getenv("LIVEKIT_URL")
LIVEKIT_API_KEY = os.getenv("LIVEKIT_API_KEY")
LIVEKIT_API_SECRET = os.getenv("LIVEKIT_API_SECRET")
BEYOND_PRESENCE_API_KEY = os.getenv("BEYOND_PRESENCE_API_KEY")
API_URL = os.getenv("API_URL", "http://localhost:8000")
ANSWER_TIMEOUT_SECONDS = int(os.getenv("ANSWER_TIMEOUT_SECONDS", "45"))
BEY_AVATAR_ID = os.getenv("BEY_AVATAR_ID")

app = FastAPI(title="RFI LiveKit Agent")
active_jobs: Dict[str, asyncio.Task] = {}
logger = logging.getLogger("rfi-agent")


class JoinRequest(BaseModel):
    rfi_id: str
    room_name: str
    persist_answers: bool = True
    generate_summary: bool = True
    end_call_on_complete: bool = True


async def fetch_rfi_detail(rfi_id: str) -> dict:
    """Fetch an RFI case from the API."""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{API_URL}/rfi/{rfi_id}")
        response.raise_for_status()
        return response.json()


async def post_answers(rfi_id: str, answers: List[dict]) -> None:
    async with httpx.AsyncClient() as client:
        await client.post(f"{API_URL}/rfi/{rfi_id}/answers", json={"answers": answers})


async def post_summary(rfi_id: str, summary_text: str, structured_json: dict) -> None:
    async with httpx.AsyncClient() as client:
        await client.post(
            f"{API_URL}/rfi/{rfi_id}/summary",
            json={"summary_text": summary_text, "structured_json": structured_json},
        )


def create_assistant(questions: List[dict], record_answer_tool: callable) -> Agent:
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
            "You ALWAYS SPEAK IN ENGLISH! You are an onboarding clarification agent. "
            "Greet the user and explain that the Risk Team has some questions for them."
            "Use the get_questions tool to retrieve the questions, then ask each question one by one. "
            "After each answer, call record_answer with the captured response and confirm it briefly. "
            "Wait for the customer to answer each question before moving to the next. "
            "If the customer is not able to or wanting to answer them, ask the customer nicely to come back when ready, and prepare to end the call."
        ),
        tools=[get_questions, record_answer_tool],
    )

def _mint_token(identity: str, room_name: str) -> str:
    if not LIVEKIT_URL or not LIVEKIT_API_KEY or not LIVEKIT_API_SECRET:
        raise RuntimeError("LiveKit is not configured")

    try:
        from livekit.api import AccessToken, VideoGrants
    except ImportError as exc:
        raise RuntimeError("LiveKit SDK not available") from exc

    grants = VideoGrants(room_join=True, room=room_name, can_publish=True, can_subscribe=True)
    token = (
        AccessToken(LIVEKIT_API_KEY, LIVEKIT_API_SECRET)
        .with_identity(identity)
        .with_name("RFI Agent")
        .with_grants(grants)
    )
    return token.to_jwt()


async def _run_agent(
    room_name: str,
    identity: str,
    rfi_id: str,
    persist_answers: bool,
    generate_summary: bool,
    end_call_on_complete: bool,
) -> None:
    token = _mint_token(identity, room_name)
    room = rtc.Room()
    room_closed = asyncio.Event()

    def _on_room_disconnected(_: rtc.DisconnectReason) -> None:
        if not room_closed.is_set():
            room_closed.set()

    room.on("disconnected", _on_room_disconnected)
    try:
        await room.connect(LIVEKIT_URL, token)
    except Exception as exc:  # noqa: BLE001 - surface connection errors cleanly
        logger.warning("LiveKit connect failed for %s: %s", room_name, exc)
        room_closed.set()
        return

    # Placeholder: Beyond Presence avatar track can be attached here later.
    # For example, initialize avatar SDK using BEYOND_PRESENCE_API_KEY and
    # publish a video track into the room once available.

    session = AgentSession(llm=openai.realtime.RealtimeModel(voice="coral"))
    close_task: asyncio.Task | None = None

    detail = await fetch_rfi_detail(rfi_id)
    questions = detail.get("questions", []) if detail else []
    recorded_answers: dict[str, str] = {}
    answer_events: dict[str, asyncio.Event] = {}

    @function_tool
    async def record_answer(question_id: str, answer_text: str) -> str:
        recorded_answers[question_id] = answer_text
        answer_events.setdefault(question_id, asyncio.Event()).set()
        if persist_answers:
            await post_answers(
                rfi_id,
                [
                    {
                        "question_id": question_id,
                        "answer_text": answer_text,
                        "captured_by": "agent",
                    }
                ],
            )
        return "Answer recorded."

    async def _close_on_room_disconnect() -> None:
        await room_closed.wait()
        await session.aclose()

    async def _safe_generate_reply(instructions: str, step: str) -> bool:
        if room_closed.is_set():
            return False
        try:
            await session.generate_reply(instructions=instructions)
            return True
        except Exception as exc:  # noqa: BLE001 - handle realtime timeouts
            logger.warning("generate_reply failed at %s: %s", step, exc)
            return False

    close_task = asyncio.create_task(_close_on_room_disconnect())

    try:
        avatar: bey.AvatarSession | None = None
        if BEYOND_PRESENCE_API_KEY:
            os.environ.setdefault("BEY_API_KEY", BEYOND_PRESENCE_API_KEY)
            try:
                avatar = bey.AvatarSession(avatar_id=BEY_AVATAR_ID)
                await avatar.start(session, room=room)
            except Exception as exc:  # noqa: BLE001 - avoid failing the call
                logger.warning("Beyond Presence avatar start failed: %s", exc)

        await session.start(
            room=room,
            agent=create_assistant(questions, record_answer),
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
                "Hello! I'm the onboarding agent. The risk team has some questions to clarify "
                "about your application. I will ask them and I will confirm your answers as we go."
            ),
            step="greeting",
        )
        if not greeted:
            return

        async def _wait_for_answer(question_id: str) -> bool:
            event = answer_events.setdefault(question_id, asyncio.Event())
            try:
                await asyncio.wait_for(event.wait(), timeout=ANSWER_TIMEOUT_SECONDS)
                return True
            except asyncio.TimeoutError:
                return False

        for question in questions:
            if room_closed.is_set():
                return
            question_id = question.get("id")
            question_text = question.get("question_text")
            if not question_id or not question_text:
                continue
            ok = await _safe_generate_reply(
                instructions=(
                    "Ask the customer the following question, then wait for their response. "
                    "Once they answer, call the record_answer tool with question_id "
                    f"'{question_id}' and answer_text set to the customer's response. "
                    "After calling the tool, briefly confirm what you heard. "
                    f"Question: {question_text}"
                ),
                step=f"question:{question_id}",
            )
            if not ok:
                break
            answered = await _wait_for_answer(question_id)
            if not answered:
                if room_closed.is_set():
                    return
                await _safe_generate_reply(
                    instructions=(
                        "No worries. Please come back when you're ready to answer the questions. "
                        "We can continue then."
                    ),
                    step=f"no-answer:{question_id}",
                )
                if room.isconnected():
                    await room.disconnect()
                return

        if generate_summary and not room_closed.is_set():
            summary_lines = []
            structured_answers: dict[str, str] = {}
            for question in questions:
                question_id = question.get("id")
                question_text = question.get("question_text")
                if not question_id or not question_text:
                    continue
                answer = recorded_answers.get(question_id, "")
                if answer:
                    summary_lines.append(f"- {question_text}: {answer}")
                    structured_answers[question_id] = answer
                else:
                    summary_lines.append(f"- {question_text}: (no answer captured)")
            summary_text = "Summary\n" + "\n".join(summary_lines)
            await post_summary(rfi_id, summary_text, {"answers": structured_answers})

        if end_call_on_complete and room.isconnected():
            await room.disconnect()
            return

        await asyncio.sleep(600)
        if room.isconnected():
            await room.disconnect()
    finally:
        if close_task is not None:
            close_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await close_task
        await session.aclose()


@app.get("/health")
def health_check() -> dict:
    return {"status": "ok"}


@app.post("/agent/join")
async def join_room(payload: JoinRequest) -> dict:
    if not LIVEKIT_URL or not LIVEKIT_API_KEY or not LIVEKIT_API_SECRET:
        raise HTTPException(status_code=503, detail="LiveKit is not configured")

    identity = f"rfi-agent-{payload.rfi_id}"
    task = active_jobs.get(identity)
    if task and not task.done():
        return {"status": "already_running"}

    active_jobs[identity] = asyncio.create_task(
        _run_agent(
            payload.room_name,
            identity,
            payload.rfi_id,
            payload.persist_answers,
            payload.generate_summary,
            payload.end_call_on_complete,
        )
    )
    return {"status": "joining"}
