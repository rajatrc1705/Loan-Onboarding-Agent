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
    NEEDS_REVIEW = "NEEDS_REVIEW"
    CLOSED = "CLOSED"


class CustomerStage(str, Enum):
    EXISTING_CUSTOMER = "EXISTING_CUSTOMER"
    LEAD = "LEAD"
    APPLICATION_PENDING = "APPLICATION_PENDING"


class CustomerProfile(SQLModel, table=True):
    __tablename__ = "customer_profiles"
    id: UUID = Field(default_factory=uuid4)
    customer_name: str
    bank_account_number: str
    customer_id: str = Field(max_length=5, primary_key=True)
    stage: CustomerStage
    business_type: Optional[str] = None
    company_type: Optional[str] = None
    company_url: Optional[str] = None
    google_drive_link: Optional[str] = None


class Application(SQLModel, table=True):
    __tablename__ = "applications"
    application_id: str = Field(primary_key=True)
    customer_id: str = Field(
        max_length=5, foreign_key="customer_profiles.customer_id", index=True
    )
    requested_loan_amount: float
    requested_tenure_amount: int
    issue_status: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class RfiCase(SQLModel, table=True):
    __tablename__ = "rfi_cases"
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    customer_email: str
    application_id: Optional[str] = None
    status: RfiStatus = Field(default=RfiStatus.DRAFT)
    room_name: Optional[str] = None
    magic_token: Optional[str] = None
    expires_at: Optional[datetime] = None
    needs_review: bool = Field(default=False)
    review_reason: Optional[str] = None
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


class AnswerStatus(str, Enum):
    ANSWERED = "answered"
    UNCLEAR = "unclear"
    NOT_ANSWERED = "not_answered"


class RfiAnswer(SQLModel, table=True):
    __tablename__ = "rfi_answers"
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    rfi_id: UUID = Field(foreign_key="rfi_cases.id")
    question_id: UUID = Field(foreign_key="rfi_questions.id")
    answer_text: str
    answer_status: AnswerStatus = Field(default=AnswerStatus.ANSWERED)
    evidence_quote: Optional[str] = None
    follow_up_asked: bool = Field(default=False)
    evaluator_notes: Optional[str] = None
    captured_by: AnswerCapturedBy
    created_at: datetime = Field(default_factory=datetime.utcnow)


class RfiCustomerQuestion(SQLModel, table=True):
    __tablename__ = "rfi_customer_questions"
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    rfi_id: UUID = Field(foreign_key="rfi_cases.id")
    question_text: str
    agent_response: Optional[str] = None
    needs_human_followup: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class TranscriptSpeaker(str, Enum):
    AGENT = "agent"
    CUSTOMER = "customer"
    SYSTEM = "system"


class RfiTranscriptTurn(SQLModel, table=True):
    __tablename__ = "rfi_transcript_turns"
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    rfi_id: UUID = Field(foreign_key="rfi_cases.id")
    speaker: TranscriptSpeaker
    text: str
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


class ApplicationRead(SQLModel):
    application_id: str
    customer_id: str
    requested_loan_amount: float
    requested_tenure_amount: int
    issue_status: Optional[str] = None
    created_at: datetime


class ApplicationList(SQLModel):
    items: List[ApplicationRead]
    total: int


class RfiCaseRead(SQLModel):
    id: UUID
    customer_email: str
    application_id: Optional[str] = None
    status: RfiStatus
    room_name: Optional[str] = None
    magic_token: Optional[str] = None
    expires_at: Optional[datetime] = None
    needs_review: bool = False
    review_reason: Optional[str] = None
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
    answer_status: Optional[AnswerStatus] = None
    evidence_quote: Optional[str] = None
    follow_up_asked: bool = False
    evaluator_notes: Optional[str] = None
    captured_by: Optional[AnswerCapturedBy] = None


class RfiAnswersUpsert(SQLModel):
    answers: List[RfiAnswerInput]


class RfiAnswerRead(SQLModel):
    id: UUID
    rfi_id: UUID
    question_id: UUID
    answer_text: str
    answer_status: AnswerStatus
    evidence_quote: Optional[str] = None
    follow_up_asked: bool
    evaluator_notes: Optional[str] = None
    captured_by: AnswerCapturedBy
    created_at: datetime


class RfiCustomerQuestionInput(SQLModel):
    question_text: str
    agent_response: Optional[str] = None
    needs_human_followup: bool = True


class RfiCustomerQuestionsUpsert(SQLModel):
    questions: List[RfiCustomerQuestionInput]


class RfiCustomerQuestionRead(SQLModel):
    id: UUID
    rfi_id: UUID
    question_text: str
    agent_response: Optional[str] = None
    needs_human_followup: bool
    created_at: datetime


class RfiTranscriptTurnInput(SQLModel):
    speaker: TranscriptSpeaker
    text: str


class RfiTranscriptTurnsUpsert(SQLModel):
    turns: List[RfiTranscriptTurnInput]


class RfiTranscriptTurnRead(SQLModel):
    id: UUID
    rfi_id: UUID
    speaker: TranscriptSpeaker
    text: str
    created_at: datetime


class RfiSummaryInput(SQLModel):
    summary_text: str
    structured_json: Dict[str, Any]
    needs_review: bool = False
    review_reason: Optional[str] = None


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
    needs_review: bool = False
    review_reason: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    questions: List[RfiQuestionRead]
    answers: List[RfiAnswerRead]
    customer_questions: List[RfiCustomerQuestionRead] = Field(default_factory=list)
    transcript: List[RfiTranscriptTurnRead] = Field(default_factory=list)
    summary: Optional[RfiSummaryRead] = None


class CustomerRfiDetail(SQLModel):
    id: UUID
    customer_email: str
    status: RfiStatus
    room_name: Optional[str] = None
    needs_review: bool = False
    review_reason: Optional[str] = None
    questions: List[RfiQuestionRead]
    answers: List[RfiAnswerRead]
    customer_questions: List[RfiCustomerQuestionRead] = Field(default_factory=list)
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


class RfiNeedsReviewInput(SQLModel):
    reason: str


class RfiCallCompleteInput(SQLModel):
    needs_review: bool = False
    review_reason: Optional[str] = None
