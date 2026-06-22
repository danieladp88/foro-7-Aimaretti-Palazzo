import os
from contextlib import asynccontextmanager, contextmanager

import psycopg
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel


DATABASE_URL = os.getenv("DATABASE_URL")


class NoteCreate(BaseModel):
    text: str


@contextmanager
def get_connection():
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL no configurada")

    conn = psycopg.connect(DATABASE_URL)

    try:
        yield conn
    finally:
        conn.close()


def init_db():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS notes (
                    id SERIAL PRIMARY KEY,
                    text VARCHAR(255) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                """
            )

        conn.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="Foro 7 API", lifespan=lifespan)

@app.get("/")
def root():
    return {
        "message": "Foro 7 API funcionando",
        "docs": "/docs",
        "health": "/health",
    }

@app.get("/health")
def health():
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1;")
                cur.fetchone()

        return {"status": "ok"}

    except Exception as exc:
        raise HTTPException(status_code=503, detail=str(exc))


@app.post("/notes", status_code=201)
def create_note(note: NoteCreate):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO notes (text) VALUES (%s) RETURNING id, text;",
                (note.text,),
            )

            row = cur.fetchone()

        conn.commit()

    return {
        "id": row[0],
        "text": row[1],
    }


@app.get("/notes")
def list_notes():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, text, created_at
                FROM notes
                ORDER BY id DESC;
                """
            )

            rows = cur.fetchall()

    return [
        {
            "id": row[0],
            "text": row[1],
            "created_at": row[2].isoformat(),
        }
        for row in rows
    ]