from groq import Groq
from sqlalchemy import text
from app.database import engine
from app.config import GROQ_API_KEY

client = Groq(api_key=GROQ_API_KEY)

def get_embedding(texto: str) -> list:
    response = client.embeddings.create(
        model="nomic-embed-text-v1_5",
        input=texto
    )
    return response.data[0].embedding

def init_rag():
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS conocimiento (
                id SERIAL PRIMARY KEY,
                categoria VARCHAR(50),
                titulo VARCHAR(200),
                contenido TEXT,
                embedding vector(768)
            )
        """))
        conn.commit()

def agregar_conocimiento(categoria: str, titulo: str, contenido: str):
    embedding = get_embedding(contenido)
    with engine.connect() as conn:
        conn.execute(text("""
            INSERT INTO conocimiento (categoria, titulo, contenido, embedding)
            VALUES (:categoria, :titulo, :contenido, :embedding)
        """), {
            "categoria": categoria,
            "titulo": titulo,
            "contenido": contenido,
            "embedding": str(embedding)
        })
        conn.commit()

def buscar_conocimiento(consulta: str, limite: int = 3) -> list:
    embedding = get_embedding(consulta)
    with engine.connect() as conn:
        resultado = conn.execute(text("""
            SELECT titulo, contenido, categoria,
            1 - (embedding <=> :embedding::vector) as similitud
            FROM conocimiento
            ORDER BY embedding <=> :embedding::vector
            LIMIT :limite
        """), {"embedding": str(embedding), "limite": limite})
        return [{"titulo": r.titulo, "contenido": r.contenido, "categoria": r.categoria, "similitud": float(r.similitud)} for r in resultado]