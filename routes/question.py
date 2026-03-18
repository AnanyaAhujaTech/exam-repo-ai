from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from db import get_db

router = APIRouter()

@router.get("/question/{q_id}")
def get_question(q_id: str, db: Session = Depends(get_db)):

    question = db.execute(
        "SELECT * FROM questions WHERE q_id = :q_id",
        {"q_id": q_id}
    ).fetchone()

    subparts = db.execute(
        "SELECT * FROM subparts WHERE q_id = :q_id",
        {"q_id": q_id}
    ).fetchall()

    return {
        "question": dict(question) if question else None,
        "subparts": [dict(sp) for sp in subparts]
    }
