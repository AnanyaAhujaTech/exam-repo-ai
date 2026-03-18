from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from db import get_db

router = APIRouter()

@router.get("/repeated/question/{hash}")
def repeated_questions(hash: str, db: Session = Depends(get_db)):

    result = db.execute(
        "SELECT * FROM questions WHERE question_hash = :hash",
        {"hash": hash}
    ).fetchall()

    return {
        "repeated_questions": [dict(r) for r in result]
    }


@router.get("/repeated/subpart/{hash}")
def repeated_subparts(hash: str, db: Session = Depends(get_db)):

    result = db.execute(
        "SELECT * FROM subparts WHERE subquestion_hash = :hash",
        {"hash": hash}
    ).fetchall()

    return {
        "repeated_subparts": [dict(r) for r in result]
    }
