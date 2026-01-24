from fastapi import APIRouter, Body, HTTPException

from ..models import LivekitTokenRequest, LivekitTokenResponse
from ..settings import LIVEKIT_API_KEY, LIVEKIT_API_SECRET, LIVEKIT_URL

router = APIRouter()


@router.post("/token")
def mint_token(payload: LivekitTokenRequest = Body(...)) -> LivekitTokenResponse:
    if not LIVEKIT_URL or not LIVEKIT_API_KEY or not LIVEKIT_API_SECRET:
        raise HTTPException(status_code=503, detail="LiveKit is not configured")

    try:
        from livekit.api import AccessToken, VideoGrants
    except ImportError as exc:
        raise HTTPException(status_code=500, detail="LiveKit SDK not available") from exc

    grants = VideoGrants(
        room_join=True,
        room=payload.room_name,
        can_publish=payload.can_publish,
        can_subscribe=payload.can_subscribe,
    )
    token = (
        AccessToken(LIVEKIT_API_KEY, LIVEKIT_API_SECRET)
        .with_identity(payload.identity)
        .with_name(payload.name or "")
        .with_metadata(payload.metadata or "")
        .with_grants(grants)
    )
    return LivekitTokenResponse(livekit_url=LIVEKIT_URL, token=token.to_jwt())
