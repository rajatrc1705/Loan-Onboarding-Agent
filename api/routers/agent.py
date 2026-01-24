import json

from fastapi import APIRouter, Body, HTTPException
from livekit import api

from ..models import AgentJoinRequest

router = APIRouter()


@router.post("/join")
async def request_agent_join(payload: AgentJoinRequest = Body(...)) -> dict:
    metadata = json.dumps(
        {
            "rfi_id": str(payload.rfi_id),
            "persist_answers": payload.persist_answers,
            "generate_summary": payload.generate_summary,
            "end_call_on_complete": payload.end_call_on_complete,
        }
    )

    lkapi = api.LiveKitAPI()
    try:
        await lkapi.agent_dispatch.create_dispatch(
            api.CreateAgentDispatchRequest(
                agent_name="rfi-agent",
                room=payload.room_name,
                metadata=metadata,
            )
        )
    except Exception as exc:  # noqa: BLE001 - surface dispatch errors cleanly
        raise HTTPException(status_code=502, detail="Agent dispatch failed") from exc
    finally:
        await lkapi.aclose()

    return {"status": "queued"}
