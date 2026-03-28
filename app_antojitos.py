import streamlit as st
import pandas as pd
import sqlite3
import json
import os
from datetime import datetime
import io
import random
import pytz

# --- CONFIGURACIÓN DE ZONA HORARIA (PERÚ) ---
def get_peru_time():
    lima_tz = pytz.timezone('America/Lima')
    return datetime.now(lima_tz)

# --- 1. CONFIGURACIÓN DE PÁGINA Y ESTILOS ---
st.set_page_config(page_title="Antojitos JorPao", page_icon="🥤", layout="wide")

# Estilos CSS - Mantenemos tu diseño original y optimizamos para móvil/categorías
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Bungee&family=Inter:wght@400;700&display=swap');

    .stApp {
        background: linear-gradient(135deg, #FFD700 0%, #FF8C00 100%);
    }
    
    .main-title {
        font-family: 'Bungee', cursive;
        color: #FFFFFF;
        text-shadow: 4px 4px 0px #FF4500, 8px 8px 15px rgba(0,0,0,0.3);
        font-size: 70px;
        text-align: center;
        padding: 10px;
        margin-top: -40px;
        margin-bottom: 0px;
        line-height: 1.1;
    }
    
    @media (max-width: 600px) {
        .main-title {
            font-size: 38px !important;
            margin-top: -30px !important;
            word-break: keep-all !important;
        }
        .subtitle { font-size: 13px !important; }
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

    .product-card { 
        background-color: white; 
        padding: 20px; 
        border-radius: 20px; 
        box-shadow: 5px 5px 15px rgba(0,0,0,0.15); 
        margin-bottom: 20px; 
        color: #333;
    }
    
    .order-card { 
        background: #FFF3E0; 
        padding: 15px; 
        border-radius: 15px; 
        border-left: 8px solid #FF4500; 
        margin-bottom: 15px; 
        color: #333;
    }

    .stButton>button { 
        border-radius: 20px; 
        font-weight: bold; 
        background-color: #FF4500; 
        color: white; 
        border: none; 
        transition: 0.3s;
    }
    .stButton>button:hover { background-color: #E63900; transform: scale(1.05); }

    .clima-section {
        background: white; 
        padding: 20px; 
        border-radius: 20px; 
        border-left: 10px solid #FF8C00; 
        margin-bottom: 25px;
    }
    </style>
    
    <div class="main-title">ANTOJITOS JORPAO</div>
    <div class="subtitle">¡ENDULZAMOS TU DIA, VECINO/A!</div>
    """, unsafe_allow_html=True)

# --- 2. GESTIÓN DE BASE DE DATOS ---
def get_db():
    conn = sqlite3.connect('antojitos_jorpao.db', check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db(); c = conn.cursor()
    # Productos
    c.execute('''CREATE TABLE IF NOT EXISTS productos 
                  (id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT, categoria TEXT, 
                   costo REAL, venta REAL, stock INTEGER, imagen_path TEXT)''')
    # Categorías
    c.execute('''CREATE TABLE IF NOT EXISTS categorias 
                  (id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT UNIQUE)''')
    # Combos
    c.execute('''CREATE TABLE IF NOT EXISTS combos 
                  (id INTEGER PRIMARY KEY AUTOINCREMENT, nombre_combo TEXT, 
                   productos_ids TEXT, precio_combo REAL, activo INTEGER DEFAULT 1)''')
    # Pedidos
    c.execute('''CREATE TABLE IF NOT EXISTS pedidos 
                  (id INTEGER PRIMARY KEY AUTOINCREMENT, fecha TEXT, cliente TEXT, celular TEXT, 
                   direccion TEXT, zona TEXT, productos_json TEXT, total REAL, ganancia REAL,
                   metodo_pago TEXT, monto_pagado REAL, captura_pago TEXT, estado TEXT)''')
    # Reseñas
    c.execute('''CREATE TABLE IF NOT EXISTS resenas 
                  (id INTEGER PRIMARY KEY AUTOINCREMENT, cliente TEXT, mensaje TEXT, fecha TEXT)''')
    
    # Insertar categorías por defecto si la tabla está vacía
    c.execute("SELECT COUNT(*) FROM categorias")
    if c.fetchone()[0] == 0:
        for cat in ["Bebidas", "Dulces", "Snacks", "Otros"]:
            c.execute("INSERT INTO categorias (nombre) VALUES (?)", (cat,))
            
    conn.commit(); conn.close()

# Inicialización de carpetas y DB
if not os.path.exists("img_productos"): os.makedirs("img_productos")
if not os.path.exists("capturas_yape"): os.makedirs("capturas_yape")
init_db()

# --- 3. LÓGICA DINÁMICA (PLAN B SIN IA) ---
def obtener_sugerencia_clima():
    hora = get_peru_time().hour
    if 10 <= hora <= 17:
        return "🔥 ¡Está haciendo un calor fuerte!", "Bebidas", "Nada como una bebida heladita para la sed. ¡Pídela al polo!"
    elif 18 <= hora <= 23:
        return "☁️ El clima está refrescando.", "Snacks", "Para calentar el cuerpo, un snack saladito o algo contundente."
    else:
        return "🌤️ El clima está templado.", "Dulces", "Perfecto para un antojito dulce antes de terminar el día."

def notificacion_simulada():
    nombres = ["Gerson", "Jorge", "Ricardo", "Vanessa", "Don Lucho", "Ana", "Beto", "Anthony", "Cesar", "José", "Daniel"]
    zonas = ["Playa Rímac", "Res. Aeropuerto", "Santa Rosa", "Gambetta", "Carmen de la Legua", "Smp"]
    if random.random() < 0.2:
        st.toast(f"🛍️ {random.choice(nombres)} de {random.choice(zonas)} acaba de comprar un antojito.", icon="🔥")

def to_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Reporte')
    return output.getvalue()

# --- 4. ESTADO DE SESIÓN ---
if 'carrito' not in st.session_state: st.session_state.carrito = []
if 'nombre_usuario' not in st.session_state: st.session_state.nombre_usuario = ""
if 'pedido_exitoso' not in st.session_state: st.session_state.pedido_exitoso = False
if 'temp_combo_items' not in st.session_state: st.session_state.temp_combo_items = []

# --- 5. SIDEBAR ---
with st.sidebar:
    if os.path.exists("WhatsApp Image 2026-03-27 at 01.27.46.jpeg"): 
        st.image("WhatsApp Image 2026-03-27 at 01.27.46.jpeg", use_container_width=True)
    st.markdown("---")
    pwd = st.text_input("🔑 Acceso Admin", type="password")
    opciones = ["🛒 Tienda Online", "✍️ Dejar Reseña"]
    if pwd == "jyp2026.": 
        opciones.extend(["⚙️ Gestión de Inventario", "📊 Análisis y Reportes", "🎁 Gestionar Combos"])
    menu = st.radio("Navegación", opciones)

# ==============================================================================
# VISTA: TIENDA ONLINE
# ==============================================================================
if menu == "🛒 Tienda Online":
    notificacion_simulada()

    if st.session_state.pedido_exitoso:
        st.balloons()
        st.success("## ✅ ¡Pedido recibido! La vecina ya está preparando todo.")
        st.markdown(f'<a href="https://wa.me/51963142733?text=Hola%20JorPao!%20Confirmo%20mi%20pedido%20web" target="_blank"><button style="width:100%;height:50px;background:#25D366;color:white;border:none;border-radius:10px;font-weight:bold;cursor:pointer;">🟢 ENVIAR WHATSAPP DE CONFIRMACIÓN</button></a>', unsafe_allow_html=True)
        if st.button("⬅️ Volver a la Tienda"): 
            st.session_state.pedido_exitoso = False
            st.rerun()
        st.stop()

    tab_tienda, tab_carrito = st.tabs(["🛍️ VER VITRINA", "🛒 MI PEDIDO"])

    with tab_tienda:
        # Sección Dinámica Clima
        tit_clima, cat_sug, msg_clima = obtener_sugerencia_clima()
        st.markdown(f"""
            <div class="clima-section">
                <h3 style="margin:0; color:#E65100;">{tit_clima}</h3>
                <p style="margin:5px 0 0 0; font-size:1.1em;"><b>Sugerencia de la Vecina:</b> {msg_clima}</p>
            </div>
        """, unsafe_allow_html=True)

        if not st.session_state.nombre_usuario:
            st.session_state.nombre_usuario = st.text_input("¡Hola vecino/a! ¿Cuál es tu nombre?")
        
        zona = st.selectbox("📍 Selecciona tu barrio", ["Selecciona...", "Residencial Aeropuerto", "Playa Rímac", "Otro"])
        if zona == "Otro": 
            st.error("⚠️ Delivery solo en Aeropuerto y Playa Rímac."); st.stop()
        elif zona == "Selecciona...": 
            st.stop()

        with st.expander("👤 Tus Datos de Entrega", expanded=True):
            u_nom = st.text_input("Nombre Completo", value=st.session_state.nombre_usuario)
            u_cel = st.text_input("Celular (9 dígitos)")
            u_dir = st.text_input("Dirección / Nro de Dpto / Referencia")

        # --- MOSTRAR COMBOS ---
        conn = get_db()
        df_combos = pd.read_sql_query("SELECT * FROM combos WHERE activo = 1", conn)
        conn.close()
        
        if not df_combos.empty:
            st.subheader("🎁 Combos Ganadores")
            for _, c in df_combos.iterrows():
                with st.container():
                    st.markdown(f"""
                    <div class="product-card">
                        <h4 style="margin:0; color:#FF4500;">{c['nombre_combo']}</h4>
                        <p style="margin:5px 0;">Contiene: {c['productos_ids']}</p>
                        <p style="font-weight:bold; font-size:1.2em;">Precio Especial: S/ {c['precio_combo']:.2f}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    if st.button(f"Añadir {c['nombre_combo']}", key=f"btn_c_{c['id']}"):
                        st.session_state.carrito.append({'id': f"C-{c['id']}", 'nombre': c['nombre_combo'], 'venta': c['precio_combo'], 'costo': 0})
                        st.toast("¡Combo añadido!")

        # --- PRODUCTOS POR CATEGORÍAS DESPLEGABLES ---
        conn = get_db()
        df_cats = pd.read_sql_query("SELECT * FROM categorias", conn)
        df_p = pd.read_sql_query("SELECT * FROM productos WHERE stock > 0", conn)
        conn.close()

        st.subheader("🍨 Nuestra Vitrina")
        for _, cat in df_cats.iterrows():
            with st.expander(f"✨ {cat['nombre'].upper()}", expanded=(cat['nombre'] == cat_sug)):
                prods_cat = df_p[df_p['categoria'] == cat['nombre']]
                if prods_cat.empty:
                    st.write("Cargando nuevos productos para esta sección...")
                for _, p in prods_cat.iterrows():
                    st.markdown('<div class="product-card">', unsafe_allow_html=True)
                    c1, c2, c3 = st.columns([1, 2, 1])
                    if p['imagen_path'] and os.path.exists(p['imagen_path']):
                        c1.image(p['imagen_path'], width=100)
                    c2.markdown(f"**{p['nombre']}**")
                    c2.markdown(f"S/ {p['venta']:.2f}")
                    if c3.button("➕", key=f"add_{p['id']}"):
                        st.session_state.carrito.append(p.to_dict())
                        st.toast(f"✅ {p['nombre']} añadido")
                    st.markdown('</div>', unsafe_allow_html=True)

    with tab_carrito:
        if st.session_state.carrito:
            df_cart = pd.DataFrame(st.session_state.carrito)
            total = df_cart['venta'].sum() + 2.0 # Costo delivery
            ganancia_p = (df_cart['venta'] - df_cart.get('costo', 0)).sum()

            st.subheader("Resumen del Pedido")
            st.table(df_cart[['nombre', 'venta']])
            st.markdown(f"### **Total a Pagar: S/ {total:.2f}** (Delivery S/ 2.00 incluido)")

            metodo = st.radio("¿Cómo pagarás?", ["Yape / Plin", "Efectivo"])
            cap_pago = None; vuelto_de = 0
            
            if metodo == "Yape / Plin":
                st.info("📱 Yape/Plin: 963 142 733 (Paula Ottiniano)")
                cap_pago = st.file_uploader("Sube tu comprobante de pago")
            else:
                vuelvo_de = st.number_input("¿Con cuánto vas a pagar?", min_value=total)

            if st.button("🚀 FINALIZAR Y ENVIAR PEDIDO", type="primary", use_container_width=True):
                if u_nom and u_cel and u_dir:
                    p_path = f"capturas_yape/p_{u_cel}_{get_peru_time().second}.png" if cap_pago else None
                    if cap_pago:
                        with open(p_path, "wb") as f: f.write(cap_pago.getbuffer())
                    
                    conn = get_db(); c = conn.cursor()
                    c.execute("""INSERT INTO pedidos (fecha, cliente, celular, direccion, zona, productos_json, 
                                 total, ganancia, metodo_pago, monto_pagado, captura_pago, estado) 
                                 VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                              (get_peru_time().strftime("%Y-%m-%d %H:%M"), u_nom, u_cel, u_dir, zona, df_cart.to_json(orient='records'), 
                               total, ganancia_p, metodo, vuelto_de, p_path, "Nuevo"))
                    
                    # Descontar stock (solo si no es combo)
                    for pid in df_cart['id']:
                        if isinstance(pid, (int, float, int)):
                            c.execute("UPDATE productos SET stock = stock - 1 WHERE id = ?", (pid,))
                    
                    conn.commit(); conn.close()
                    st.session_state.carrito = []; st.session_state.pedido_exitoso = True; st.rerun()
                else:
                    st.error("Por favor, completa tus datos de entrega.")
        else:
            st.warning("Tu carrito está vacío, vecino. ¡Anímate por algo rico!")

# ==============================================================================
# VISTA: GESTIÓN DE INVENTARIO (ADMIN) - CATEGORÍAS CORREGIDAS
# ==============================================================================
elif menu == "⚙️ Gestión de Inventario":
    st.header("📦 Administración de Stock")
    t1, t2, t3, t4 = st.tabs(["Stock Actual", "Agregar Producto", "📁 Categorías", "🧹 Limpieza"])

    with t1:
        conn = get_db(); df_inv = pd.read_sql_query("SELECT * FROM productos", conn); conn.close()
        if not df_inv.empty:
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df_rep = df_inv.copy()
                df_rep['Valor Total'] = df_rep['venta'] * df_rep['stock']
                df_rep.to_excel(writer, index=False, sheet_name='Stock')
            st.download_button("📥 Descargar Reporte (Excel)", data=output.getvalue(), file_name="stock_antojitos.xlsx")
            
            df_edit = st.data_editor(df_inv, num_rows="dynamic", key="edit_prod")
            if st.button("Actualizar Todo"):
                conn = get_db(); c = conn.cursor()
                c.execute("DELETE FROM productos")
                for _, r in df_edit.iterrows():
                    c.execute("INSERT INTO productos (id, nombre, categoria, costo, venta, stock, imagen_path) VALUES (?,?,?,?,?,?,?)",
                              (r.get('id'), r['nombre'], r['categoria'], r['costo'], r['venta'], r['stock'], r['imagen_path']))
                conn.commit(); conn.close(); st.success("Inventario actualizado."); st.rerun()

    with t2:
        with st.form("new_product"):
            n = st.text_input("Nombre del Producto")
            conn = get_db(); df_c = pd.read_sql_query("SELECT nombre FROM categorias", conn); conn.close()
            cat = st.selectbox("Categoría", df_c['nombre'].tolist() if not df_c.empty else ["Otros"])
            co = st.number_input("Costo de Compra"); ve = st.number_input("Precio de Venta")
            stk = st.number_input("Stock Inicial", step=1)
            img = st.file_uploader("Imagen")
            if st.form_submit_button("Guardar Producto"):
                path = f"img_productos/{n.replace(' ','_')}.png" if img else ""
                if img:
                    with open(path, "wb") as f: f.write(img.getbuffer())
                conn = get_db(); c = conn.cursor()
                c.execute("INSERT INTO productos (nombre, categoria, costo, venta, stock, imagen_path) VALUES (?,?,?,?,?,?)",
                          (n, cat, co, ve, stk, path))
                conn.commit(); conn.close(); st.success("Añadido."); st.rerun()

    with t3:
        st.subheader("📁 Administrar Categorías")
        
        # Formulario para añadir
        col_add_n, col_add_b = st.columns([3, 1])
        n_cat = col_add_n.text_input("Nueva Categoría (Ej: Bebidas Calientes)")
        if col_add_b.button("Añadir", use_container_width=True):
            if n_cat:
                conn = get_db(); c = conn.cursor()
                c.execute("INSERT OR IGNORE INTO categorias (nombre) VALUES (?)", (n_cat,))
                conn.commit(); conn.close(); st.rerun()

        st.markdown("---")
        # Listado con opción de borrado
        conn = get_db(); df_cats_admin = pd.read_sql_query("SELECT * FROM categorias", conn); conn.close()
        for _, row in df_cats_admin.iterrows():
            c1, c2 = st.columns([4, 1])
            c1.write(f"📁 **{row['nombre']}**")
            if c2.button("Eliminar", key=f"del_cat_{row['id']}"):
                conn = get_db(); c = conn.cursor()
                c.execute("DELETE FROM categorias WHERE id = ?", (row['id'],))
                conn.commit(); conn.close()
                st.success(f"Categoría {row['nombre']} eliminada")
                st.rerun()

    with t4:
        st.subheader("🧹 Mantenimiento")
        if st.button("Borrar Pedidos de Prueba"):
            conn = get_db(); c = conn.cursor()
            c.execute("DELETE FROM pedidos WHERE LOWER(cliente) LIKE '%prueba%' OR LOWER(cliente) IN ('gerson', 'ana')")
            conn.commit(); conn.close(); st.success("Base de datos limpia."); st.rerun()

# ==============================================================================
# VISTA: GESTIÓN DE COMBOS (ADMIN) - MEJORADO CON CANTIDADES
# ==============================================================================
elif menu == "🎁 Gestionar Combos":
    st.header("🎁 Creador de Combos Ganadores")
    
    with st.container(border=True):
        col1, col2 = st.columns([2, 1])
        with col1:
            nom_combo = st.text_input("Nombre del Combo (Ej: Combo Mundialista)")
        with col2:
            precio_combo = st.number_input("Precio Final del Combo S/", min_value=0.0)

        st.markdown("### 📝 Selecciona la cantidad de cada producto:")
        c_prod, c_cant, c_add = st.columns([3, 1, 1])
        
        conn = get_db(); df_ps = pd.read_sql_query("SELECT nombre FROM productos", conn); conn.close()
        prod_sel = c_prod.selectbox("Producto", df_ps['nombre'].tolist() if not df_ps.empty else ["Sin productos"])
        cant_sel = c_cant.number_input("Cant.", min_value=1, value=1)
        
        if c_add.button("➕ Añadir a Receta"):
            st.session_state.temp_combo_items.append(f"{cant_sel}x {prod_sel}")

        if st.session_state.temp_combo_items:
            st.write("**Lista del combo:** " + " + ".join(st.session_state.temp_combo_items))
            if st.button("🗑️ Limpiar Lista"): 
                st.session_state.temp_combo_items = []
                st.rerun()

        if st.button("🚀 LANZAR COMBO", type="primary", use_container_width=True):
            if nom_combo and st.session_state.temp_combo_items:
                receta_final = ", ".join(st.session_state.temp_combo_items)
                conn = get_db(); c = conn.cursor()
                c.execute("INSERT INTO combos (nombre_combo, productos_ids, precio_combo) VALUES (?,?,?)",
                          (nom_combo, receta_final, precio_combo))
                conn.commit(); conn.close()
                st.session_state.temp_combo_items = []
                st.success("¡Combo activo en la tienda!")
                st.rerun()
            else:
                st.error("Debes poner un nombre y añadir productos.")

    st.markdown("---")
    st.subheader("📋 Combos en Vitrina")
    conn = get_db(); df_list_combos = pd.read_sql_query("SELECT * FROM combos", conn); conn.close()
    
    for _, cb in df_list_combos.iterrows():
        with st.container():
            col_a, col_b, col_c = st.columns([3, 1, 1])
            col_a.markdown(f"**{cb['nombre_combo']}** \n<small>{cb['productos_ids']}</small>", unsafe_allow_html=True)
            col_b.write(f"S/ {cb['precio_combo']:.2f}")
            if col_c.button("Borrar", key=f"del_cb_{cb['id']}"):
                conn = get_db(); c = conn.cursor()
                c.execute("DELETE FROM combos WHERE id = ?", (cb['id'],))
                conn.commit(); conn.close()
                st.success("Combo eliminado")
                st.rerun()

# ==============================================================================
# VISTA: REPORTES Y BANDEJA DE PEDIDOS (ADMIN)
# ==============================================================================
elif menu == "📊 Análisis y Reportes":
    st.header("📊 Métricas y Gestión de Pedidos")
    
    conn = get_db()
    # Mostramos los nuevos arriba
    df_v = pd.read_sql_query("SELECT * FROM pedidos ORDER BY CASE WHEN estado = 'Nuevo' THEN 0 ELSE 1 END, id DESC", conn)
    conn.close()
    
    if not df_v.empty:
        # --- MÉTRICAS ---
        c1, c2, c3 = st.columns(3)
        c1.metric("Ventas Totales", f"S/ {df_v['total'].sum():.2f}")
        c2.metric("Ganancia Estimada", f"S/ {df_v['ganancia'].sum():.2f}")
        c3.metric("Nro Pedidos", len(df_v))
        
        # --- BANDEJA DE PEDIDOS ENTRANTE ---
        st.subheader("🔔 Bandeja de Pedidos")
        for _, ped in df_v.iterrows():
            with st.container():
                color_borde = "#FF4500" if ped['estado'] == 'Nuevo' else "#666"
                st.markdown(f"""
                <div class="order-card" style="border-left-color: {color_borde};">
                    <div style="display: flex; justify-content: space-between;">
                        <b>📦 Pedido #{ped['id']} - {ped['estado']}</b>
                        <i>{ped['fecha']}</i>
                    </div>
                    <hr style="margin: 10px 0; border: 0.5px solid #ddd;">
                    <b>👤 Cliente:</b> {ped['cliente']} ({ped['celular']})<br>
                    <b>📍 Ubicación:</b> {ped['direccion']} - {ped['zona']}<br>
                    <b>💰 Pago:</b> S/ {ped['total']:.2f} ({ped['metodo_pago']})
                </div>
                """, unsafe_allow_html=True)
                
                with st.expander("🔎 Ver detalle y gestionar"):
                    # Detalle de productos - CORRECCIÓN JSON
                    try:
                        items = json.loads(ped['productos_json'])
                        # Si el JSON es una cadena de texto doblemente codificada
                        if isinstance(items, str):
                            items = json.loads(items)
                            
                        # Si items es un diccionario (formato antiguo), convertir a lista
                        if isinstance(items, dict):
                            # Si viene de pandas .to_json() por defecto, es un dict de columnas
                            df_items = pd.DataFrame.from_dict(items)
                            items = df_items.to_dict('records')

                        for item in items:
                            st.write(f"• {item.get('nombre', 'Producto')} - S/ {item.get('venta', 0)}")
                    except Exception as e:
                        st.error(f"Error al cargar productos: {e}")
                    
                    if ped['captura_pago']:
                        st.image(ped['captura_pago'], caption="Comprobante Enviado", width=250)
                        
                        # --- BOTÓN DE DESCARGA AÑADIDO AQUÍ ---
                        if os.path.exists(ped['captura_pago']):
                            with open(ped['captura_pago'], "rb") as f:
                                st.download_button(
                                    label="📥 Descargar Comprobante",
                                    data=f,
                                    file_name=f"pago_pedido_{ped['id']}.png",
                                    mime="image/png",
                                    key=f"dl_{ped['id']}"
                                )
                    
                    # Botones de estado
                    if ped['estado'] == 'Nuevo':
                        col_acc1, col_acc2, _ = st.columns([1, 1, 2])
                        if col_acc1.button(f"✅ Marcar Entregado", key=f"ent_{ped['id']}"):
                            conn = get_db(); c = conn.cursor()
                            c.execute("UPDATE pedidos SET estado = 'Entregado' WHERE id = ?", (ped['id'],))
                            conn.commit(); conn.close(); st.rerun()
                        if col_acc2.button(f"❌ Cancelar", key=f"can_{ped['id']}"):
                            conn = get_db(); c = conn.cursor()
                            c.execute("UPDATE pedidos SET estado = 'Cancelado' WHERE id = ?", (ped['id'],))
                            conn.commit(); conn.close(); st.rerun()

        st.markdown("---")
        st.subheader("📋 Historial Completo")
        st.dataframe(df_v[['id', 'fecha', 'cliente', 'total', 'metodo_pago', 'estado']])
        st.download_button("📥 Descargar Reporte Ventas", data=to_excel(df_v), file_name="ventas_jorpao.xlsx")
    else:
        st.info("Aún no hay ventas registradas.")

# ==============================================================================
# VISTA: RESEÑAS
# ==============================================================================
elif menu == "✍️ Dejar Reseña":
    st.title("💬 El Muro de los Vecinos")
    with st.form("reseña"):
        n_res = st.text_input("Tu nombre"); m_res = st.text_area("Cuéntanos tu experiencia")
        if st.form_submit_button("Publicar Reseña"):
            conn = get_db(); c = conn.cursor()
            c.execute("INSERT INTO resenas (cliente, mensaje, fecha) VALUES (?,?,?)", 
                      (n_res, m_res, get_peru_time().strftime("%d/%m/%Y")))
            conn.commit(); conn.close(); st.success("¡Gracias por tu comentario!"); st.rerun()
    
    conn = get_db(); df_res = pd.read_sql_query("SELECT * FROM resenas ORDER BY id DESC", conn); conn.close()
    for _, r in df_res.iterrows():
        st.info(f"👤 **{r['cliente']}** ({r['fecha']}): {r['mensaje']}")