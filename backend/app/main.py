import os
from contextlib import asynccontextmanager, contextmanager

import psycopg
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field


DATABASE_URL = os.getenv("DATABASE_URL")


class TicketCreate(BaseModel):
    title: str = Field(min_length=1, max_length=150)
    description: str = Field(min_length=1, max_length=500)
    priority: str = Field(min_length=1, max_length=50)


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
                CREATE TABLE IF NOT EXISTS tickets (
                    id SERIAL PRIMARY KEY,
                    title VARCHAR(150) NOT NULL,
                    description VARCHAR(500) NOT NULL,
                    priority VARCHAR(50) NOT NULL,
                    status VARCHAR(50) NOT NULL DEFAULT 'Abierto',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                """
            )

        conn.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="Foro 7 - API Mesa de Ayuda", lifespan=lifespan)


@app.get("/")
def root():
    return {
        "message": "API de mesa de ayuda funcionando",
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


@app.post("/tickets", status_code=201)
def create_ticket(ticket: TicketCreate):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO tickets (title, description, priority)
                VALUES (%s, %s, %s)
                RETURNING id, title, description, priority, status;
                """,
                (
                    ticket.title,
                    ticket.description,
                    ticket.priority,
                ),
            )

            row = cur.fetchone()

        conn.commit()

    return {
        "id": row[0],
        "title": row[1],
        "description": row[2],
        "priority": row[3],
        "status": row[4],
    }


@app.get("/tickets")
def list_tickets():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, title, description, priority, status, created_at
                FROM tickets
                ORDER BY id DESC;
                """
            )

            rows = cur.fetchall()

    return [
        {
            "id": row[0],
            "title": row[1],
            "description": row[2],
            "priority": row[3],
            "status": row[4],
            "created_at": row[5].isoformat(),
        }
        for row in rows
    ]


@app.get("/tickets/stats")
def ticket_stats():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM tickets;")
            total = cur.fetchone()[0]

            cur.execute(
                """
                SELECT status, COUNT(*)
                FROM tickets
                GROUP BY status;
                """
            )

            rows = cur.fetchall()

    return {
        "total": total,
        "by_status": {
            row[0]: row[1]
            for row in rows
        },
    }