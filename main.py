from fastapi import FastAPI
from routes import search, question, repeated, paper, vector

app = FastAPI()

app.include_router(search.router)
app.include_router(question.router)
app.include_router(repeated.router)
app.include_router(paper.router)
app.include_router(vector.router)
