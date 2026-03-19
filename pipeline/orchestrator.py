import uuid
import os
import time
import logging
import traceback
import threading

from ingestion import extract_content
from regex_parser import parse_exam
from ai_tagging import enrich_exam_json

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# =========================
# JOB TRACKING (In-memory)
# =========================

PIPELINE_JOBS = {}
JOB_RETENTION_SECONDS = 3600 * 24  # Keep jobs in memory for 24 hours


def cleanup_old_jobs():
    """
    Prevents memory leaks by deleting jobs older than the retention period.
    """
    current_time = time.time()
    jobs_to_delete = []
    
    for job_id, job_data in PIPELINE_JOBS.items():
        if current_time - job_data["created_at"] > JOB_RETENTION_SECONDS:
            jobs_to_delete.append(job_id)
            
    for job_id in jobs_to_delete:
        del PIPELINE_JOBS[job_id]


def create_job(file_name):
    # Run cleanup every time a new job is created
    cleanup_old_jobs()
    
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


def complete_job(job_id, paper_id, metrics):
    if job_id in PIPELINE_JOBS:
        PIPELINE_JOBS[job_id]["status"] = "completed"
        PIPELINE_JOBS[job_id]["progress"] = 100
        PIPELINE_JOBS[job_id]["message"] = "Completed successfully"
        # Store results so the UI can fetch them when complete
        PIPELINE_JOBS[job_id]["paper_id"] = paper_id
        PIPELINE_JOBS[job_id]["metrics"] = metrics


def fail_job(job_id, error_msg):
    if job_id in PIPELINE_JOBS:
        PIPELINE_JOBS[job_id]["status"] = "failed"
        PIPELINE_JOBS[job_id]["message"] = str(error_msg)


def get_job(job_id):
    return PIPELINE_JOBS.get(job_id, None)


# =========================
# INTERNAL PIPELINE WORKER
# =========================

def _run_pipeline(job_id, file_path, file_name):
    """
    The actual heavy lifting that runs in the background thread.
    """
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
        complete_job(job_id, enriched.get("paper_id"), metrics)

    except Exception as e:
        # Log the full traceback to the console for debugging
        logging.error(f"Pipeline failed for {file_name}:\n{traceback.format_exc()}")
        
        # Update the job tracker with a readable error
        fail_job(job_id, str(e))


# =========================
# PUBLIC ASYNC ENTRY POINT
# =========================

def process_exam_async(file_path):
    """
    Triggers the pipeline in a background thread and returns the job_id immediately.
    Your web API should call this function.
    """
    file_name = os.path.basename(file_path)
    
    # 1. Create the job synchronously so we can return the ID to the UI
    job_id = create_job(file_name)

    # 2. Spawn the background thread to do the work
    thread = threading.Thread(target=_run_pipeline, args=(job_id, file_path, file_name))
    thread.daemon = True # Allows the script to exit even if this thread is hanging
    thread.start()

    # 3. Return the ID instantly
    return job_id
