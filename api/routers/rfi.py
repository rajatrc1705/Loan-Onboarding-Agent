from datetime import datetime, timedelta
from typing import List, Optional
from uuid import UUID, uuid4

import httpx
from fastapi import APIRouter, Body, Depends, HTTPException
from sqlmodel import Session, delete, select

from ..db import get_session
from ..models import (
    AnswerCapturedBy,
    RfiAnswer,
    RfiAnswerRead,
    RfiAnswersUpsert,
    RfiCase,
    RfiCaseCreate,
    RfiCaseRead,
    RfiDetail,
    RfiQuestion,
    RfiQuestionRead,
    RfiQuestionsUpdate,
    RfiStatus,
    RfiSummary,
    RfiSummaryInput,
    RfiSummaryRead,
    StartCallRequest,
)
from ..settings import (
    AGENT_SERVICE_URL,
    EMAIL_FROM,
    MAGIC_LINK_BASE_URL,
    RESEND_API_KEY,
)

router = APIRouter()


@router.post("")
def create_rfi_case(
    payload: RfiCaseCreate = Body(...),
    session: Session = Depends(get_session),
) -> RfiCaseRead:
    case = RfiCase(
        customer_email=payload.customer_email,
        application_id=payload.application_id,
        status=RfiStatus.DRAFT,
    )
    session.add(case)
    session.commit()
    session.refresh(case)
    return RfiCaseRead.model_validate(case)


@router.put("/{rfi_id}/questions")
def replace_questions(
    rfi_id: str,
    payload: RfiQuestionsUpdate = Body(...),
    session: Session = Depends(get_session),
) -> List[RfiQuestionRead]:
    case = _get_case_or_404(session, rfi_id)
    session.exec(delete(RfiQuestion).where(RfiQuestion.rfi_id == case.id))
    for item in payload.questions:
        session.add(
            RfiQuestion(
                rfi_id=case.id,
                order_index=item.order_index,
                question_text=item.question_text,
            )
        )
    case.updated_at = datetime.utcnow()
    session.add(case)
    session.commit()
    return _list_questions(session, case.id)


@router.post("/{rfi_id}/send-invite")
def send_invite(
    rfi_id: str, session: Session = Depends(get_session)
) -> RfiCaseRead:
    case = _get_case_or_404(session, rfi_id)
    case.magic_token = uuid4().hex
    case.room_name = case.room_name or f"rfi-{case.id}"
    case.expires_at = datetime.utcnow() + timedelta(days=7)
    case.status = RfiStatus.INVITED
    case.updated_at = datetime.utcnow()
    session.add(case)
    session.commit()
    session.refresh(case)
    _maybe_send_magic_link(case)
    return RfiCaseRead.model_validate(case)


@router.get("")
def list_rfi_cases(
    status: Optional[RfiStatus] = None,
    customer_email: Optional[str] = None,
    session: Session = Depends(get_session),
) -> List[RfiCaseRead]:
    statement = select(RfiCase)
    if status:
        statement = statement.where(RfiCase.status == status)
    if customer_email:
        statement = statement.where(RfiCase.customer_email == customer_email)
    statement = statement.order_by(RfiCase.created_at.desc())
    cases = session.exec(statement).all()
    return [RfiCaseRead.model_validate(case) for case in cases]


@router.get("/{rfi_id}")
def get_rfi_case(
    rfi_id: str, session: Session = Depends(get_session)
) -> RfiDetail:
    case = _get_case_or_404(session, rfi_id)
    questions = _list_questions(session, case.id)
    answers = _list_answers(session, case.id)
    summary = _get_summary(session, case.id)
    return RfiDetail(
        id=case.id,
        customer_email=case.customer_email,
        application_id=case.application_id,
        status=case.status,
        room_name=case.room_name,
        magic_token=case.magic_token,
        expires_at=case.expires_at,
        created_at=case.created_at,
        updated_at=case.updated_at,
        questions=questions,
        answers=answers,
        summary=summary,
    )


@router.post("/{rfi_id}/start-call")
def start_call(
    rfi_id: str,
    payload: StartCallRequest | None = Body(None),
    session: Session = Depends(get_session),
) -> RfiCaseRead:
    case = _get_case_or_404(session, rfi_id)
    case.status = RfiStatus.IN_CALL
    case.updated_at = datetime.utcnow()
    session.add(case)
    session.commit()
    session.refresh(case)

    if AGENT_SERVICE_URL and case.room_name:
        options = payload or StartCallRequest()
        try:
            httpx.post(
                f"{AGENT_SERVICE_URL.rstrip('/')}/agent/join",
                json={
                    "rfi_id": str(case.id),
                    "room_name": case.room_name,
                    "persist_answers": options.persist_answers,
                    "generate_summary": options.generate_summary,
                    "end_call_on_complete": options.end_call_on_complete,
                },
                timeout=5.0,
            )
        except httpx.HTTPError:
            pass

    return RfiCaseRead.model_validate(case)


