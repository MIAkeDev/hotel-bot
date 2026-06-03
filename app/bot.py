from groq import Groq
from app.config import GROQ_API_KEY
from app.database import obtener_mensajes_por_telefono # Importamos tu función existente

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
no mientas con informacion que no sabes, solo responde segun lo que tendas del RAG y recuerda ser muy amable y que se note
un interes de conversacion, eres un experto atendiendo y cerrando reservacion o ventas
"""

def chat(session_id: str, message: str, contexto_rag: str = "") -> str:
    # 1. Recuperar el historial desde Supabase
    historial_db = obtener_mensajes_por_telefono(session_id)
    
    # 2. Construir los mensajes para Groq
    messages_formateados = [{"role": "system", "content": SYSTEM_PROMPT}]
    
    # Tomamos solo los últimos 6 mensajes para no gastar demasiados tokens
    for msg in historial_db[-6:]:
        messages_formateados.append({"role": "user", "content": msg["mensaje"]})
        if msg["respuesta"]:
            messages_formateados.append({"role": "assistant", "content": msg["respuesta"].replace("##HANDOFF##", "")})

    # 3. Preparar el mensaje actual (con RAG si existe)
    prompt_con_contexto = message
    if contexto_rag:
        prompt_con_contexto = f"El huésped pregunta: {message}\n\nInformación relevante encontrada:\n{contexto_rag}\n\nUsa esta información para responder."

    messages_formateados.append({"role": "user", "content": prompt_con_contexto})

    # 4. Llamada a Groq
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages_formateados
    )

    return response.choices[0].message.content