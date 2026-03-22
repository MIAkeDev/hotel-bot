from sentence_transformers import SentenceTransformer
from sqlalchemy import text
from app.database import engine

model = SentenceTransformer('all-MiniLM-L6-v2')

def init_rag():
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS conocimiento (
                id SERIAL PRIMARY KEY,
                categoria VARCHAR(50),
                titulo VARCHAR(200),
                contenido TEXT,
                embedding vector(384)
            )
        """))
        conn.commit()

def agregar_conocimiento(categoria: str, titulo: str, contenido: str):
    embedding = model.encode(contenido).tolist()
    with engine.connect() as conn:
        conn.execute(text("""
            INSERT INTO conocimiento (categoria, titulo, contenido, embedding)
            VALUES (:categoria, :titulo, :contenido, :embedding)
        """), {
            "categoria": categoria,
            "titulo": titulo,
            "contenido": contenido,
            "embedding": embedding
        })
        conn.commit()

def buscar_conocimiento(consulta: str, limite: int = 3) -> list:
    embedding = model.encode(consulta).tolist()
    with engine.connect() as conn:
        resultado = conn.execute(text("""
            SELECT titulo, contenido, categoria,
            1 - (embedding <=> :embedding::vector) as similitud
            FROM conocimiento
            ORDER BY embedding <=> :embedding::vector
            LIMIT :limite
        """), {"embedding": embedding, "limite": limite})
        return [{"titulo": r.titulo, "contenido": r.contenido, "categoria": r.categoria, "similitud": float(r.similitud)} for r in resultado]