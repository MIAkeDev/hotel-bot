from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
from app.bot import chat
from app.config import WHATSAPP_TOKEN, VERIFY_TOKEN, RECEPTIONIST_NUMBER
from app.database import init_db, guardar_conversacion
import httpx
from datetime import datetime
import langdetect

app = FastAPI(title="Hotel Sunrise - Bot")

@app.on_event("startup")
def startup():
    init_db()

class MessageRequest(BaseModel):
    session_id: str
    message: str

class MessageResponse(BaseModel):
    session_id: str
    reply: str

@app.get("/")
def root():
    return {
        "status": "activo",
        "hotel": "Hotel Sunrise",
        "version": "1.0"
    }

@app.post("/chat", response_model=MessageResponse)
def handle_message(request: MessageRequest):
    reply = chat(
        session_id=request.session_id,
        message=request.message
    )
    return MessageResponse(
        session_id=request.session_id,
        reply=reply
    )

@app.get("/webhook")
def verify_webhook(request: Request):
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")
    if mode == "subscribe" and token == VERIFY_TOKEN:
        return PlainTextResponse(content=challenge)
    return PlainTextResponse(content="Token inválido", status_code=403)

async def send_whatsapp(phone_id: str, to: str, message: str):
    url = f"https://graph.facebook.com/v18.0/{phone_id}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "text": {"body": message}
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload, headers=headers)
        print(f"META RESPONSE: {response.status_code}")
        print(f"META BODY: {response.text}")

@app.post("/webhook")
async def receive_message(request: Request):
    data = await request.json()
    print("DATA RECIBIDA:", data)

    try:
        entry = data["entry"][0]
        change = entry["changes"][0]
        value = change["value"]
        message = value["messages"][0]

        phone = message["from"]
        text = message["text"]["body"]
        phone_id = value["metadata"]["phone_number_id"]
        hora = datetime.now().strftime("%I:%M %p")

        try:
            idioma = langdetect.detect(text)
        except:
            idioma = "desconocido"

        print(f"TELEFONO: {phone}")
        print(f"IDIOMA: {idioma}")
        print(f"MENSAJE: {text}")

        reply = chat(session_id=phone, message=text)
        print(f"RESPUESTA BOT: {reply}")

        fue_handoff = "##HANDOFF##" in reply

        if fue_handoff:
            reply_clean = reply.replace("##HANDOFF##", "").strip()
            await send_whatsapp(phone_id, phone, reply_clean)

            notificacion = (
                f"🔔 PEDIDO NUEVO\n"
                f"👤 Huésped: +{phone}\n"
                f"🌐 Idioma: {idioma}\n"
                f"📋 Pedido: {text}\n"
                f"🕐 Hora: {hora}\n"
                f"💬 Respuesta enviada: {reply_clean}"
            )
            await send_whatsapp(phone_id, RECEPTIONIST_NUMBER, notificacion)
        else:
            reply_clean = reply
            await send_whatsapp(phone_id, phone, reply)

        guardar_conversacion(
            telefono=phone,
            idioma=idioma,
            mensaje=text,
            respuesta=reply_clean,
            fue_handoff=fue_handoff
        )

    except Exception as e:
        print(f"ERROR: {e}")

    return {"status": "ok"}