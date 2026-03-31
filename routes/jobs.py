from fastapi import APIRouter, HTTPException
from pipeline.orchestrator import get_job

router = APIRouter()

@router.get("/jobs/{job_id}")
def check_job_status(job_id: str):
    job_data = get_job(job_id)
    
    if not job_data:
        raise HTTPException(status_code=404, detail="Job not found")
        
    return {"job_id": job_id, "data": job_data}
