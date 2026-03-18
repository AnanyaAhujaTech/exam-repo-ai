from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from db import get_db

router = APIRouter()

@router.get("/search")
def search_papers(
    subject_name: str = None,
    semester: int = None,
    exam_type: str = None,
    department: str = None,
    academic_year: str = None,
    db: Session = Depends(get_db)
):
    query = """
    SELECT 
        p.paper_id,
        p.subject_name,
        p.semester,
        p.exam_type,
        p.department,
        p.academic_year,
        e.file_path
    FROM paper_metadata p
    JOIN exam_papers e ON p.paper_id = e.paper_id
    WHERE 1=1
    """

    params = {}

    if subject_name:
        query += " AND p.subject_name ILIKE :subject"
        params["subject"] = f"%{subject_name}%"

    if semester:
        query += " AND p.semester = :semester"
        params["semester"] = semester

    if exam_type:
        query += " AND p.exam_type ILIKE :exam_type"
        params["exam_type"] = f"%{exam_type}%"

    if department:
        query += " AND p.department ILIKE :dept"
        params["dept"] = f"%{department}%"

    if academic_year:
        query += " AND p.academic_year = :year"
        params["year"] = academic_year

    result = db.execute(query, params).fetchall()

    return {
        "papers": [
            {
                "paper_id": r[0],
                "subject_name": r[1],
                "semester": r[2],
                "exam_type": r[3],
                "department": r[4],
                "academic_year": r[5],
                "file_path": r[6]
            }
            for r in result
        ]
    }
