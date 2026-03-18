from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from db import get_db
from vector_search import search_ids

router = APIRouter()


# SEMANTIC SEARCH (DB CONNECTED)
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

    filters = {
        "subject_name": subject_name,
        "semester": semester,
        "exam_type": exam_type,
        "department": department,
        "academic_year": academic_year
    }

    vector_results = search_ids(query, top_k=10, filters=filters)

    ids = [r["id"] for r in vector_results]

    if not ids:
        return {"results": []}

    # Fetch from BOTH tables
    questions = db.execute(
        "SELECT * FROM questions WHERE q_id = ANY(:ids)",
        {"ids": ids}
    ).fetchall()

    subparts = db.execute(
        "SELECT * FROM subparts WHERE s_id = ANY(:ids)",
        {"ids": ids}
    ).fetchall()

    # convert to dict
    results = [dict(q) for q in questions] + [dict(s) for s in subparts]

    return {"results": results}

# SIMILAR QUESTIONS (DB CONNECTED)
@router.get("/similar/{q_id}")
def similar_questions(q_id: str, db: Session = Depends(get_db)):

    # get original text from DB
    question = db.execute(
        "SELECT question_text FROM questions WHERE q_id = :id",
        {"id": q_id}
    ).fetchone()

    if not question:
        return {"error": "Question not found"}

    vector_results = search_ids(question[0], top_k=10)

    ids = [r["id"] for r in vector_results]

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
