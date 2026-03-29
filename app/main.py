from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
from app.bot import chat
from app.config import WHATSAPP_TOKEN, VERIFY_TOKEN, RECEPTIONIST_NUMBER
from app.database import init_db, guardar_conversacion
import httpx
from datetime import datetime
import langdetect
from app.rag import init_rag, agregar_conocimiento, buscar_conocimiento
from app.admin import router as admin_router

app = FastAPI(title="Hotel Sunrise - Bot")
app.include_router(admin_router)



@app.on_event("startup")
def startup():
    init_db()
    init_rag()

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

        resultados_rag = buscar_conocimiento(text)
        contexto_rag = ""
        if resultados_rag and resultados_rag[0]["similitud"] > 0.3:
            contexto_rag = "\n".join([
                f"- {r['titulo']}: {r['contenido']}"
                for r in resultados_rag
            ])

        reply = chat(session_id=phone, message=text, contexto_rag=contexto_rag)
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
@app.get("/conversaciones")
def ver_conversaciones():
    from app.database import SessionLocal, Conversacion
    db = SessionLocal()
    try:
        conversaciones = db.query(Conversacion).order_by(Conversacion.fecha.desc()).all()
        return [
            {
                "id": c.id,
                "telefono": c.telefono,
                "idioma": c.idioma,
                "mensaje": c.mensaje,
                "respuesta": c.respuesta,
                "fue_handoff": c.fue_handoff,
                "fecha": str(c.fecha)
            }
            for c in conversaciones
        ]
    finally:
        db.close()
@app.get("/dashboard")
def dashboard():
    from app.database import SessionLocal, Conversacion
    from sqlalchemy import func
    db = SessionLocal()
    try:
        total = db.query(Conversacion).count()
        handoffs = db.query(Conversacion).filter(Conversacion.fue_handoff == True).count()
        automaticas = total - handoffs
        idiomas = db.query(Conversacion.idioma, func.count(Conversacion.idioma)).group_by(Conversacion.idioma).all()

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Hotel Sunrise - Dashboard</title>
            <style>
                body {{ font-family: Arial; padding: 30px; background: #f5f5f5; }}
                h1 {{ color: #1a1a2e; }}
                .cards {{ display: flex; gap: 20px; margin: 20px 0; flex-wrap: wrap; }}
                .card {{ background: white; padding: 24px; border-radius: 12px; min-width: 160px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); }}
                .card h2 {{ margin: 0; font-size: 36px; color: #2563eb; }}
                .card p {{ margin: 4px 0 0; color: #666; font-size: 14px; }}
                .card.handoff h2 {{ color: #f59e0b; }}
                .card.auto h2 {{ color: #10b981; }}
                table {{ width: 100%; background: white; border-radius: 12px; border-collapse: collapse; box-shadow: 0 2px 8px rgba(0,0,0,0.08); }}
                th {{ background: #2563eb; color: white; padding: 12px 16px; text-align: left; }}
                td {{ padding: 10px 16px; border-bottom: 1px solid #f0f0f0; font-size: 14px; }}
                tr:last-child td {{ border-bottom: none; }}
                .badge {{ padding: 3px 10px; border-radius: 20px; font-size: 12px; font-weight: bold; }}
                .si {{ background: #fef3c7; color: #d97706; }}
                .no {{ background: #d1fae5; color: #059669; }}
            </style>
        </head>
        <body>
            <h1>🏨 Hotel Sunrise — Dashboard</h1>

            <div class="cards">
                <div class="card">
                    <h2>{total}</h2>
                    <p>Total conversaciones</p>
                </div>
                <div class="card auto">
                    <h2>{automaticas}</h2>
                    <p>Resueltas por el bot</p>
                </div>
                <div class="card handoff">
                    <h2>{handoffs}</h2>
                    <p>Escaladas al recepcionista</p>
                </div>
                <div class="card">
                    <h2>{round((automaticas/total*100) if total > 0 else 0)}%</h2>
                    <p>Tasa de resolución automática</p>
                </div>
            </div>

            <h2>Idiomas detectados</h2>
            <div class="cards">
                {"".join(f'<div class="card"><h2>{c}</h2><p>{i}</p></div>' for i, c in idiomas)}
            </div>

            <h2>Últimas conversaciones</h2>
            <table>
                <tr>
                    <th>Teléfono</th>
                    <th>Idioma</th>
                    <th>Mensaje</th>
                    <th>Respuesta</th>
                    <th>Handoff</th>
                    <th>Fecha</th>
                </tr>
        """

        conversaciones = db.query(Conversacion).order_by(Conversacion.fecha.desc()).limit(20).all()
        for c in conversaciones:
            handoff_badge = '<span class="badge si">Sí</span>' if c.fue_handoff else '<span class="badge no">No</span>'
            html += f"""
                <tr>
                    <td>+{c.telefono}</td>
                    <td>{c.idioma}</td>
                    <td>{c.mensaje[:50]}...</td>
                    <td>{c.respuesta[:60]}...</td>
                    <td>{handoff_badge}</td>
                    <td>{str(c.fecha)[:16]}</td>
                </tr>
            """

        html += """
            </table>
        </body>
        </html>
        """
        return __import__('fastapi').responses.HTMLResponse(content=html)
    finally:
        db.close()
    return {"status": "ok"}
@app.post("/conocimiento")
def agregar_conocimiento_ruta(categoria: str, titulo: str, contenido: str):
    agregar_conocimiento(categoria, titulo, contenido)
    return {"status": "agregado", "titulo": titulo}

@app.get("/conocimiento/buscar")
def buscar_ruta(consulta: str):
    resultados = buscar_conocimiento(consulta)
    return resultados