from contextlib import asynccontextmanager
from fastapi import FastAPI
from routes import search, question, repeated, paper, vector, jobs
from watcher import start_watcher

@asynccontextmanager
async def lifespan(app: FastAPI):
    observer = start_watcher()
    yield
    observer.stop()
    observer.join()

app = FastAPI(lifespan=lifespan)

app.include_router(search.router)
app.include_router(question.router)
app.include_router(repeated.router)
app.include_router(paper.router)
app.include_router(vector.router)
app.include_router(jobs.router)