@router.post("/{rfi_id}/answers")
def post_answers(
    rfi_id: str,
    payload: RfiAnswersUpsert = Body(...),
    session: Session = Depends(get_session),
) -> List[RfiAnswerRead]:
    case = _get_case_or_404(session, rfi_id)
    for answer in payload.answers:
        session.add(
            RfiAnswer(
                rfi_id=case.id,
                question_id=answer.question_id,
                answer_text=answer.answer_text,
                captured_by=answer.captured_by or AnswerCapturedBy.AGENT,
            )
        )
    case.updated_at = datetime.utcnow()
    session.add(case)
    session.commit()
    return _list_answers(session, case.id)


@router.post("/{rfi_id}/summary")
def post_summary(
    rfi_id: str,
    payload: RfiSummaryInput = Body(...),
    session: Session = Depends(get_session),
) -> RfiSummaryRead:
    case = _get_case_or_404(session, rfi_id)
    session.exec(delete(RfiSummary).where(RfiSummary.rfi_id == case.id))
    summary = RfiSummary(
        rfi_id=case.id,
        summary_text=payload.summary_text,
        structured_json=payload.structured_json,
    )
    session.add(summary)
    case.status = RfiStatus.SUMMARIZED
    case.updated_at = datetime.utcnow()
    session.add(case)
    session.commit()
    session.refresh(summary)
    return RfiSummaryRead(
        rfi_id=summary.rfi_id,
        summary_text=summary.summary_text,
        structured_json=summary.structured_json,
        created_at=summary.created_at,
    )


def _get_case_or_404(session: Session, rfi_id: str) -> RfiCase:
    try:
        case_id = UUID(rfi_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid RFI id") from exc
    case = session.get(RfiCase, case_id)
    if not case:
        raise HTTPException(status_code=404, detail="RFI not found")
    return case


def _maybe_send_magic_link(case: RfiCase) -> None:
    if not case.magic_token:
        return
    if not (RESEND_API_KEY and EMAIL_FROM):
        return
    magic_link = f"{MAGIC_LINK_BASE_URL.rstrip('/')}/c/{case.magic_token}"
    payload = {
        "from": EMAIL_FROM,
        "to": [case.customer_email],
        "subject": "Your clarification request",
        "html": (
            "<p>Hello,</p>"
            "<p>Please use the link below to complete your clarification request:</p>"
            f"<p><a href=\"{magic_link}\">{magic_link}</a></p>"
            "<p>Thank you.</p>"
        ),
        "text": (
            "Hello,\n\n"
            "Please use the link below to complete your clarification request:\n"
            f"{magic_link}\n\n"
            "Thank you."
        ),
    }
    try:
        httpx.post(
            "https://api.resend.com/emails",
            headers={"Authorization": f"Bearer {RESEND_API_KEY}"},
            json=payload,
            timeout=10.0,
        )
    except httpx.HTTPError:
        pass


def _list_questions(session: Session, rfi_id: UUID) -> List[RfiQuestionRead]:
    statement = select(RfiQuestion).where(RfiQuestion.rfi_id == rfi_id)
    statement = statement.order_by(RfiQuestion.order_index.asc())
    questions = session.exec(statement).all()
    return [RfiQuestionRead.model_validate(item) for item in questions]


def _list_answers(session: Session, rfi_id: UUID) -> List[RfiAnswerRead]:
    statement = select(RfiAnswer).where(RfiAnswer.rfi_id == rfi_id)
    statement = statement.order_by(RfiAnswer.created_at.asc())
    answers = session.exec(statement).all()
    return [RfiAnswerRead.model_validate(item) for item in answers]


def _get_summary(session: Session, rfi_id: UUID) -> RfiSummaryRead | None:
    statement = select(RfiSummary).where(RfiSummary.rfi_id == rfi_id)
    summary = session.exec(statement).first()
    if not summary:
        return None
    return RfiSummaryRead(
        rfi_id=summary.rfi_id,
        summary_text=summary.summary_text,
        structured_json=summary.structured_json,
        created_at=summary.created_at,
    )
