from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from sqlalchemy import Column, JSON
from sqlmodel import Field, SQLModel


class RfiStatus(str, Enum):
    DRAFT = "DRAFT"
    INVITED = "INVITED"
    CALL_READY = "CALL_READY"
    IN_CALL = "IN_CALL"
    SUMMARIZED = "SUMMARIZED"
    DELIVERED = "DELIVERED"
    CLOSED = "CLOSED"


class CustomerStage(str, Enum):
    EXISTING_CUSTOMER = "EXISTING_CUSTOMER"
    LEAD = "LEAD"
    APPLICATION_PENDING = "APPLICATION_PENDING"


class CustomerProfile(SQLModel, table=True):
    __tablename__ = "customer_profiles"
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    customer_name: str
    bank_account_number: str
    customer_id: str = Field(max_length=5, index=True)
    stage: CustomerStage
    business_type: Optional[str] = None
    company_type: Optional[str] = None
    company_url: Optional[str] = None
    google_drive_link: Optional[str] = None


class RfiCase(SQLModel, table=True):
    __tablename__ = "rfi_cases"
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    customer_email: str
    application_id: Optional[str] = None
    status: RfiStatus = Field(default=RfiStatus.DRAFT)
    room_name: Optional[str] = None
    magic_token: Optional[str] = None
    expires_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class RfiQuestion(SQLModel, table=True):
    __tablename__ = "rfi_questions"
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    rfi_id: UUID = Field(foreign_key="rfi_cases.id")
    order_index: int
    question_text: str


class AnswerCapturedBy(str, Enum):
    AGENT = "agent"
    CUSTOMER_TEXT = "customer_text"


class RfiAnswer(SQLModel, table=True):
    __tablename__ = "rfi_answers"
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    rfi_id: UUID = Field(foreign_key="rfi_cases.id")
    question_id: UUID = Field(foreign_key="rfi_questions.id")
    answer_text: str
    captured_by: AnswerCapturedBy
    created_at: datetime = Field(default_factory=datetime.utcnow)


class RfiSummary(SQLModel, table=True):
    __tablename__ = "rfi_summaries"
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    rfi_id: UUID = Field(foreign_key="rfi_cases.id")
    summary_text: str
    structured_json: Dict[str, Any] = Field(
        default_factory=dict, sa_column=Column(JSON)
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)


class RfiCaseCreate(SQLModel):
    customer_email: str
    application_id: Optional[str] = None


class RfiCaseRead(SQLModel):
    id: UUID
    customer_email: str
    application_id: Optional[str] = None
    status: RfiStatus
    room_name: Optional[str] = None
    magic_token: Optional[str] = None
    expires_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class RfiQuestionInput(SQLModel):
    order_index: int
    question_text: str


class RfiQuestionsUpdate(SQLModel):
    questions: List[RfiQuestionInput]


class RfiQuestionRead(SQLModel):
    id: UUID
    rfi_id: UUID
    order_index: int
    question_text: str


class RfiAnswerInput(SQLModel):
    question_id: UUID
    answer_text: str
    captured_by: Optional[AnswerCapturedBy] = None


class RfiAnswersUpsert(SQLModel):
    answers: List[RfiAnswerInput]


class RfiAnswerRead(SQLModel):
    id: UUID
    rfi_id: UUID
    question_id: UUID
    answer_text: str
    captured_by: AnswerCapturedBy
    created_at: datetime


class RfiSummaryInput(SQLModel):
    summary_text: str
    structured_json: Dict[str, Any]


class RfiSummaryRead(SQLModel):
    rfi_id: UUID
    summary_text: str
    structured_json: Dict[str, Any]
    created_at: datetime


class RfiDetail(SQLModel):
    id: UUID
    customer_email: str
    application_id: Optional[str] = None
    status: RfiStatus
    room_name: Optional[str] = None
    magic_token: Optional[str] = None
    expires_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    questions: List[RfiQuestionRead]
    answers: List[RfiAnswerRead]
    summary: Optional[RfiSummaryRead] = None


class CustomerRfiDetail(SQLModel):
    id: UUID
    customer_email: str
    status: RfiStatus
    room_name: Optional[str] = None
    questions: List[RfiQuestionRead]
    answers: List[RfiAnswerRead]
    summary: Optional[RfiSummaryRead] = None


class LivekitTokenRequest(SQLModel):
    room_name: str
    identity: str
    name: Optional[str] = None
    metadata: Optional[str] = None
    can_publish: bool = True
    can_subscribe: bool = True


class LivekitTokenResponse(SQLModel):
    livekit_url: str
    token: str


class AgentJoinRequest(SQLModel):
    rfi_id: UUID
    room_name: str
    persist_answers: bool = True
    generate_summary: bool = True
    end_call_on_complete: bool = True


class StartCallRequest(SQLModel):
    persist_answers: bool = True
    generate_summary: bool = True
    end_call_on_complete: bool = True
