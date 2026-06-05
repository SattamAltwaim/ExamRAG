import sys
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

sys.path.insert(0, str(Path(__file__).resolve().parent))

import config
import rag
import vlm
from ingest import ingest_all_content


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        count = rag.get_collection_count()
    except Exception:
        count = 0
    if count == 0:
        print("ChromaDB empty — running initial ingestion...")
        ingest_all_content()
    else:
        print(f"ChromaDB has {count} documents, skipping ingestion.")
    yield


app = FastAPI(title="ExamRAG", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class GradeRequest(BaseModel):
    image: str
    course_topic: str | None = None


@app.get("/api/health")
def health():
    return {"status": "ok", "documents": rag.get_collection_count()}


@app.get("/api/courses")
def courses():
    return {"courses": rag.get_topics()}


@app.post("/api/grade")
async def grade(req: GradeRequest):
    extraction = await vlm.extract_answers(req.image)
    questions = extraction.get("questions", [])
    if not questions:
        raise HTTPException(400, "Could not extract any questions from the image.")

    graded = []
    total_score = 0
    total_max = 0

    for q in questions:
        query = f"{q.get('question_text', '')} {q.get('student_answer', '')}"
        chunks = rag.retrieve_context(query, n_results=5, topic=req.course_topic)
        context = "\n\n---\n\n".join(
            f"[{c['metadata']['topic']} — Slide {c['metadata']['slide_number']}]\n{c['text']}"
            for c in chunks
        )

        result = await vlm.grade_answer(
            question_text=q.get("question_text", ""),
            student_answer=q.get("student_answer", "No answer provided"),
            course_context=context,
        )

        score = result.get("score", 0)
        max_score = result.get("max_score", q.get("max_score", 10))
        total_score += score
        total_max += max_score

        graded.append({
            "question_number": q.get("question_number"),
            "question_text": q.get("question_text"),
            "student_answer": q.get("student_answer"),
            "score": score,
            "max_score": max_score,
            "feedback": result.get("feedback", ""),
            "key_concepts_expected": result.get("key_concepts_expected", []),
            "concepts_demonstrated": result.get("concepts_demonstrated", []),
            "sources_used": [
                f"{c['metadata']['topic']} slide {c['metadata']['slide_number']}"
                for c in chunks[:3]
            ],
        })

    percentage = round((total_score / total_max) * 100, 1) if total_max > 0 else 0

    return {
        "student_name": extraction.get("student_name"),
        "total_score": total_score,
        "max_total_score": total_max,
        "percentage": percentage,
        "questions": graded,
    }


@app.post("/api/ingest")
def run_ingest():
    ingest_all_content()
    return {"status": "ok", "documents": rag.get_collection_count()}
