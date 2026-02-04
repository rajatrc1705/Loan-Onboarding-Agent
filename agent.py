import asyncio
import contextlib
import json
import logging
import os
from typing import List

import httpx
from dotenv import load_dotenv
from livekit import agents, rtc
from livekit.agents import AgentServer, AgentSession, Agent, room_io, function_tool
from livekit.plugins import openai, noise_cancellation, bey
from openai.types.beta.realtime.session import TurnDetection

load_dotenv(".env.local")

API_URL = os.getenv("API_URL", "http://localhost:8000")
BEYOND_PRESENCE_API_KEY = os.getenv("BEYOND_PRESENCE_API_KEY")
BEY_AVATAR_ID = os.getenv("BEY_AVATAR_ID")
ANSWER_TIMEOUT_SECONDS = int(os.getenv("ANSWER_TIMEOUT_SECONDS", "45"))

logger = logging.getLogger("rfi-agent-worker")


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
            "You are an onboarding clarification agent. "
            "Lead with the exact greeting provided by the system prompt. Do not add any other words. "
            "Use the get_questions tool to retrieve the questions, and ONLY ask those questions. "
            "Do not ask any additional questions beyond the tool-provided list. "
            "Ask each question one by one, waiting for the customer's answer before moving on. "
            "Only call record_answer after the customer has spoken. Never fabricate answers. "
            "After each answer, call record_answer with the captured response and confirm it briefly. "
            "If the customer is not able or willing to answer, politely ask them to come back when ready and end the call. "
            "IMPORTANT: If the user interrupts you while you are speaking, stop immediately and listen to what they have to say. "
            "Acknowledge their input naturally (e.g., 'Sure, go ahead' or 'Yes?') and respond to their question or comment before continuing. "
            "If they ask to skip a question, move to the next one. If they want to go back to a previous question, accommodate that request."
        ),
        tools=[get_questions, record_answer_tool],
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
                threshold=0.5,  # Sensitivity: higher = requires louder audio
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
    recorded_answers: dict[str, str] = {}
    answer_events: dict[str, asyncio.Event] = {}
    current_question_text: str | None = None

    @function_tool
    async def record_answer(question_id: str, answer_text: str) -> str:
        cleaned = answer_text.strip()
        if not cleaned or len(cleaned.split()) < 3:
            return "No answer captured yet. Ask the customer to respond."
        if current_question_text and cleaned.lower() == current_question_text.strip().lower():
            return "No answer captured yet. Ask the customer to respond."
        recorded_answers[question_id] = cleaned
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

    reply_lock = asyncio.Lock()

    async def _safe_generate_reply(instructions: str, step: str) -> bool:
        if room_closed.is_set():
            return False
        async with reply_lock:
            try:
                await session.generate_reply(instructions=instructions)
                return True
            except Exception as exc:  # noqa: BLE001 - handle realtime timeouts
                logger.warning("generate_reply failed at %s: %s", step, exc)
                return False

    async def _wait_for_answer(question_id: str) -> bool:
        event = answer_events.setdefault(question_id, asyncio.Event())
        try:
            await asyncio.wait_for(event.wait(), timeout=ANSWER_TIMEOUT_SECONDS)
            return True
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
                "Say exactly this greeting and nothing else: "
                "\"Hello! I'm the onboarding agent. The Risk Team has a few questions to clarify "
                "about your application. I'll ask them one at a time and confirm your answers as we go.\""
            ),
            step="greeting",
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
            current_question_text = question_text
            ok = await _safe_generate_reply(
                instructions=(
                    "Ask ONLY the following question, with no preface or filler, then wait for their response. "
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
                ctx.shutdown("no answer")
                return

        if questions and not room_closed.is_set():
            await _safe_generate_reply(
                instructions=(
                    "Thank you for your patience. Your answers will be forwarded to the Risk Team."
                ),
                step="thank-you",
            )

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
    