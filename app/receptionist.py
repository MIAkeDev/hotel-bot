from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from app.database import obtener_chats, obtener_mensajes_por_telefono

router = APIRouter()

@router.get("/recepcionista", response_class=HTMLResponse)
def panel_recepcionista():
    html = """
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Panel Recepcionista — Hotel Sunrise</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }

            body {
                font-family: 'Segoe UI', system-ui, sans-serif;
                background: #0f172a;
                color: #e2e8f0;
                height: 100vh;
                display: flex;
                flex-direction: column;
                overflow: hidden;
            }

            .topbar {
                background: #1e293b;
                padding: 14px 24px;
                display: flex;
                align-items: center;
                gap: 12px;
                border-bottom: 1px solid #334155;
                flex-shrink: 0;
            }

            .topbar-logo { font-size: 24px; }

            .topbar-info { flex: 1; }

            .topbar-title {
                font-size: 16px;
                font-weight: 700;
                color: #f1f5f9;
            }

            .topbar-sub {
                font-size: 12px;
                color: #64748b;
            }

            .topbar-status {
                display: flex;
                align-items: center;
                gap: 6px;
                font-size: 12px;
                color: #10b981;
                font-weight: 600;
            }

            .status-dot {
                width: 8px;
                height: 8px;
                border-radius: 50%;
                background: #10b981;
                animation: pulse 2s infinite;
            }

            @keyframes pulse {
                0%, 100% { opacity: 1; }
                50% { opacity: 0.4; }
            }

            .main {
                display: flex;
                flex: 1;
                overflow: hidden;
            }

            /* Lista de chats */
            .chat-list {
                width: 320px;
                background: #1e293b;
                border-right: 1px solid #334155;
                display: flex;
                flex-direction: column;
                flex-shrink: 0;
            }

            .chat-list-header {
                padding: 16px;
                border-bottom: 1px solid #334155;
                display: flex;
                align-items: center;
                justify-content: space-between;
            }

            .chat-list-title {
                font-size: 14px;
                font-weight: 600;
                color: #94a3b8;
                text-transform: uppercase;
                letter-spacing: 1px;
            }

            .chat-list-count {
                background: #1d4ed8;
                color: white;
                padding: 2px 8px;
                border-radius: 12px;
                font-size: 11px;
                font-weight: 700;
            }

            .chat-list-body {
                overflow-y: auto;
                flex: 1;
            }

            .chat-item {
                padding: 14px 16px;
                border-bottom: 1px solid #0f172a;
                cursor: pointer;
                transition: all 0.2s;
                display: flex;
                align-items: center;
                gap: 12px;
            }

            .chat-item:hover {
                background: #2d3f55;
            }

            .chat-item.active {
                background: #1d3a5f;
                border-left: 3px solid #3b82f6;
            }

            .chat-avatar {
                width: 44px;
                height: 44px;
                border-radius: 50%;
                background: linear-gradient(135deg, #1d4ed8, #7c3aed);
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 18px;
                flex-shrink: 0;
            }

            .chat-info { flex: 1; min-width: 0; }

            .chat-phone {
                font-size: 14px;
                font-weight: 600;
                color: #f1f5f9;
                margin-bottom: 4px;
            }

            .chat-preview {
                font-size: 12px;
                color: #64748b;
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
            }

            .chat-meta {
                display: flex;
                flex-direction: column;
                align-items: flex-end;
                gap: 4px;
                flex-shrink: 0;
            }

            .chat-time {
                font-size: 11px;
                color: #475569;
            }

            .chat-badge {
                background: #3b82f6;
                color: white;
                width: 18px;
                height: 18px;
                border-radius: 50%;
                font-size: 10px;
                display: flex;
                align-items: center;
                justify-content: center;
                font-weight: 700;
            }

            .handoff-badge {
                background: #f59e0b;
                color: #1a1a1a;
                padding: 2px 6px;
                border-radius: 6px;
                font-size: 9px;
                font-weight: 700;
            }

            /* Panel de conversación */
            .chat-panel {
                flex: 1;
                display: flex;
                flex-direction: column;
                overflow: hidden;
            }

            .chat-header {
                padding: 14px 24px;
                background: #1e293b;
                border-bottom: 1px solid #334155;
                display: flex;
                align-items: center;
                gap: 12px;
                flex-shrink: 0;
            }

            .chat-header-avatar {
                width: 40px;
                height: 40px;
                border-radius: 50%;
                background: linear-gradient(135deg, #1d4ed8, #7c3aed);
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 18px;
            }

            .chat-header-info { flex: 1; }

            .chat-header-phone {
                font-size: 15px;
                font-weight: 700;
                color: #f1f5f9;
            }

            .chat-header-sub {
                font-size: 12px;
                color: #64748b;
            }

            .chat-header-actions {
                display: flex;
                gap: 8px;
            }

            .btn-action {
                background: #334155;
                border: none;
                color: #94a3b8;
                padding: 8px 14px;
                border-radius: 8px;
                font-size: 12px;
                cursor: pointer;
                transition: all 0.2s;
                font-weight: 500;
            }

            .btn-action:hover {
                background: #3b82f6;
                color: white;
            }

            /* Mensajes */
            .messages-container {
                flex: 1;
                overflow-y: auto;
                padding: 24px;
                display: flex;
                flex-direction: column;
                gap: 16px;
                background: #0f172a;
            }

            .message-group {
                display: flex;
                flex-direction: column;
                gap: 8px;
            }

            .message-date {
                text-align: center;
                font-size: 11px;
                color: #475569;
                margin: 8px 0;
            }

            .bubble-row {
                display: flex;
                gap: 8px;
                align-items: flex-end;
            }

            .bubble-row.huesped { justify-content: flex-start; }
            .bubble-row.bot { justify-content: flex-end; }

            .bubble {
                max-width: 65%;
                padding: 10px 14px;
                border-radius: 16px;
                font-size: 14px;
                line-height: 1.5;
                position: relative;
            }

            .bubble.huesped {
                background: #1e293b;
                border: 1px solid #334155;
                border-bottom-left-radius: 4px;
                color: #e2e8f0;
            }

            .bubble.bot {
                background: #1d4ed8;
                border-bottom-right-radius: 4px;
                color: white;
            }

            .bubble.handoff {
                background: #92400e;
                border: 1px solid #f59e0b44;
            }

            .bubble-time {
                font-size: 10px;
                opacity: 0.6;
                margin-top: 4px;
                text-align: right;
            }

            .bubble-label {
                font-size: 10px;
                color: #64748b;
                margin-bottom: 4px;
                font-weight: 600;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }

            .handoff-tag {
                display: inline-block;
                background: #f59e0b22;
                border: 1px solid #f59e0b66;
                color: #fbbf24;
                padding: 2px 8px;
                border-radius: 6px;
                font-size: 10px;
                font-weight: 700;
                margin-top: 4px;
            }

            .idioma-tag {
                display: inline-block;
                background: #1d4ed822;
                border: 1px solid #3b82f644;
                color: #60a5fa;
                padding: 2px 8px;
                border-radius: 6px;
                font-size: 10px;
                font-weight: 600;
                margin-left: 6px;
            }

            /* Input de mensaje */
            .message-input-area {
                padding: 16px 24px;
                background: #1e293b;
                border-top: 1px solid #334155;
                display: flex;
                gap: 12px;
                align-items: center;
                flex-shrink: 0;
            }

            .message-input {
                flex: 1;
                background: #0f172a;
                border: 1px solid #334155;
                border-radius: 24px;
                padding: 10px 18px;
                color: #e2e8f0;
                font-size: 14px;
                font-family: inherit;
                outline: none;
                transition: border 0.2s;
            }

            .message-input:focus {
                border-color: #3b82f6;
            }

            .btn-send {
                background: #1d4ed8;
                border: none;
                color: white;
                width: 42px;
                height: 42px;
                border-radius: 50%;
                font-size: 18px;
                cursor: pointer;
                transition: all 0.2s;
                display: flex;
                align-items: center;
                justify-content: center;
            }

            .btn-send:hover {
                background: #2563eb;
                transform: scale(1.05);
            }

            /* Empty state */
            .empty-chat {
                flex: 1;
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                color: #475569;
                gap: 12px;
            }

            .empty-icon { font-size: 64px; }
            .empty-text { font-size: 16px; font-weight: 600; }
            .empty-sub { font-size: 13px; }

            /* Scrollbar */
            ::-webkit-scrollbar { width: 6px; }
            ::-webkit-scrollbar-track { background: transparent; }
            ::-webkit-scrollbar-thumb { background: #334155; border-radius: 10px; }

            @media (max-width: 600px) {
                .chat-list { width: 100%; display: none; }
                .chat-list.show { display: flex; }
            }
        </style>
    </head>
    <body>

    <div class="topbar">
        <div class="topbar-logo">🏨</div>
        <div class="topbar-info">
            <div class="topbar-title">Hotel Sunrise — Panel Recepcionista</div>
            <div class="topbar-sub">Conversaciones en tiempo real</div>
        </div>
        <div class="topbar-status">
            <div class="status-dot"></div>
            Bot activo
        </div>
    </div>

    <div class="main">
        <div class="chat-list" id="chatList">
            <div class="chat-list-header">
                <span class="chat-list-title">Conversaciones</span>
                <span class="chat-list-count" id="totalChats">0</span>
            </div>
            <div class="chat-list-body" id="chatListBody">
                <div style="padding:20px;text-align:center;color:#475569;font-size:13px;">Cargando...</div>
            </div>
        </div>

        <div class="chat-panel" id="chatPanel">
            <div class="empty-chat" id="emptyChat">
                <div class="empty-icon">💬</div>
                <div class="empty-text">Selecciona una conversación</div>
                <div class="empty-sub">Elige un huésped de la lista para ver su historial</div>
            </div>

            <div id="activeChat" style="display:none;flex-direction:column;flex:1;overflow:hidden;">
                <div class="chat-header">
                    <div class="chat-header-avatar">👤</div>
                    <div class="chat-header-info">
                        <div class="chat-header-phone" id="activePhone">—</div>
                        <div class="chat-header-sub" id="activeSub">—</div>
                    </div>
                    <div class="chat-header-actions">
                        <button class="btn-action" id="btnModo" onclick="toggleModo()">🤖 Tomar control</button>
                        <button class="btn-action" onclick="recargarChat()">🔄 Actualizar</button>
                    </div>
                </div>

                <div class="messages-container" id="messagesContainer"></div>

                <div class="message-input-area">
                    <input type="text" class="message-input" id="msgInput" placeholder="Escribe un mensaje como recepcionista..." onkeypress="if(event.key==='Enter') enviarMensaje()">
                    <button class="btn-send" onclick="enviarMensaje()">➤</button>
                </div>
            </div>
        </div>
    </div>

    <script>
        let currentPhone = null;
        let autoRefresh = null;

        async function cargarChats() {
            const res = await fetch('/api/chats');
            const chats = await res.json();
            document.getElementById('totalChats').textContent = chats.length;

            const body = document.getElementById('chatListBody');
            if (chats.length === 0) {
                body.innerHTML = '<div style="padding:20px;text-align:center;color:#475569;font-size:13px;">No hay conversaciones aún</div>';
                return;
            }

            body.innerHTML = chats.map(chat => {
                const hora = new Date(chat.ultima_fecha).toLocaleTimeString('es-PE', {hour:'2-digit', minute:'2-digit'});
                const isActive = chat.telefono === currentPhone ? 'active' : '';
                return `
                    <div class="chat-item ${isActive}" onclick="abrirChat('${chat.telefono}', ${chat.total_mensajes})">
                        <div class="chat-avatar">👤</div>
                        <div class="chat-info">
                            <div class="chat-phone">+${chat.telefono}</div>
                            <div class="chat-preview">${chat.total_mensajes} mensaje${chat.total_mensajes !== 1 ? 's' : ''}</div>
                        </div>
                        <div class="chat-meta">
                            <div class="chat-time">${hora}</div>
                            <div class="chat-badge">${chat.total_mensajes}</div>
                        </div>
                    </div>
                `;
            }).join('');
        }

        async function abrirChat(telefono, total) {
            currentPhone = telefono;
            document.getElementById('emptyChat').style.display = 'none';
            document.getElementById('activeChat').style.display = 'flex';
            document.getElementById('activePhone').textContent = '+' + telefono;
            document.getElementById('activeSub').textContent = total + ' mensajes en total';

            await cargarMensajes(telefono);
            await cargarChats();

            if (autoRefresh) clearInterval(autoRefresh);
            autoRefresh = setInterval(() => cargarMensajes(telefono), 10000);
            modoManual = false;
            actualizarBotonModo();
        }
    let modoManual = false;

    function actualizarBotonModo() {
        const btn = document.getElementById('btnModo');
        if (modoManual) {
            btn.innerHTML = '🟢 Devolver al bot';
            btn.style.background = '#f59e0b';
            btn.style.color = '#1a1a1a';
        } else {
            btn.innerHTML = '🤖 Tomar control';
            btn.style.background = '';
            btn.style.color = '';
        }
    }

    async function toggleModo() {
        if (!currentPhone) return;
        if (modoManual) {
            await fetch('/api/modo-manual/' + currentPhone, { method: 'DELETE' });
            modoManual = false;
        } else {
            await fetch('/api/modo-manual/' + currentPhone, { method: 'POST' });
            modoManual = true;
        }
        actualizarBotonModo();
}
        async function cargarMensajes(telefono) {
            const res = await fetch('/api/mensajes/' + telefono);
            const mensajes = await res.json();

            const container = document.getElementById('messagesContainer');
            container.innerHTML = mensajes.map(m => {
                const hora = new Date(m.fecha).toLocaleTimeString('es-PE', {hour:'2-digit', minute:'2-digit'});
                const idiomaTag = m.idioma && m.idioma !== 'desconocido' ? `<span class="idioma-tag">${m.idioma}</span>` : '';
                const handoffTag = m.fue_handoff ? '<div class="handoff-tag">🔔 Escalado al recepcionista</div>' : '';

                return `
                    <div class="message-group">
                        <div class="bubble-label">Huésped ${idiomaTag}</div>
                        <div class="bubble-row huesped">
                            <div class="bubble huesped">
                                ${m.mensaje}
                                <div class="bubble-time">${hora}</div>
                            </div>
                        </div>
                        <div class="bubble-label" style="text-align:right">Bot 🤖</div>
                        <div class="bubble-row bot">
                            <div class="bubble bot ${m.fue_handoff ? 'handoff' : ''}">
                                ${m.respuesta}
                                ${handoffTag}
                                <div class="bubble-time">${hora}</div>
                            </div>
                        </div>
                    </div>
                `;
            }).join('');

            container.scrollTop = container.scrollHeight;
        }

        async function recargarChat() {
            if (currentPhone) await cargarMensajes(currentPhone);
        }

        async function enviarMensaje() {
            const input = document.getElementById('msgInput');
            const texto = input.value.trim();
            if (!texto || !currentPhone) return;

            input.value = '';
            const res = await fetch('/api/enviar', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({telefono: currentPhone, mensaje: texto})
            });

            if (res.ok) {
                await cargarMensajes(currentPhone);
            } else {
                alert('Error al enviar el mensaje');
            }
        }

        cargarChats();
        setInterval(cargarChats, 15000);
    </script>

    </body>
    </html>
    """
    return html

@router.get("/api/chats")
def api_chats():
    from app.database import obtener_chats
    return obtener_chats()

@router.get("/api/mensajes/{telefono}")
def api_mensajes(telefono: str):
    from app.database import obtener_mensajes_por_telefono
    return obtener_mensajes_por_telefono(telefono)

@router.post("/api/modo-manual/{telefono}")
def activar_manual(telefono: str):
    from app.database import activar_modo_manual
    activar_modo_manual(telefono)
    return {"status": "manual", "telefono": telefono}

@router.delete("/api/modo-manual/{telefono}")
def desactivar_manual(telefono: str):
    from app.database import desactivar_modo_manual
    desactivar_modo_manual(telefono)
    return {"status": "bot", "telefono": telefono}

@router.post("/api/enviar")
async def api_enviar(data: dict):
    import httpx
    from app.config import WHATSAPP_TOKEN
    phone_id = "1089612837558156"
    url = f"https://graph.facebook.com/v18.0/{phone_id}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": data["telefono"],
        "text": {"body": data["mensaje"]}
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload, headers=headers)
    return {"status": "ok", "code": response.status_code}