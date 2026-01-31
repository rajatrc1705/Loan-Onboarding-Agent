from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlmodel import Session, select

from ..db import get_session
from ..models import Application, ApplicationList, ApplicationRead

router = APIRouter()


@router.get("")
def list_applications(
    search: Optional[str] = Query(default=None, max_length=200),
    limit: int = Query(default=20, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    session: Session = Depends(get_session),
) -> ApplicationList:
    statement = select(Application)
    count_statement = select(func.count()).select_from(Application)
    if search:
        search_value = f"%{search.lower()}%"
        statement = statement.where(
            func.lower(Application.application_id).like(search_value)
        )
        count_statement = count_statement.where(
            func.lower(Application.application_id).like(search_value)
        )
    statement = (
        statement.order_by(Application.application_id.asc())
        .offset(offset)
        .limit(limit)
    )
    applications = session.exec(statement).all()
    total = session.exec(count_statement).one()
    return ApplicationList(
        items=[ApplicationRead.model_validate(item) for item in applications],
        total=total,
    )
