import json
import logging
from sqlalchemy import text
from db import SessionLocal  # Imports the connection you made in db.py

def insert_into_db(enriched_data, pdf_path):
    """
    Takes the final JSON from the pipeline and inserts it into PostgreSQL.
    """
    db = SessionLocal()
    
    try:
        paper_id = enriched_data["paper_id"]
        meta = enriched_data["paper_metadata"]
        
        # 1. Insert into exam_papers
        db.execute(
            text("""
            INSERT INTO exam_papers (paper_id, pdf_path) 
            VALUES (:paper_id, :pdf_path)
            ON CONFLICT (paper_id) DO NOTHING
            """),
            {"paper_id": paper_id, "pdf_path": pdf_path}
        )
        
        # 2. Insert into paper_metadata
        db.execute(
            text("""
            INSERT INTO paper_metadata 
            (paper_id, subject_code, subject_name, program, department, semester, academic_year, exam_type, exam_name, time_duration, max_marks)
            VALUES 
            (:paper_id, :subj_code, :subj_name, :prog, :dept, :sem, :acad_year, :ex_type, :ex_name, :dur, :marks)
            ON CONFLICT (paper_id) DO NOTHING
            """),
            {
                "paper_id": paper_id,
                "subj_code": meta.get("subject_code"),
                "subj_name": meta.get("subject_name"),
                "prog": meta.get("program"),
                "dept": meta.get("department"),
                "sem": meta.get("semester"),
                "acad_year": meta.get("academic_year"),
                "ex_type": meta.get("exam_type"),
                "ex_name": meta.get("exam_name"),
                "dur": meta.get("time_duration"),
                "marks": meta.get("max_marks", 0)
            }
        )
        
        # 3. Insert Questions
        for q in enriched_data.get("questions", []):
            # Generate the globally unique q_id (e.g. "AMC152_2024_MIDSEM_Q1")
            q_id = f"{paper_id}_{q['question_id']}"
            
            db.execute(
                text("""
                INSERT INTO questions 
                (q_id, paper_id, question_id, unit, question_text, marks, question_hash, question_ai_tags, question_ai_confidence, question_syllabus_topics)
                VALUES 
                (:q_id, :paper_id, :qid_str, :unit, :text, :marks, :hash, :tags, :conf, :topics)
                ON CONFLICT (q_id) DO NOTHING
                """),
                {
                    "q_id": q_id,
                    "paper_id": paper_id,
                    "qid_str": q["question_id"],
                    "unit": q.get("unit"),
                    "text": q.get("question_text", ""),
                    "marks": q.get("marks") or 0,
                    "hash": q.get("question_hash"),
                    # Convert dicts/lists to JSON strings for PostgreSQL JSONB columns
                    "tags": json.dumps(q.get("ai_tags")) if q.get("ai_tags") else None,
                    "conf": json.dumps(q.get("ai_confidence")) if q.get("ai_confidence") else None,
                    "topics": json.dumps(q.get("syllabus_topics")) if q.get("syllabus_topics") else None
                }
            )
            
            # 4. Insert Subparts
            for sp in q.get("subparts", []):
                # Generate unique subpart id (e.g. "AMC152_2024_MIDSEM_Q1_a")
                s_id = f"{q_id}_{sp['subpart_id']}"
                
                db.execute(
                    text("""
                    INSERT INTO subparts 
                    (s_id, q_id, paper_id, subpart_id, text, marks, subquestion_hash, subpart_ai_tags, subpart_ai_confidence, subpart_syllabus_topics)
                    VALUES 
                    (:s_id, :q_id, :paper_id, :sp_id, :text, :marks, :hash, :tags, :conf, :topics)
                    ON CONFLICT (s_id) DO NOTHING
                    """),
                    {
                        "s_id": s_id,
                        "q_id": q_id,
                        "paper_id": paper_id,
                        "sp_id": sp["subpart_id"],
                        "text": sp.get("text", ""),
                        "marks": sp.get("marks") or 0,
                        "hash": sp.get("subquestion_hash"),
                        "tags": json.dumps(sp.get("ai_tags")) if sp.get("ai_tags") else None,
                        "conf": json.dumps(sp.get("ai_confidence")) if sp.get("ai_confidence") else None,
                        "topics": json.dumps(sp.get("syllabus_topics")) if sp.get("syllabus_topics") else None
                    }
                )
        
        # Commit the transaction to save to disk
        db.commit()
        logging.info(f"Successfully saved {paper_id} to PostgreSQL database.")
        
    except Exception as e:
        db.rollback() # If anything fails, undo all database changes for this paper
        logging.error(f"Database insertion failed: {e}")
        raise e
    finally:
        db.close()
