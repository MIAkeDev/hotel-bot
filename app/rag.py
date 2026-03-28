import cohere
from sqlalchemy import text
from app.database import engine
from app.config import COHERE_API_KEY

client = cohere.Client(api_key=COHERE_API_KEY)

def get_embedding(texto: str) -> list:
    response = client.embed(
        texts=[texto],
        model="embed-multilingual-light-v3.0",
        input_type="search_query"
    )
    return response.embeddings[0]

def init_rag():
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS conocimiento (
                id SERIAL PRIMARY KEY,
                categoria VARCHAR(50),
                titulo VARCHAR(200),
                embedding vector(384),
                contenido TEXT
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