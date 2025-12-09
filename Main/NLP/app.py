# app.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from nlp_service import analyse_text

app = FastAPI()

# Enable CORS for Angular frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:4200",  # Angular dev server
        "http://127.0.0.1:4200",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class SummRequest(BaseModel):
    text: str
    num_sentences: int = 6
    abstractive: bool = False

@app.post("/summarize")
def summarize(req: SummRequest):
    return analyse_text(req.text, num_sentences=req.num_sentences, do_abstractive=req.abstractive)