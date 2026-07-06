from datetime import datetime
from typing import List
from uuid import UUID

from fastapi import APIRouter, Body, Depends, HTTPException
from sqlmodel import Session, select

from ..db import get_session
from ..models import (
    AnswerCapturedBy,
    CustomerRfiDetail,
    RfiAnswer,
    RfiAnswerRead,
    RfiAnswersUpsert,
    RfiCase,
    RfiCustomerQuestion,
    RfiCustomerQuestionRead,
    RfiQuestion,
    RfiQuestionRead,
    RfiSummary,
    RfiSummaryRead,
    RfiStatus,
)

router = APIRouter()


@router.get("/{token}")
def get_magic_link(
    token: str, session: Session = Depends(get_session)
) -> CustomerRfiDetail:
    case = _get_case_by_token(session, token)
    if case.expires_at and case.expires_at < datetime.utcnow():
        raise HTTPException(status_code=410, detail="Magic link expired")
    if case.status == RfiStatus.INVITED:
        case.status = RfiStatus.CALL_READY
        case.updated_at = datetime.utcnow()
        session.add(case)
        session.commit()
    questions = _list_questions(session, case.id)
    answers = _list_answers(session, case.id)
    customer_questions = _list_customer_questions(session, case.id)
    summary = _get_summary(session, case.id)
    return CustomerRfiDetail(
        id=case.id,
        customer_email=case.customer_email,
        status=case.status,
        room_name=case.room_name,
        needs_review=case.needs_review,
        review_reason=case.review_reason,
        questions=questions,
        answers=answers,
        customer_questions=customer_questions,
        summary=summary,
    )


@router.post("/{token}/answer")
def post_fallback_answers(
    token: str,
    payload: RfiAnswersUpsert = Body(...),
    session: Session = Depends(get_session),
) -> List[RfiAnswerRead]:
    case = _get_case_by_token(session, token)
    for answer in payload.answers:
        session.add(
            RfiAnswer(
                rfi_id=case.id,
                question_id=answer.question_id,
                answer_text=answer.answer_text,
                captured_by=AnswerCapturedBy.CUSTOMER_TEXT,
            )
        )
    case.updated_at = datetime.utcnow()
    session.add(case)
    session.commit()
    return _list_answers(session, case.id)


@router.post("/{token}/submit")
def submit_answers(token: str, session: Session = Depends(get_session)) -> dict:
    case = _get_case_by_token(session, token)
    if case.status not in (RfiStatus.IN_CALL, RfiStatus.SUMMARIZED, RfiStatus.CALL_READY):
        raise HTTPException(status_code=409, detail="Case is not ready to submit")
    case.status = RfiStatus.DELIVERED
    case.updated_at = datetime.utcnow()
    session.add(case)
    session.commit()
    return {"status": "delivered"}


def _get_case_by_token(session: Session, token: str) -> RfiCase:
    statement = select(RfiCase).where(RfiCase.magic_token == token)
    case = session.exec(statement).first()
    if not case:
        raise HTTPException(status_code=404, detail="Magic link not found")
    return case


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


def _list_customer_questions(
    session: Session, rfi_id: UUID
) -> List[RfiCustomerQuestionRead]:
    statement = select(RfiCustomerQuestion).where(RfiCustomerQuestion.rfi_id == rfi_id)
    statement = statement.order_by(RfiCustomerQuestion.created_at.asc())
    questions = session.exec(statement).all()
    return [RfiCustomerQuestionRead.model_validate(item) for item in questions]


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
