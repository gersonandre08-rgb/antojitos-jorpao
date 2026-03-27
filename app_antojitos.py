import streamlit as st
import pandas as pd
import sqlite3
from google import genai
import json
import os
from datetime import datetime
import io
import random

# --- 1. CONFIGURACIÓN DE IA Y API ---
# Configura tu clave aquí
API_KEY = "AIzaSyDFwIADCQK6kDey3KhRcPGONXcpqqxtfSg" 
client = genai.Client(api_key=API_KEY)
ID_MODELO = 'gemini-2.5-flash'

# --- 2. CONFIGURACIÓN DE PÁGINA Y ESTILOS ---
st.set_page_config(page_title="Antojitos JorPao", page_icon="🥤", layout="wide")

# Estilos CSS avanzados - VERSIÓN CORREGIDA PARA CELULAR
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Bungee&family=Inter:wght@400;700&display=swap');

    .stApp {
        background: linear-gradient(135deg, #FFD700 0%, #FF8C00 100%);
    }
    
    /* --- ESTILO DEL TÍTULO PRINCIPAL (PARA PC) --- */
    .main-title {
        font-family: 'Bungee', cursive;
        color: #FFFFFF;
        text-shadow: 4px 4px 0px #FF4500, 8px 8px 15px rgba(0,0,0,0.3);
        font-size: 70px; /* Un poco más grande para PC */
        text-align: center;
        padding: 10px;
        margin-top: -40px; /* Sube más el título */
        margin-bottom: 0px;
        line-height: 1.1; /* Ajusta el interlineado */
        white-space: normal; /* Permite saltos de línea normales si es necesario */
    }
    
    /* --- ¡SOLUCIÓN PARA CELULAR! (RESPONSIVO) --- */
    @media (max-width: 600px) {
        .main-title {
            font-size: 38px !important; /* Letra mucho más chica en móvil para que entre */
            text-shadow: 2px 2px 0px #FF4500 !important;
            margin-top: -30px !important;
            padding: 5px !important;
            /* Evita que se corte la palabra en dos */
            word-wrap: normal !important;
            word-break: normal !important;
            overflow-wrap: break-word !important;
        }
        .subtitle {
            font-size: 13px !important;
            margin-top: -10px !important;
            margin-bottom: 20px !important;
            padding: 0 10px;
        }
    }
    
    .subtitle {
        font-family: 'Inter', sans-serif;
        color: #FFFFFF;
        font-weight: bold;
        text-align: center;
        font-size: 18px;
        margin-top: -20px;
        margin-bottom: 30px;
        letter-spacing: 2px;
    }

    /* --- AGRANDAR TEXTOS ESPECÍFICOS (FLECHAS) --- */
    /* Texto de ayuda arriba del nombre */
    .stMarkdown p {
        font-size: 20px !important;
        line-height: 1.5;
    }

    /* Etiqueta "¿Dónde entregamos?" */
    label[data-testid="stWidgetLabel"] p {
        font-size: 24px !important;
        font-weight: bold !important;
        color: #333 !important;
    }

    /* Texto dentro del selector */
    .stSelectbox div[data-baseweb="select"] {
        font-size: 18px !important;
    }

    /* --- OTROS ESTILOS --- */
    .stButton>button { 
        border-radius: 20px; font-weight: bold; background-color: #FF4500; 
        color: white; border: none; transition: 0.3s;
    }
    .stButton>button:hover { background-color: #E63900; transform: scale(1.05); }
    
    .product-card { 
        background-color: white; padding: 20px; border-radius: 20px; 
        box-shadow: 5px 5px 15px rgba(0,0,0,0.15); margin-bottom: 20px; color: #333;
    }
    
    .ia-section {
        background: white; padding: 25px; border-radius: 25px; 
        border: 5px solid #FF8C00; margin-bottom: 30px; box-shadow: 0px 10px 20px rgba(0,0,0,0.2);
    }
    </style>
    
    <div class="main-title">ANTOJITOS JORPAO</div>
    <div class="subtitle">¡EL SABOR QUE TE PONE PILAS, SOBRINO!</div>
    """, unsafe_allow_html=True)

# --- 3. GESTIÓN DE BASE DE DATOS ---
def get_db():
    conn = sqlite3.connect('antojitos_jorpao.db', check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db(); c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS productos 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT, categoria TEXT, 
                  costo REAL, venta REAL, stock INTEGER, imagen_path TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS pedidos 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, fecha TEXT, cliente TEXT, celular TEXT, 
                  direccion TEXT, zona TEXT, productos_json TEXT, total REAL, ganancia REAL,
                  metodo_pago TEXT, monto_pagado REAL, captura_pago TEXT, estado TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS resenas 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, cliente TEXT, mensaje TEXT, fecha TEXT)''')
    conn.commit(); conn.close()

if not os.path.exists("img_productos"): os.makedirs("img_productos")
if not os.path.exists("capturas_yape"): os.makedirs("capturas_yape")
init_db()

# --- 4. LÓGICA DE IA (TÍA JORPAO CON GEMINI) ---
def consultar_tia_gemini(user_query, nombre, productos):
    prods_str = ", ".join([p['nombre'] for p in productos])
    parentesco = "sobrina" if nombre.lower().endswith('a') else "sobrino"
    hora = datetime.now().hour
    saludo = "¡Buen día!" if 5 <= hora < 12 else "¡Buenas tardes!" if 12 <= hora < 19 else "¡Buenas noches!"
    
    prompt = f"""
    Eres la 'Tía JorPao', dueña de un negocio de antojitos en el Callao. 
    Eres criolla, divertida y hablas con mucha chispa (jerga peruana amigable).
    Tu cliente se llama {nombre}, trátalo como {parentesco}.
    Empieza con este saludo: '{saludo}'.
    Usa frases como: 'Te doy tu ayudín', 'Yo te aviento la boya', 'Te hago la gauchada', 'Te hago la taba'.
    Solo recomienda estos productos disponibles: {prods_str}.
    Responde de forma carismática y breve (máximo 2 líneas) a esto: {user_query}
    """
    try:
        response = client.models.generate_content(
            model=ID_MODELO,
            contents=prompt
        )
        return response.text
    except Exception as e:
        return f"¡Uy {parentesco}, se me bajó la presión del sistema! Pero pídete algo rico."

def to_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Reporte')
    return output.getvalue()

# --- 5. ESTADO DE SESIÓN ---
if 'carrito' not in st.session_state: st.session_state.carrito = []
if 'nombre_usuario' not in st.session_state: st.session_state.nombre_usuario = ""
if 'pedido_exitoso' not in st.session_state: st.session_state.pedido_exitoso = False

# --- 6. SIDEBAR ---
with st.sidebar:
    if os.path.exists("WhatsApp Image 2026-03-27 at 01.27.46.jpeg"): 
        st.image("WhatsApp Image 2026-03-27 at 01.27.46.jpeg", caption="Aquí no solo vendemos snacks, vendemos el momento más rico de tu tarde.", use_container_width=True)
    st.markdown("---")
    pwd = st.text_input("🔑 Acceso Admin", type="password")
    opciones = ["🛒 Tienda Online", "✍️ Dejar Reseña"]
    if pwd == "jorpao2026": opciones.extend(["⚙️ Gestión de Inventario", "📊 Análisis y Reportes"])
    menu = st.radio("Navegación", opciones)

# ==============================================================================
# VISTA: TIENDA ONLINE
# ==============================================================================
if menu == "🛒 Tienda Online":

    conn = get_db()
    ps = pd.read_sql_query("SELECT * FROM productos WHERE stock > 0", conn).to_dict('records')
    conn.close()

    if st.session_state.pedido_exitoso:
        st.balloons()
        st.success("## ✅ ¡Pedido recibido! La tía ya se puso el delantal.")
        st.markdown(f'<a href="https://wa.me/51963142733?text=Hola%20JorPao!%20Confirmo%20mi%20pedido%20web" target="_blank"><button style="width:100%;height:50px;background:#25D366;color:white;border:none;border-radius:10px;font-weight:bold;cursor:pointer;">🟢 ENVIAR WHATSAPP DE CONFIRMACIÓN</button></a>', unsafe_allow_html=True)
        if st.button("⬅️ Volver a la Tienda"): st.session_state.pedido_exitoso = False; st.rerun()
        st.stop()

    # --- BLOQUE IA VENDEDORA ---
    st.markdown('<div class="ia-section">', unsafe_allow_html=True)
    c_ia1, c_ia2 = st.columns([1, 4])
    
    with c_ia1:
        if os.path.exists("logo.png"):
            st.image("logo.png")
    
    with c_ia2:
        if not st.session_state.nombre_usuario:
            st.session_state.nombre_usuario = st.text_input("¡Hola sobrino/a! No sabes que pedir?, déjame tu nombre y selecciona tu barrio para ayudarte")
        else:
            # 1. LÓGICA DE MENSAJES DEL DÍA
            dias = {
                0: "Para este lunes pesado, un antojito para despertar... ☕",
                1: "Para este martes aburrido, ponle sabor a tu tarde... 🍬",
                2: "Para este día de miércoles, ¡date un gusto que te lo mereces! 🍰",
                3: "Para este jueves optimista, ya casi llegamos a la meta... 🚀",
                4: "¡Hoy es viernes y el cuerpo lo sabe! 💃🕺 ¿Qué se te antoja, sobrino?",
                5: "¡Fin de semana, sobrino! A disfrutar como se debe... 🍦",
                6: "Que nunca se acabe el domingo... relájate con algo rico. 🥤"
            }
            
            dia_idx = datetime.now().weekday()
            mensaje_hoy = dias.get(dia_idx)
            
            # COLOR ESPECIAL PARA EL VIERNES
            color_borde = "#FF4500" if dia_idx != 4 else "#FF0000" # Rojo pasión para el viernes
            fondo = "#FFF3E0" if dia_idx != 4 else "#FFF0F0"

            # ESTE ES EL CONTENEDOR QUE REEMPLAZA AL CUADRO BLANCO
            contenedor_dinamico = st.empty()
            
            with contenedor_dinamico.container():
                st.markdown(f"""
                    <div style="background-color: #FFF3E0; padding: 20px; border-radius: 15px; border-left: 10px solid #FF4500;">
                        <h2 style="margin: 0; color: #E65100; font-family: 'Bungee', sans-serif; font-size: 28px;">
                            {mensaje_hoy}
                        </h2>
                        <p style="margin: 10px 0 0 0; font-size: 1.2em; color: #333;">
                            ¡Hola <b>{st.session_state.nombre_usuario}</b>! ¿Qué te provoca hoy?
                        </p>
                    </div>
                """, unsafe_allow_html=True)

            # 2. BOTONES DE PREGUNTAS PREDETERMINADAS (Se mantienen intactos)
            st.write("") # Espacio estético
            col_b1, col_b2, col_b3, col_b4 = st.columns(4)
            p_ia = ""
            
            if col_b1.button("¡Ayúdame por favor, que calor!"): p_ia = "Ayúdame por favor, no sé qué pedir para la sed."
            if col_b2.button("Que me recomienda?"): p_ia = "Dime qué me recomiendas hoy."
            if col_b3.button("Qué es lo que más sale?"): p_ia = "¿Cuál es el producto estrella?"
            if col_b4.button("Asu, estoy con un hambre"): p_ia = "Recomiéndame algo para el hambre fuerte."
            
            # 3. INTERACCIÓN DE LA IA Y MUESTRA DE IMAGEN
            if p_ia:
                with st.spinner("Sobrino, voy a revisar la vitrina..."):
                    respuesta = consultar_tia_gemini(p_ia, st.session_state.nombre_usuario, ps)
                    
                    # Buscamos si la IA mencionó algún producto para mostrar su foto
                    img_sugerida = None
                    for prod in ps:
                        if prod['nombre'].lower() in respuesta.lower():
                            if prod.get('imagen_path'):
                                img_sugerida = prod['imagen_path']
                            break

                    with contenedor_dinamico.container():
                        st.info(respuesta)
                        if img_sugerida and os.path.exists(img_sugerida):
                            st.image(img_sugerida, caption=f"¡Te recomiendo esto!", width=250)
                            if st.button("🛒 ¡Lo quiero!"):
                                st.toast("¡Buena elección!")

    st.markdown('</div>', unsafe_allow_html=True)

    # --- SELECCIÓN DE PRODUCTOS ---
    st.title("🍨 Nuestros Antojitos")
    zona = st.selectbox("📍 Selecciona tu barrio", ["Selecciona...", "Residencial Aeropuerto", "Playa Rímac", "Otro"])
    if zona == "Otro": st.error("⚠️ Delivery automático solo en Aeropuerto y Playa Rímac."); st.stop()
    elif zona == "Selecciona...": st.stop()

    with st.expander("👤 Tus Datos de Entrega", expanded=True):
        u_nom = st.text_input("Nombre y Apellido", value=st.session_state.nombre_usuario)
        u_cel = st.text_input("Celular (9 dígitos)")
        u_dir = st.text_input("Dirección / Nro de Depto / Referencia")

    conn = get_db(); df_p = pd.read_sql_query("SELECT * FROM productos WHERE stock > 0", conn); conn.close()
    
    for _, p in df_p.iterrows():
        with st.container():
            st.markdown('<div class="product-card">', unsafe_allow_html=True)
            c1, c2, c3 = st.columns([1, 2, 1])
            if p['imagen_path'] and os.path.exists(p['imagen_path']):
                c1.image(p['imagen_path'], width=130)
                with c1.expander("🔍 Ver foto"): st.image(p['imagen_path'], use_container_width=True)
            
            c2.markdown(f"### {p['nombre']}")
            c2.markdown(f"**Precio: S/ {p['venta']:.2f}**")
            stk_clase = "low-stock" if p['stock'] <= 3 else "ok-stock"
            c2.markdown(f'<span class="stock-tag {stk_clase}">Stock: {p['stock']}</span>', unsafe_allow_html=True)
            
            if c3.button("➕ Añadir", key=f"add_{p['id']}"):
                st.session_state.carrito.append(p.to_dict()); st.toast(f"Añadido: {p['nombre']}")
            st.markdown('</div>', unsafe_allow_html=True)

    # --- CHECKOUT ---
    if st.session_state.carrito:
        st.divider()
        df_c = pd.DataFrame(st.session_state.carrito)
        total = df_c['venta'].sum() + 2.0
        ganancia = (df_c['venta'] - df_c['costo']).sum()
        
        st.subheader("💰 Resumen de Compra")
        st.table(df_c[['nombre', 'venta']])
        st.markdown(f"### **Total a Pagar: S/ {total:.2f}** (Inc. Delivery S/ 2.00)")
        
        metodo = st.radio("Método de Pago", ["Yape / Plin", "Efectivo"])
        cap = None; vuelto = 0
        if metodo == "Yape / Plin":
            st.info("📱 Yape/Plin al 963 142 733 (Paula Ottiniano)")
            cap = st.file_uploader("Sube tu captura de pago")
        else:
            vuelto = st.number_input("¿Con cuánto pagarás?", min_value=total)

        if st.button("🚀 CONFIRMAR PEDIDO", type="primary", use_container_width=True):
            if u_nom and u_cel and u_dir:
                conn = get_db(); c = conn.cursor()
                p_path = f"capturas_yape/p_{u_cel}_{datetime.now().second}.png" if cap else None
                if cap:
                    with open(p_path, "wb") as f: f.write(cap.getbuffer())
                
                c.execute("""INSERT INTO pedidos (fecha, cliente, celular, direccion, zona, productos_json, 
                             total, ganancia, metodo_pago, monto_pagado, captura_pago, estado) 
                             VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                          (datetime.now().strftime("%Y-%m-%d %H:%M"), u_nom, u_cel, u_dir, zona, df_c.to_json(), 
                           total, ganancia, metodo, vuelto, p_path, "Nuevo"))
                
                for pid in df_c['id']: c.execute("UPDATE productos SET stock = stock - 1 WHERE id = ?", (pid,))
                conn.commit(); conn.close()
                st.session_state.carrito = []; st.session_state.pedido_exitoso = True; st.rerun()
            else: st.error("Faltan datos de entrega.")

# ==============================================================================
# VISTA: GESTIÓN DE INVENTARIO (ADMIN)
# ==============================================================================
elif menu == "⚙️ Gestión de Inventario":
    st.header("📦 Control de Productos")
    t1, t2, t3 = st.tabs(["Stock Actual", "Agregar Producto", "🧹 Limpieza de Pruebas"])
    
    with t1:
        # 1. CARGAR DATOS
        conn = get_db()
        df_i = pd.read_sql_query("SELECT * FROM productos", conn)
        conn.close()
        
        # --- BOTÓN PARA DESCARGAR EXCEL ---
        if not df_i.empty:
            # Función interna para generar el archivo
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                # Calculamos el valor total del inventario (Venta x Stock)
                df_reporte = df_i.copy()
                df_reporte['Valor Total'] = df_reporte['venta'] * df_reporte['stock']
                
                df_reporte.to_excel(writer, index=False, sheet_name='Stock_Antojitos')
                
                # Formato estético para el Excel
                workbook  = writer.book
                worksheet = writer.sheets['Stock_Antojitos']
                header_format = workbook.add_format({
                    'bold': True, 'fg_color': '#FF8C00', 'font_color': 'white', 'border': 1
                })
                for col_num, value in enumerate(df_reporte.columns.values):
                    worksheet.write(0, col_num, value, header_format)

            st.download_button(
                label="📥 Descargar Reporte de Stock (Excel)",
                data=output.getvalue(),
                file_name=f"stock_antojitos_{datetime.now().strftime('%d_%m_%Y')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        
        # 2. EDITOR DE DATOS
        df_edit = st.data_editor(df_i, num_rows="dynamic", key="editor_stock")
        
        if st.button("Guardar Cambios"):
            conn = get_db()
            c = conn.cursor()
            c.execute("DELETE FROM productos")
            for _, r in df_edit.iterrows():
                # Aseguramos que el ID se mantenga o se genere correctamente
                c.execute("""INSERT INTO productos 
                          (id, nombre, categoria, costo, venta, stock, imagen_path) 
                          VALUES (?,?,?,?,?,?,?)""",
                          (r.get('id'), r['nombre'], r['categoria'], r['costo'], r['venta'], r['stock'], r['imagen_path']))
            conn.commit()
            conn.close()
            st.success("¡Cambios guardados y stock actualizado!")
            st.rerun()

    with t2:
        with st.form("new_p", clear_on_submit=True):
            st.markdown("### ✨ Nuevo Producto")
            n = st.text_input("Nombre")
            cat = st.selectbox("Categoría", ["Bebidas", "Dulces", "Snacks", "Otros"])
            col1, col2, col3 = st.columns(3)
            co = col1.number_input("Costo unitario", min_value=0.0)
            ve = col2.number_input("Venta unitaria", min_value=0.0)
            stk = col3.number_input("Stock inicial", step=1, min_value=0)
            img = st.file_uploader("Foto del producto")
            
            if st.form_submit_button("Añadir al Inventario"):
                if n:
                    # Crear carpeta si no existe
                    if not os.path.exists("img_productos"):
                        os.makedirs("img_productos")
                        
                    path = f"img_productos/{n.replace(' ', '_')}.png" if img else ""
                    if img:
                        with open(path, "wb") as f:
                            f.write(img.getbuffer())
                    
                    conn = get_db()
                    c = conn.cursor()
                    c.execute("""INSERT INTO productos (nombre, categoria, costo, venta, stock, imagen_path) 
                              VALUES (?,?,?,?,?,?)""", (n, cat, co, ve, stk, path))
                    conn.commit()
                    conn.close()
                    st.success(f"✅ {n} añadido correctamente.")
                    st.rerun()
                else:
                    st.error("Sobrino, ponle un nombre al producto pe'.")

    with t3:
        st.subheader("🧹 Limpieza de Base de Datos")
        st.info("Esta opción borrará todos los registros que contengan 'Prueba' o tu nombre para dejar el reporte limpio.")
        if st.button("🗑️ Ejecutar Limpieza de Registros"):
            conn = get_db()
            c = conn.cursor()
            # Borra pedidos de prueba (ajustado a tus nombres según la captura)
            c.execute("DELETE FROM pedidos WHERE LOWER(cliente) IN ('prueba', 'gerson', 'gerson siverio', 'Ana') OR cliente LIKE '%prueba%'")
            conn.commit()
            conn.close()
            st.success("¡Base de datos limpia de pruebas! Ahora sí, a vender de verdad.")
            st.rerun()

# ==============================================================================
# VISTA: REPORTES (ADMIN)
# ==============================================================================
elif menu == "📊 Análisis y Reportes":
    st.header("📊 Métricas del Negocio")
    conn = get_db(); df_v = pd.read_sql_query("SELECT * FROM pedidos ORDER BY id DESC", conn); conn.close()
    
    if not df_v.empty:
        c1, c2, c3 = st.columns(3)
        c1.metric("Ventas Totales", f"S/ {df_v['total'].sum():.2f}")
        c2.metric("Ganancia Real", f"S/ {df_v['ganancia'].sum():.2f}")
        c3.metric("Nro de Pedidos", len(df_v))
        
        st.subheader("📋 Detalle de Pedidos")
        for _, r in df_v.iterrows():
            with st.expander(f"Pedido #{r['id']} - {r['cliente']} ({r['fecha']})"):
                col_a, col_b = st.columns(2)
                with col_a:
                    st.write(f"📞 Cel: {r['celular']} | 📍 Zona: {r['zona']}")
                    st.write(f"🏠 Dir: {r['direccion']}")
                    st.write(f"💰 Total: S/ {r['total']} | Ganancia: S/ {r['ganancia']}")
                    if r['metodo_pago'] == "Efectivo": st.warning(f"Vuelto para: S/ {r['monto_pagado']}")
                with col_b:
                    if r['captura_pago']:
                        st.image(r['captura_pago'], width=200)
                        with open(r['captura_pago'], "rb") as f:
                            st.download_button(f"📥 Bajar Pago {r['id']}", data=f, file_name=f"pago_{r['id']}.png")
        st.download_button("📥 Excel de Ventas", data=to_excel(df_v), file_name="Ventas_JorPao.xlsx")
    else: st.info("No hay ventas registradas.")

# ==============================================================================
# VISTA: RESEÑAS
# ==============================================================================
elif menu == "✍️ Dejar Reseña":
    st.title("💬 ¿Qué dicen nuestros sobrinos?")
    with st.form("res"):
        n = st.text_input("Tu nombre"); m = st.text_area("¿Qué te pareció el antojo?")
        if st.form_submit_button("Publicar"):
            conn = get_db(); c = conn.cursor()
            c.execute("INSERT INTO resenas (cliente, mensaje, fecha) VALUES (?,?,?)", (n, m, datetime.now().strftime("%d/%m/%Y")))
            conn.commit(); conn.close(); st.success("¡Gracias!")
    conn = get_db(); df_r = pd.read_sql_query("SELECT * FROM resenas ORDER BY id DESC", conn); conn.close()
    for _, r in df_r.iterrows(): st.info(f"👤 **{r['cliente']}** ({r['fecha']}): {r['mensaje']}")