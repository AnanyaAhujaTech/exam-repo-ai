from fastapi import APIRouter, Query
from vector_search import search, metadata

router = APIRouter()


# SEMANTIC SEARCH
@router.get("/search/questions")
def semantic_search(
    query: str,
    subject_name: str = None,
    semester: int = None,
    exam_type: str = None,
    department: str = None,
    academic_year: str = None
):

    filters = {
        "subject_name": subject_name,
        "semester": semester,
        "exam_type": exam_type,
        "department": department,
        "academic_year": academic_year
    }

    results = search(query, top_k=10, filters=filters)

    return {"results": results}


# SIMILAR QUESTIONS
@router.get("/similar/{q_id}")
def similar_questions(q_id: str):

    original = next((m for m in metadata if m["id"] == q_id), None)

    if not original:
        return {"error": "Question not found"}

    results = search(original["text"], top_k=10)

    return {"similar_questions": results}
