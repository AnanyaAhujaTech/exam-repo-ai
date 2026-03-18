from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from db import get_db

router = APIRouter()

@router.get("/paper/{paper_id}")
def get_paper(paper_id: str, db: Session = Depends(get_db)):

    paper = db.execute(
        "SELECT * FROM exam_papers WHERE paper_id = :pid",
        {"pid": paper_id}
    ).fetchone()

    metadata = db.execute(
        "SELECT * FROM paper_metadata WHERE paper_id = :pid",
        {"pid": paper_id}
    ).fetchone()

    return {
        "paper": dict(paper) if paper else None,
        "metadata": dict(metadata) if metadata else None
    }
