from fastapi import APIRouter, UploadFile, File
from fastapi.responses import HTMLResponse
from app.rag import agregar_conocimiento, buscar_conocimiento
from sqlalchemy import text
from app.database import engine
import io

router = APIRouter()

@router.get("/admin", response_class=HTMLResponse)
def panel_admin():
    with engine.connect() as conn:
        items = conn.execute(text("""
            SELECT id, categoria, titulo, contenido 
            FROM conocimiento 
            ORDER BY categoria, id DESC
        """)).fetchall()

    categorias = {}
    for item in items:
        cat = item.categoria
        if cat not in categorias:
            categorias[cat] = []
        categorias[cat].append(item)

    items_html = ""
    iconos = {
        "carta": "🍽️",
        "habitaciones": "🛏️",
        "eventos": "🎉",
        "espacios": "🏛️",
        "informacion": "ℹ️",
        "tarifas": "💰"
    }

    for cat, lista in categorias.items():
        icono = iconos.get(cat, "📁")
        items_html += f"""
        <div class="categoria-section">
            <div class="categoria-header">
                <span class="cat-icon">{icono}</span>
                <span class="cat-nombre">{cat.upper()}</span>
                <span class="cat-count">{len(lista)} items</span>
            </div>
            <div class="items-grid">
        """
        for item in lista:
            contenido_corto = item.contenido[:120] + "..." if len(item.contenido) > 120 else item.contenido
            items_html += f"""
                <div class="item-card">
                    <div class="item-titulo">{item.titulo}</div>
                    <div class="item-contenido">{contenido_corto}</div>
                    <button class="btn-eliminar" onclick="eliminar({item.id})">✕ Eliminar</button>
                </div>
            """
        items_html += "</div></div>"

    if not items_html:
        items_html = """
        <div class="empty-state">
            <div class="empty-icon">📭</div>
            <p>No hay información cargada aún.</p>
            <p>Agrega contenido usando el formulario.</p>
        </div>
        """

    html = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Panel Admin — Hotel Sunrise</title>
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            
            body {{
                font-family: 'Segoe UI', sans-serif;
                background: #0f172a;
                color: #e2e8f0;
                min-height: 100vh;
            }}

            .topbar {{
                background: linear-gradient(135deg, #1e3a5f, #0f172a);
                padding: 20px 40px;
                display: flex;
                align-items: center;
                gap: 16px;
                border-bottom: 1px solid #1e40af33;
            }}

            .topbar-logo {{
                font-size: 28px;
            }}

            .topbar-title {{
                font-size: 22px;
                font-weight: 700;
                color: #f8fafc;
            }}

            .topbar-sub {{
                font-size: 13px;
                color: #94a3b8;
                margin-top: 2px;
            }}

            .topbar-badge {{
                margin-left: auto;
                background: #1d4ed8;
                color: #bfdbfe;
                padding: 6px 14px;
                border-radius: 20px;
                font-size: 12px;
                font-weight: 600;
            }}

            .container {{
                max-width: 1200px;
                margin: 0 auto;
                padding: 40px 20px;
                display: grid;
                grid-template-columns: 400px 1fr;
                gap: 32px;
                align-items: start;
            }}

            .panel-form {{
                background: #1e293b;
                border-radius: 16px;
                padding: 28px;
                border: 1px solid #334155;
                position: sticky;
                top: 20px;
            }}

            .panel-form h2 {{
                font-size: 16px;
                font-weight: 600;
                color: #f1f5f9;
                margin-bottom: 20px;
                display: flex;
                align-items: center;
                gap: 8px;
            }}

            .tab-group {{
                display: flex;
                gap: 8px;
                margin-bottom: 20px;
                flex-wrap: wrap;
            }}

            .tab {{
                padding: 7px 14px;
                border-radius: 8px;
                border: 1px solid #334155;
                background: transparent;
                color: #94a3b8;
                font-size: 12px;
                cursor: pointer;
                transition: all 0.2s;
                font-weight: 500;
            }}

            .tab:hover {{ background: #334155; color: #e2e8f0; }}

            .tab.active {{
                background: #1d4ed8;
                border-color: #1d4ed8;
                color: #fff;
            }}

            .form-group {{
                margin-bottom: 16px;
            }}

            label {{
                display: block;
                font-size: 12px;
                color: #94a3b8;
                margin-bottom: 6px;
                font-weight: 500;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }}

            input, textarea, select {{
                width: 100%;
                background: #0f172a;
                border: 1px solid #334155;
                border-radius: 8px;
                padding: 10px 14px;
                color: #e2e8f0;
                font-size: 14px;
                font-family: inherit;
                transition: border 0.2s;
                outline: none;
            }}

            input:focus, textarea:focus, select:focus {{
                border-color: #3b82f6;
            }}

            textarea {{
                resize: vertical;
                min-height: 120px;
            }}

            .btn-guardar {{
                width: 100%;
                background: linear-gradient(135deg, #1d4ed8, #2563eb);
                color: white;
                border: none;
                border-radius: 10px;
                padding: 12px;
                font-size: 15px;
                font-weight: 600;
                cursor: pointer;
                transition: opacity 0.2s;
                margin-top: 4px;
            }}

            .btn-guardar:hover {{ opacity: 0.9; }}

            .divider {{
                border: none;
                border-top: 1px solid #334155;
                margin: 20px 0;
            }}

            .upload-area {{
                border: 2px dashed #334155;
                border-radius: 10px;
                padding: 24px;
                text-align: center;
                cursor: pointer;
                transition: all 0.2s;
            }}

            .upload-area:hover {{
                border-color: #3b82f6;
                background: #1e293b;
            }}

            .upload-icon {{ font-size: 32px; margin-bottom: 8px; }}
            .upload-text {{ font-size: 13px; color: #64748b; }}

            .panel-data {{ }}

            .panel-data h2 {{
                font-size: 16px;
                font-weight: 600;
                color: #f1f5f9;
                margin-bottom: 20px;
                display: flex;
                align-items: center;
                gap: 8px;
            }}

            .categoria-section {{
                margin-bottom: 24px;
            }}

            .categoria-header {{
                display: flex;
                align-items: center;
                gap: 10px;
                margin-bottom: 12px;
                padding-bottom: 8px;
                border-bottom: 1px solid #1e40af44;
            }}

            .cat-icon {{ font-size: 18px; }}

            .cat-nombre {{
                font-size: 13px;
                font-weight: 700;
                color: #93c5fd;
                letter-spacing: 1px;
            }}

            .cat-count {{
                margin-left: auto;
                background: #1e3a5f;
                color: #93c5fd;
                padding: 2px 10px;
                border-radius: 12px;
                font-size: 11px;
                font-weight: 600;
            }}

            .items-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
                gap: 12px;
            }}

            .item-card {{
                background: #1e293b;
                border: 1px solid #334155;
                border-radius: 12px;
                padding: 16px;
                transition: border-color 0.2s;
            }}

            .item-card:hover {{ border-color: #3b82f6; }}

            .item-titulo {{
                font-size: 14px;
                font-weight: 600;
                color: #f1f5f9;
                margin-bottom: 6px;
            }}

            .item-contenido {{
                font-size: 12px;
                color: #64748b;
                line-height: 1.5;
                margin-bottom: 12px;
            }}

            .btn-eliminar {{
                background: transparent;
                border: 1px solid #ef444433;
                color: #f87171;
                padding: 5px 12px;
                border-radius: 6px;
                font-size: 11px;
                cursor: pointer;
                transition: all 0.2s;
            }}

            .btn-eliminar:hover {{
                background: #ef444422;
                border-color: #ef4444;
            }}

            .empty-state {{
                text-align: center;
                padding: 60px 20px;
                color: #475569;
            }}

            .empty-icon {{ font-size: 48px; margin-bottom: 12px; }}

            .toast {{
                position: fixed;
                bottom: 30px;
                right: 30px;
                background: #1d4ed8;
                color: white;
                padding: 14px 24px;
                border-radius: 10px;
                font-size: 14px;
                font-weight: 500;
                display: none;
                z-index: 999;
                box-shadow: 0 4px 20px rgba(0,0,0,0.3);
            }}

            .toast.error {{ background: #dc2626; }}
            .toast.show {{ display: block; animation: slideIn 0.3s ease; }}

            @keyframes slideIn {{
                from {{ transform: translateY(20px); opacity: 0; }}
                to {{ transform: translateY(0); opacity: 1; }}
            }}

            @media (max-width: 800px) {{
                .container {{ grid-template-columns: 1fr; }}
                .panel-form {{ position: static; }}
            }}
        </style>
    </head>
    <body>

    <div class="topbar">
        <div class="topbar-logo">🏨</div>
        <div>
            <div class="topbar-title">Hotel Sunrise</div>
            <div class="topbar-sub">Panel de administración — Base de conocimiento</div>
        </div>
        <div class="topbar-badge">⚡ RAG Activo</div>
    </div>

    <div class="container">

        <div class="panel-form">
            <h2>➕ Agregar información</h2>

            <div class="tab-group">
                <button class="tab active" onclick="setCategoria('carta', this)">🍽️ Carta</button>
                <button class="tab" onclick="setCategoria('habitaciones', this)">🛏️ Habitaciones</button>
                <button class="tab" onclick="setCategoria('eventos', this)">🎉 Eventos</button>
                <button class="tab" onclick="setCategoria('espacios', this)">🏛️ Espacios</button>
                <button class="tab" onclick="setCategoria('tarifas', this)">💰 Tarifas</button>
                <button class="tab" onclick="setCategoria('informacion', this)">ℹ️ Info</button>
            </div>

            <input type="hidden" id="categoria" value="carta">

            <div class="form-group">
                <label>Título</label>
                <input type="text" id="titulo" placeholder="Ej: Ceviche clásico">
            </div>

            <div class="form-group">
                <label>Descripción completa</label>
                <textarea id="contenido" placeholder="Ingredientes, precio, características, restricciones, recomendaciones..."></textarea>
            </div>

            <button class="btn-guardar" onclick="guardar()">💾 Guardar en base de conocimiento</button>

            <hr class="divider">

            <div class="upload-area" onclick="document.getElementById('fileInput').click()">
                <div class="upload-icon">📄</div>
                <div class="upload-text">Subir archivo PDF o TXT<br><small>Haz clic para seleccionar</small></div>
                <input type="file" id="fileInput" accept=".txt,.pdf" style="display:none" onchange="subirArchivo(this)">
            </div>
        </div>

        <div class="panel-data">
            <h2>📚 Base de conocimiento del hotel</h2>
            {items_html}
        </div>

    </div>

    <div class="toast" id="toast"></div>

    <script>
        function setCategoria(cat, btn) {{
            document.getElementById('categoria').value = cat;
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            btn.classList.add('active');
        }}

        function showToast(msg, error=false) {{
            const t = document.getElementById('toast');
            t.textContent = msg;
            t.className = 'toast show' + (error ? ' error' : '');
            setTimeout(() => t.className = 'toast', 3000);
        }}

        async function guardar() {{
            const categoria = document.getElementById('categoria').value;
            const titulo = document.getElementById('titulo').value.trim();
            const contenido = document.getElementById('contenido').value.trim();

            if (!titulo || !contenido) {{
                showToast('Completa todos los campos', true);
                return;
            }}

            const params = new URLSearchParams({{ categoria, titulo, contenido }});
            const res = await fetch('/conocimiento?' + params, {{ method: 'POST' }});

            if (res.ok) {{
                showToast('✅ Guardado correctamente');
                document.getElementById('titulo').value = '';
                document.getElementById('contenido').value = '';
                setTimeout(() => location.reload(), 1500);
            }} else {{
                showToast('❌ Error al guardar', true);
            }}
        }}

        async function eliminar(id) {{
            if (!confirm('¿Eliminar este item?')) return;
            const res = await fetch('/conocimiento/' + id, {{ method: 'DELETE' }});
            if (res.ok) {{
                showToast('🗑️ Eliminado');
                setTimeout(() => location.reload(), 1000);
            }}
        }}

        async function subirArchivo(input) {{
            const file = input.files[0];
            if (!file) return;
            const formData = new FormData();
            formData.append('file', file);
            const categoria = document.getElementById('categoria').value;
            showToast('⏳ Procesando archivo...');
            const res = await fetch('/conocimiento/upload?categoria=' + categoria, {{
                method: 'POST',
                body: formData
            }});
            if (res.ok) {{
                const data = await res.json();
                showToast('✅ ' + data.chunks + ' secciones cargadas');
                setTimeout(() => location.reload(), 1500);
            }} else {{
                showToast('❌ Error al procesar', true);
            }}
        }}
    </script>

    </body>
    </html>
    """
    return html

@router.delete("/conocimiento/{{item_id}}")
def eliminar_conocimiento(item_id: int):
    with engine.connect() as conn:
        conn.execute(text("DELETE FROM conocimiento WHERE id = :id"), {{"id": item_id}})
        conn.commit()
    return {{"status": "eliminado"}}

@router.post("/conocimiento/upload")
async def subir_archivo(file: UploadFile = File(...), categoria: str = "informacion"):
    contenido = await file.read()

    if file.filename.endswith('.pdf'):
        import pypdf
        reader = pypdf.PdfReader(io.BytesIO(contenido))
        texto = " ".join(page.extract_text() for page in reader.pages)
    else:
        texto = contenido.decode('utf-8')

    chunks = [texto[i:i+500] for i in range(0, len(texto), 500)]
    
    for i, chunk in enumerate(chunks):
        if chunk.strip():
            agregar_conocimiento(
                categoria=categoria,
                titulo=f"{file.filename} - parte {i+1}",
                contenido=chunk
            )

    return {{"status": "ok", "chunks": len(chunks)}}