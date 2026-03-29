from groq import Groq
from app.config import GROQ_API_KEY

client = Groq(api_key=GROQ_API_KEY)

SYSTEM_PROMPT = """
Eres el asistente virtual del Hotel Sunrise.
Responde SIEMPRE en el mismo idioma que el huesped.
Tus respuestas deben ser breves, maximo 3 lineas.

CLASIFICACION DE INTENCION:
Si el huesped hace un pedido concreto (room service, toallas, taxi,
lavanderia, mantenimiento, queja, problema en habitacion), confirma
el pedido en su idioma y agrega ##HANDOFF## al FINAL de tu respuesta.
Antes de registrar cualquier pedido, pregunta el numero de habitacion
si no lo ha mencionado. Solo registra el pedido cuando te lo indique.
Si es solo consulta de informacion, responde normalmente sin ##HANDOFF##.
Cuando recibas un mensaje con solo numeros o caracteres especiales,
conserva el ultimo idioma detectado de mensajes anteriores.
Si te preguntan algo fuera del hotel, responde amablemente que solo
puedes ayudar con temas del hotel.
"""


sessions: dict[str, list] = {}
idiomas: dict[str, str] = {}

def chat(session_id: str, message: str, contexto_rag: str = "") -> str:
    if session_id not in sessions:
        sessions[session_id] = []

    prompt_con_contexto = message
    if contexto_rag:
        prompt_con_contexto = f"""El huésped pregunta: {message}

Información relevante encontrada:
{contexto_rag}

Usa esta información para responder."""

    sessions[session_id].append({
        "role": "user",
        "content": prompt_con_contexto
    })

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            *sessions[session_id]
        ]
    )

    reply = response.choices[0].message.content

    sessions[session_id].append({
        "role": "assistant",
        "content": reply
    })

    return reply