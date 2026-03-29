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

    colores_categoria = {
        "carta": "#ff6b35",
        "habitaciones": "#4ecdc4",
        "eventos": "#ffd166",
        "espacios": "#9d4edd",
        "informacion": "#06d6a0",
        "tarifas": "#ff006e"
    }

    for cat, lista in categorias.items():
        color = colores_categoria.get(cat, "#64748b")
        icono = iconos.get(cat, "📁")
        items_html += f"""
        <div class="categoria-section" data-categoria="{cat}">
            <div class="categoria-header" style="border-left-color: {color};">
                <span class="cat-icon">{icono}</span>
                <span class="cat-nombre">{cat.upper()}</span>
                <span class="cat-count">{len(lista)} items</span>
                <button class="btn-toggle" onclick="toggleCategoria(this)">▼</button>
            </div>
            <div class="items-grid">
        """
        for item in lista:
            contenido_corto = item.contenido[:100] + "..." if len(item.contenido) > 100 else item.contenido
            items_html += f"""
                <div class="item-card" data-id="{item.id}">
                    <div class="item-titulo">{item.titulo}</div>
                    <div class="item-contenido">{contenido_corto}</div>
                    <div class="item-actions">
                        <button class="btn-ver" onclick="verContenido({item.id}, '{item.titulo}', `{item.contenido.replace('`', '\\`').replace("'", "\\'")}`)">👁️ Ver</button>
                        <button class="btn-eliminar" onclick="eliminar({item.id})">🗑️ Eliminar</button>
                    </div>
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
                font-family: 'Segoe UI', 'Inter', system-ui, -apple-system, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: #e2e8f0;
                min-height: 100vh;
            }}

            /* Animaciones */
            @keyframes fadeIn {{
                from {{ opacity: 0; transform: translateY(20px); }}
                to {{ opacity: 1; transform: translateY(0); }}
            }}

            @keyframes slideIn {{
                from {{ transform: translateX(100%); opacity: 0; }}
                to {{ transform: translateX(0); opacity: 1; }}
            }}

            @keyframes pulse {{
                0%, 100% {{ transform: scale(1); }}
                50% {{ transform: scale(1.05); }}
            }}

            @keyframes spin {{
                to {{ transform: rotate(360deg); }}
            }}

            /* Topbar mejorado */
            .topbar {{
                background: rgba(15, 23, 42, 0.95);
                backdrop-filter: blur(10px);
                padding: 20px 40px;
                display: flex;
                align-items: center;
                gap: 16px;
                border-bottom: 1px solid rgba(255,255,255,0.1);
                position: sticky;
                top: 0;
                z-index: 100;
            }}

            .topbar-logo {{
                font-size: 32px;
                animation: pulse 2s infinite;
            }}

            .topbar-title {{
                font-size: 24px;
                font-weight: 700;
                background: linear-gradient(135deg, #fff, #a5f3fc);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
            }}

            .topbar-sub {{
                font-size: 13px;
                color: #94a3b8;
                margin-top: 2px;
            }}

            .topbar-badge {{
                margin-left: auto;
                background: linear-gradient(135deg, #1d4ed8, #2563eb);
                color: #bfdbfe;
                padding: 6px 14px;
                border-radius: 20px;
                font-size: 12px;
                font-weight: 600;
                animation: pulse 2s infinite;
            }}

            /* Container mejorado */
            .container {{
                max-width: 1400px;
                margin: 0 auto;
                padding: 40px 20px;
                display: grid;
                grid-template-columns: 380px 1fr;
                gap: 32px;
                align-items: start;
                animation: fadeIn 0.6s ease-out;
            }}

            /* Formulario mejorado */
            .panel-form {{
                background: rgba(30, 41, 59, 0.95);
                backdrop-filter: blur(10px);
                border-radius: 24px;
                padding: 28px;
                border: 1px solid rgba(255,255,255,0.1);
                position: sticky;
                top: 100px;
                transition: transform 0.3s, box-shadow 0.3s;
            }}

            .panel-form:hover {{
                transform: translateY(-5px);
                box-shadow: 0 20px 40px rgba(0,0,0,0.3);
            }}

            .panel-form h2 {{
                font-size: 18px;
                font-weight: 600;
                margin-bottom: 24px;
                display: flex;
                align-items: center;
                gap: 8px;
            }}

            /* Tabs mejorados */
            .tab-group {{
                display: flex;
                gap: 8px;
                margin-bottom: 24px;
                flex-wrap: wrap;
            }}

            .tab {{
                padding: 8px 16px;
                border-radius: 12px;
                border: none;
                background: rgba(15, 23, 42, 0.6);
                color: #94a3b8;
                font-size: 13px;
                cursor: pointer;
                transition: all 0.3s;
                font-weight: 500;
                position: relative;
                overflow: hidden;
            }}

            .tab::before {{
                content: '';
                position: absolute;
                top: 50%;
                left: 50%;
                width: 0;
                height: 0;
                border-radius: 50%;
                background: rgba(255,255,255,0.1);
                transform: translate(-50%, -50%);
                transition: width 0.6s, height 0.6s;
            }}

            .tab:hover::before {{
                width: 300px;
                height: 300px;
            }}

            .tab:hover {{
                background: rgba(51, 65, 85, 0.8);
                color: #e2e8f0;
                transform: translateY(-2px);
            }}

            .tab.active {{
                background: linear-gradient(135deg, #1d4ed8, #2563eb);
                color: #fff;
                box-shadow: 0 4px 15px rgba(29, 78, 216, 0.3);
            }}

            /* Form inputs mejorados */
            .form-group {{
                margin-bottom: 20px;
            }}

            label {{
                display: block;
                font-size: 12px;
                color: #94a3b8;
                margin-bottom: 8px;
                font-weight: 600;
                text-transform: uppercase;
                letter-spacing: 1px;
            }}

            input, textarea, select {{
                width: 100%;
                background: rgba(15, 23, 42, 0.8);
                border: 2px solid rgba(51, 65, 85, 0.6);
                border-radius: 12px;
                padding: 12px 16px;
                color: #e2e8f0;
                font-size: 14px;
                font-family: inherit;
                transition: all 0.3s;
                outline: none;
            }}

            input:focus, textarea:focus, select:focus {{
                border-color: #3b82f6;
                box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
                transform: translateY(-2px);
            }}

            textarea {{
                resize: vertical;
                min-height: 120px;
            }}

            /* Botón guardar mejorado */
            .btn-guardar {{
                width: 100%;
                background: linear-gradient(135deg, #1d4ed8, #2563eb);
                color: white;
                border: none;
                border-radius: 12px;
                padding: 14px;
                font-size: 15px;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.3s;
                margin-top: 8px;
                position: relative;
                overflow: hidden;
            }}

            .btn-guardar::before {{
                content: '';
                position: absolute;
                top: 0;
                left: -100%;
                width: 100%;
                height: 100%;
                background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
                transition: left 0.5s;
            }}

            .btn-guardar:hover::before {{
                left: 100%;
            }}

            .btn-guardar:hover {{
                transform: translateY(-2px);
                box-shadow: 0 10px 20px rgba(29, 78, 216, 0.3);
            }}

            /* Upload area mejorado */
            .upload-area {{
                border: 2px dashed rgba(51, 65, 85, 0.6);
                border-radius: 16px;
                padding: 24px;
                text-align: center;
                cursor: pointer;
                transition: all 0.3s;
                background: rgba(15, 23, 42, 0.4);
            }}

            .upload-area:hover {{
                border-color: #3b82f6;
                background: rgba(59, 130, 246, 0.1);
                transform: translateY(-2px);
            }}

            .upload-icon {{ font-size: 48px; margin-bottom: 12px; transition: transform 0.3s; }}
            .upload-area:hover .upload-icon {{ transform: scale(1.1); }}
            .upload-text {{ font-size: 13px; color: #64748b; }}

            /* Categorías mejoradas */
            .categoria-section {{
                margin-bottom: 32px;
                animation: fadeIn 0.5s ease-out;
            }}

            .categoria-header {{
                display: flex;
                align-items: center;
                gap: 12px;
                margin-bottom: 16px;
                padding: 12px 16px;
                background: rgba(30, 41, 59, 0.6);
                border-radius: 12px;
                border-left: 4px solid;
                cursor: pointer;
                transition: all 0.3s;
            }}

            .categoria-header:hover {{
                background: rgba(30, 41, 59, 0.8);
                transform: translateX(5px);
            }}

            .cat-icon {{ font-size: 24px; }}

            .cat-nombre {{
                font-size: 14px;
                font-weight: 700;
                letter-spacing: 1px;
                flex: 1;
            }}

            .cat-count {{
                background: rgba(0,0,0,0.3);
                padding: 4px 12px;
                border-radius: 20px;
                font-size: 11px;
                font-weight: 600;
            }}

            .btn-toggle {{
                background: transparent;
                border: none;
                color: #94a3b8;
                cursor: pointer;
                font-size: 16px;
                transition: transform 0.3s;
            }}

            .categoria-section.collapsed .items-grid {{
                display: none;
            }}

            .categoria-section.collapsed .btn-toggle {{
                transform: rotate(-90deg);
            }}

            /* Grid de items mejorado */
            .items-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
                gap: 16px;
                transition: all 0.3s;
            }}

            /* Tarjetas mejoradas */
            .item-card {{
                background: rgba(30, 41, 59, 0.8);
                backdrop-filter: blur(10px);
                border: 1px solid rgba(255,255,255,0.1);
                border-radius: 16px;
                padding: 20px;
                transition: all 0.3s;
                position: relative;
                overflow: hidden;
            }}

            .item-card::before {{
                content: '';
                position: absolute;
                top: 0;
                left: -100%;
                width: 100%;
                height: 100%;
                background: linear-gradient(90deg, transparent, rgba(255,255,255,0.1), transparent);
                transition: left 0.5s;
            }}

            .item-card:hover::before {{
                left: 100%;
            }}

            .item-card:hover {{
                transform: translateY(-5px) scale(1.02);
                box-shadow: 0 20px 40px rgba(0,0,0,0.3);
                border-color: rgba(59, 130, 246, 0.5);
            }}

            .item-titulo {{
                font-size: 16px;
                font-weight: 700;
                margin-bottom: 10px;
                background: linear-gradient(135deg, #fff, #a5f3fc);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
            }}

            .item-contenido {{
                font-size: 13px;
                color: #94a3b8;
                line-height: 1.6;
                margin-bottom: 16px;
            }}

            .item-actions {{
                display: flex;
                gap: 10px;
                justify-content: flex-end;
            }}

            .btn-ver, .btn-eliminar {{
                padding: 6px 12px;
                border-radius: 8px;
                font-size: 12px;
                cursor: pointer;
                transition: all 0.3s;
                border: none;
                font-weight: 500;
            }}

            .btn-ver {{
                background: rgba(59, 130, 246, 0.2);
                color: #60a5fa;
                border: 1px solid rgba(59, 130, 246, 0.3);
            }}

            .btn-ver:hover {{
                background: #3b82f6;
                color: white;
                transform: scale(1.05);
            }}

            .btn-eliminar {{
                background: rgba(239, 68, 68, 0.2);
                color: #f87171;
                border: 1px solid rgba(239, 68, 68, 0.3);
            }}

            .btn-eliminar:hover {{
                background: #ef4444;
                color: white;
                transform: scale(1.05);
            }}

            /* Modal mejorado */
            .modal {{
                display: none;
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(0,0,0,0.8);
                backdrop-filter: blur(5px);
                z-index: 1000;
                justify-content: center;
                align-items: center;
                animation: fadeIn 0.3s;
            }}

            .modal-content {{
                background: rgba(30, 41, 59, 0.95);
                backdrop-filter: blur(10px);
                border-radius: 24px;
                padding: 32px;
                max-width: 600px;
                width: 90%;
                max-height: 80vh;
                overflow-y: auto;
                position: relative;
                animation: slideIn 0.3s;
            }}

            .modal-header {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 20px;
                padding-bottom: 15px;
                border-bottom: 2px solid rgba(255,255,255,0.1);
            }}

            .modal-title {{
                font-size: 20px;
                font-weight: 700;
                background: linear-gradient(135deg, #fff, #a5f3fc);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
            }}

            .modal-close {{
                background: transparent;
                border: none;
                color: #94a3b8;
                font-size: 28px;
                cursor: pointer;
                transition: all 0.3s;
            }}

            .modal-close:hover {{
                color: #ef4444;
                transform: scale(1.1);
            }}

            .modal-body {{
                line-height: 1.8;
                color: #cbd5e1;
            }}

            /* Toast mejorado */
            .toast {{
                position: fixed;
                bottom: 30px;
                right: 30px;
                background: linear-gradient(135deg, #1d4ed8, #2563eb);
                color: white;
                padding: 16px 24px;
                border-radius: 12px;
                font-size: 14px;
                font-weight: 500;
                display: none;
                z-index: 1000;
                box-shadow: 0 10px 30px rgba(0,0,0,0.3);
                animation: slideIn 0.3s;
            }}

            .toast.error {{
                background: linear-gradient(135deg, #dc2626, #ef4444);
            }}

            .toast.show {{
                display: block;
            }}

            /* Loading spinner */
            .loading {{
                display: inline-block;
                width: 20px;
                height: 20px;
                border: 3px solid rgba(255,255,255,0.3);
                border-radius: 50%;
                border-top-color: white;
                animation: spin 0.6s linear;
            }}

            /* Responsive */
            @media (max-width: 800px) {{
                .container {{
                    grid-template-columns: 1fr;
                    padding: 20px;
                }}
                .panel-form {{
                    position: static;
                }}
                .topbar {{
                    padding: 15px 20px;
                }}
                .topbar-title {{
                    font-size: 18px;
                }}
            }}

            /* Scrollbar personalizado */
            ::-webkit-scrollbar {{
                width: 8px;
                height: 8px;
            }}

            ::-webkit-scrollbar-track {{
                background: rgba(30, 41, 59, 0.5);
                border-radius: 10px;
            }}

            ::-webkit-scrollbar-thumb {{
                background: linear-gradient(135deg, #1d4ed8, #2563eb);
                border-radius: 10px;
            }}

            ::-webkit-scrollbar-thumb:hover {{
                background: linear-gradient(135deg, #2563eb, #3b82f6);
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
                <label>📝 Título</label>
                <input type="text" id="titulo" placeholder="Ej: Ceviche clásico">
            </div>

            <div class="form-group">
                <label>📄 Descripción completa</label>
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

    <!-- Modal para ver contenido completo -->
    <div id="modal" class="modal">
        <div class="modal-content">
            <div class="modal-header">
                <div class="modal-title" id="modalTitle"></div>
                <button class="modal-close" onclick="cerrarModal()">&times;</button>
            </div>
            <div class="modal-body" id="modalBody"></div>
        </div>
    </div>

    <div class="toast" id="toast"></div>

    <script>
        let currentLoading = false;

        function setCategoria(cat, btn) {{
            document.getElementById('categoria').value = cat;
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            btn.classList.add('active');
            showToast(`Categoría seleccionada: ${{cat}}`);
        }}

        function toggleCategoria(btn) {{
            const section = btn.closest('.categoria-section');
            section.classList.toggle('collapsed');
        }}

        function showToast(msg, error=false) {{
            const t = document.getElementById('toast');
            t.textContent = msg;
            t.className = 'toast show' + (error ? ' error' : '');
            setTimeout(() => t.className = 'toast', 3000);
        }}

        async function guardar() {{
            if (currentLoading) return;
            
            const categoria = document.getElementById('categoria').value;
            const titulo = document.getElementById('titulo').value.trim();
            const contenido = document.getElementById('contenido').value.trim();

            if (!titulo || !contenido) {{
                showToast('❌ Completa todos los campos', true);
                return;
            }}

            currentLoading = true;
            const btn = document.querySelector('.btn-guardar');
            const originalText = btn.innerHTML;
            btn.innerHTML = '<span class="loading"></span> Guardando...';
            btn.disabled = true;

            try {{
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
            }} catch (error) {{
                showToast('❌ Error de conexión', true);
            }} finally {{
                currentLoading = false;
                btn.innerHTML = originalText;
                btn.disabled = false;
            }}
        }}

        async function eliminar(id) {{
            if (!confirm('¿Eliminar este item?')) return;
            
            const res = await fetch('/conocimiento/' + id, {{ method: 'DELETE' }});
            if (res.ok) {{
                showToast('🗑️ Eliminado correctamente');
                setTimeout(() => location.reload(), 1000);
            }} else {{
                showToast('❌ Error al eliminar', true);
            }}
        }}

        async function subirArchivo(input) {{
            const file = input.files[0];
            if (!file) return;
            
            const formData = new FormData();
            formData.append('file', file);
            const categoria = document.getElementById('categoria').value;
            
            showToast('⏳ Procesando archivo...');
            
            try {{
                const res = await fetch('/conocimiento/upload?categoria=' + categoria, {{
                    method: 'POST',
                    body: formData
                }});
                
                if (res.ok) {{
                    const data = await res.json();
                    showToast(`✅ ${{data.chunks}} secciones cargadas correctamente`);
                    setTimeout(() => location.reload(), 1500);
                }} else {{
                    showToast('❌ Error al procesar el archivo', true);
                }}
            }} catch (error) {{
                showToast('❌ Error de conexión', true);
            }}
            
            input.value = '';
        }}

        function verContenido(id, titulo, contenido) {{
            document.getElementById('modalTitle').textContent = titulo;
            document.getElementById('modalBody').innerHTML = contenido.replace(/\\n/g, '<br>');
            document.getElementById('modal').style.display = 'flex';
        }}

        function cerrarModal() {{
            document.getElementById('modal').style.display = 'none';
        }}

        // Cerrar modal con ESC
        document.addEventListener('keydown', function(e) {{
            if (e.key === 'Escape') {{
                cerrarModal();
            }}
        }});

        // Cerrar modal clickeando fuera
        document.getElementById('modal').addEventListener('click', function(e) {{
            if (e.target === this) {{
                cerrarModal();
            }}
        }});

        // Animación de entrada para las tarjetas
        document.addEventListener('DOMContentLoaded', function() {{
            const cards = document.querySelectorAll('.item-card');
            cards.forEach((card, index) => {{
                card.style.animation = `fadeIn 0.5s ease-out ${{index * 0.05}}s both`;
            }});
        }});
    </script>

    </body>
    </html>
    """
    return html

@router.delete("/conocimiento/{{item_id}}")
def eliminar_conocimiento(item_id: int):
    with engine.connect() as conn:
        conn.execute(text("DELETE FROM conocimiento WHERE id = :id"), {"id": item_id})
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