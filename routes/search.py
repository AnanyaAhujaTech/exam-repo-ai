from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from db import get_db

router = APIRouter()

@router.get("/search")
def search_questions(
    subject: str = None,
    unit: str = None,
    tag: str = None,
    db: Session = Depends(get_db)
):
    query = """
    SELECT q.q_id, q.question_text, q.unit, q.question_ai_tags
    FROM questions q
    JOIN paper_metadata p ON q.paper_id = p.paper_id
    WHERE 1=1
    """

    params = {}

    if subject:
        query += " AND p.subject_name ILIKE :subject"
        params["subject"] = f"%{subject}%"

    if unit:
        query += " AND q.unit = :unit"
        params["unit"] = unit

    if tag:
        query += " AND q.question_ai_tags::text ILIKE :tag"
        params["tag"] = f"%{tag}%"

    result = db.execute(query, params).fetchall()

    return {
        "results": [
            {
                "id": r[0],
                "question_text": r[1],
                "unit": r[2],
                "tags": r[3]
            }
            for r in result
        ]
    }
