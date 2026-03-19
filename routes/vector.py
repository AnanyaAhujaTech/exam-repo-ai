from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text  # Required for raw SQL binding
from db import get_db
from chroma.search import search

router = APIRouter()

# =========================
# SEMANTIC SEARCH
# =========================
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

    # 1. Build Chroma-compatible filter syntax
    conditions = []
    
    if subject_name:
        conditions.append({"subject_name": subject_name})
    if semester:
        conditions.append({"semester": semester})
    if exam_type:
        conditions.append({"exam_type": exam_type})
    if department:
        conditions.append({"department": department})
    if academic_year:
        conditions.append({"academic_year": academic_year})

    # Format for ChromaDB
    chroma_filters = None
    if len(conditions) == 1:
        chroma_filters = conditions[0]
    elif len(conditions) > 1:
        chroma_filters = {"$and": conditions}

    # 2. Search Chroma for the IDs
    chroma_results = search(query, filters=chroma_filters)

    ids = chroma_results["ids"][0] if chroma_results and chroma_results["ids"] else []

    if not ids:
        return {"results": []}

    # 3. Fetch full records from PostgreSQL
    questions = db.execute(
        text("SELECT * FROM questions WHERE q_id = ANY(:ids)"),
        {"ids": ids}
    ).fetchall()

    subparts = db.execute(
        text("SELECT * FROM subparts WHERE s_id = ANY(:ids)"),
        {"ids": ids}
    ).fetchall()

    return {
        "results": [dict(q) for q in questions] + [dict(s) for s in subparts]
    }


# =========================
# SIMILAR QUESTIONS
# =========================
@router.get("/similar/{q_id}")
def similar_questions(q_id: str, db: Session = Depends(get_db)):

    # 1. Look up the original question text
    question = db.execute(
        text("SELECT question_text FROM questions WHERE q_id = :id"),
        {"id": q_id}
    ).fetchone()

    if not question:
        return {"error": "Question not found"}

    # 2. Use the text to query Chroma
    chroma_results = search(question[0])
    
    ids = chroma_results["ids"][0] if chroma_results and chroma_results["ids"] else []
    
    if not ids:
        return {"similar_questions": []}

    # 3. Fetch the similar full records from PostgreSQL
    questions = db.execute(
        text("SELECT * FROM questions WHERE q_id = ANY(:ids) AND q_id != :original_id"),
        {"ids": ids, "original_id": q_id} # Filter out the exact question they searched with
    ).fetchall()

    subparts = db.execute(
        text("SELECT * FROM subparts WHERE s_id = ANY(:ids)"),
        {"ids": ids}
    ).fetchall()

    return {
        "similar_questions": [dict(q) for q in questions] + [dict(s) for s in subparts]
    }
