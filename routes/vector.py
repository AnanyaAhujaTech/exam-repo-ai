from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from db import get_db
from chroma.search import search

router = APIRouter()

#SEMANTIC SEARCH
@router.get("/search/questions")
def semantic_search(
    query: str,
    subject_name: str = None,
    semester: int = None,
    exam_type: str = None,
    department: str = None,
    academic_year: str = None,
    db: Session = Depends(get_db)
):

    filters = {}

    if subject_name:
        filters["subject_name"] = subject_name
    if semester:
        filters["semester"] = semester
    if exam_type:
        filters["exam_type"] = exam_type
    if department:
        filters["department"] = department
    if academic_year:
        filters["academic_year"] = academic_year

    chroma_results = search(query, filters=filters)

    ids = chroma_results["ids"][0] if chroma_results["ids"] else []

    if not ids:
        return {"results": []}

    questions = db.execute(
        "SELECT * FROM questions WHERE q_id = ANY(:ids)",
        {"ids": ids}
    ).fetchall()

    subparts = db.execute(
        "SELECT * FROM subparts WHERE s_id = ANY(:ids)",
        {"ids": ids}
    ).fetchall()

    return {
        "results": [dict(q) for q in questions] + [dict(s) for s in subparts]
    }

#SIMILAR QUES
@router.get("/similar/{q_id}")
def similar_questions(q_id: str, db: Session = Depends(get_db)):

    question = db.execute(
        "SELECT question_text FROM questions WHERE q_id = :id",
        {"id": q_id}
    ).fetchone()

    if not question:
        return {"error": "Not found"}

    chroma_results = search(question[0])

    ids = chroma_results["ids"][0]

    questions = db.execute(
        "SELECT * FROM questions WHERE q_id = ANY(:ids)",
        {"ids": ids}
    ).fetchall()

    subparts = db.execute(
        "SELECT * FROM subparts WHERE s_id = ANY(:ids)",
        {"ids": ids}
    ).fetchall()

    return {
        "similar_questions": [dict(q) for q in questions] + [dict(s) for s in subparts]
    }
