import uuid
import os
import time

from pipeline.ingestion import extract_content
from pipeline.regex_parser import parse_exam
from pipeline.ai_tagging import enrich_exam_json


# =========================
# JOB TRACKING (TEMP - in-memory)
# =========================

PIPELINE_JOBS = {}


def create_job(file_name):
    job_id = str(uuid.uuid4())

    PIPELINE_JOBS[job_id] = {
        "file_name": file_name,
        "status": "processing",
        "progress": 0,
        "message": "Starting pipeline...",
        "created_at": time.time()
    }

    return job_id


def update_job(job_id, progress, message):
    if job_id in PIPELINE_JOBS:
        PIPELINE_JOBS[job_id]["progress"] = progress
        PIPELINE_JOBS[job_id]["message"] = message


def complete_job(job_id):
    if job_id in PIPELINE_JOBS:
        PIPELINE_JOBS[job_id]["status"] = "completed"
        PIPELINE_JOBS[job_id]["progress"] = 100
        PIPELINE_JOBS[job_id]["message"] = "Completed successfully"


def fail_job(job_id, error):
    if job_id in PIPELINE_JOBS:
        PIPELINE_JOBS[job_id]["status"] = "failed"
        PIPELINE_JOBS[job_id]["message"] = str(error)


def get_job(job_id):
    return PIPELINE_JOBS.get(job_id, None)


# =========================
# MAIN PIPELINE
# =========================

def process_exam(file_path):

    file_name = os.path.basename(file_path)
    job_id = create_job(file_name)

    try:
        # -------- STEP 1: INGESTION --------
        update_job(job_id, 10, "Extracting content...")
        extracted = extract_content(file_path)

        # -------- STEP 2: REGEX --------
        update_job(job_id, 30, "Parsing exam structure...")
        parsed = parse_exam(extracted)

        # -------- STEP 3: AI TAGGING --------
        update_job(job_id, 60, "Running AI tagging...")
        enriched, metrics = enrich_exam_json(parsed)

        # -------- STEP 4: DB INSERT (placeholder) --------
        update_job(job_id, 80, "Saving to database...")
        # TODO: insert_into_db(enriched)

        # -------- STEP 5: CHROMA INSERT (placeholder) --------
        update_job(job_id, 90, "Indexing for search...")
        # TODO: insert_into_chroma(enriched)

        # -------- COMPLETE --------
        complete_job(job_id)

        return {
            "job_id": job_id,
            "paper_id": enriched.get("paper_id"),
            "metrics": metrics
        }

    except Exception as e:
        fail_job(job_id, str(e))

        return {
            "job_id": job_id,
            "error": str(e)
        }
