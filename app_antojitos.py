import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
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

# Estilos CSS - Tu diseño original
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
        margin-bottom: 10px;
        line-height: 1.1;
    }
    
    @media (max-width: 600px) {
        .main-title {
            font-size: 38px !important;
            margin-top: -30px !important;
            margin-bottom: 5px !important;
            word-break: keep-all !important;
        }
        .subtitle { 
            font-size: 13px !important; 
            margin-top: 0px !important; 
        }
        .sugerencia-texto {
            color: #262730 !important;
        }
    }
    
    .subtitle {
        font-family: 'Inter', sans-serif;
        color: #FFFFFF;
        font-weight: bold;
        text-align: center;
        font-size: 18px;
        margin-top: -10px;
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
        transition: transform 0.2s;
    }
    .product-card:hover {
        transform: translateY(-5px);
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
        height: 45px;
    }
    .stButton>button:hover { background-color: #E63900; transform: scale(1.02); }

    .clima-section {
        background: white; 
        padding: 20px; 
        border-radius: 20px; 
        border-left: 10px solid #FF8C00; 
        margin-bottom: 25px;
    }

    .floating-cart {
        position: fixed;
        bottom: 20px;
        right: 20px;
        background-color: #FF4500;
        color: white !important;
        padding: 15px 25px;
        border-radius: 50px;
        box-shadow: 0px 4px 20px rgba(0,0,0,0.4);
        z-index: 9999;
        text-decoration: none;
        font-weight: bold;
        display: flex;
        align-items: center;
        gap: 12px;
        border: 2px solid white;
        transition: 0.3s;
    }
    .floating-cart:hover {
        transform: scale(1.1);
        background-color: #E63900;
    }
    </style>
    
    <div class="main-title">ANTOJITOS JORPAO</div>
    <div class="subtitle">¡ENDULZAMOS TU DIA, VECINO/A!</div>
""", unsafe_allow_html=True)

# --- 2. GESTIÓN DE PERSISTENCIA (GOOGLE SHEETS) ---
conn_gs = st.connection("gsheets", type=GSheetsConnection)

def load_data(worksheet):
    try:
        return conn_gs.read(worksheet=worksheet, ttl=0)
    except Exception:
        return pd.DataFrame()

def update_data(df, worksheet):
    conn_gs.update(worksheet=worksheet, data=df)
    st.cache_data.clear()

if not os.path.exists("img_productos"): os.makedirs("img_productos")
if not os.path.exists("capturas_yape"): os.makedirs("capturas_yape")

# --- 3. FUNCIONES DE LÓGICA DE NEGOCIO ---
def obtener_sugerencia_clima():
    hora = get_peru_time().hour
    if 10 <= hora <= 17:
        return "🔥 ¡Está haciendo un calor fuerte!", "Bebidas", "Nada como una bebida heladita para la sed. ¡Pídela al polo!"
    elif 18 <= hora <= 23:
        return "☁️ El clima está refrescando.", "Snacks", "Para calentar el cuerpo, un snack saladito o algo contundente."
    else:
        return "🌤️ El clima está templado.", "Dulces", "Perfecto para un antojito dulce antes de terminar el día."

def notificacion_simulada():
    nombres = ["Gerson", "Jorge", "Ricardo", "Vanessa", "Don Lucho", "Ana", "Beto", "Anthony", "Cesar", "José", "Daniel", "Milagros", "Elena"]
    zonas = ["Playa Rímac", "Res. Aeropuerto", "Santa Rosa", "Gambetta", "Carmen de la Legua", "Smp", "Faucett"]
    if random.random() < 0.15:
        st.toast(f"🛍️ {random.choice(nombres)} de {random.choice(zonas)} acaba de comprar un antojito.", icon="🔥")

def to_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Reporte_Ventas')
    return output.getvalue()

# --- 4. ESTADO DE SESIÓN ---
if 'carrito' not in st.session_state: st.session_state.carrito = []
if 'nombre_usuario' not in st.session_state: st.session_state.nombre_usuario = ""
if 'pedido_exitoso' not in st.session_state: st.session_state.pedido_exitoso = False
if 'temp_combo_items' not in st.session_state: st.session_state.temp_combo_items = []
if 'form_submitted' not in st.session_state: st.session_state.form_submitted = False
if 'ultimo_pedido_id' not in st.session_state: st.session_state.ultimo_pedido_id = None

# --- 5. SIDEBAR ---
with st.sidebar:
    if os.path.exists("logo.png"): 
        st.image("logo.png", use_container_width=True)
    
    st.markdown("### 🏰 Menú Principal")
    pwd = st.text_input("🔑 Panel Administrativo", type="password", help="Solo para la vecina JorPao")
    
    opciones = ["🛒 Tienda Online", "✍️ Dejar Reseña"]
    is_admin = False
    if pwd == "jyp2026.": 
        is_admin = True
        opciones.extend(["⚙️ Gestión de Inventario", "📊 Análisis y Reportes", "🎁 Gestionar Combos", "📸 Ver Comprobantes"])
    
    menu = st.radio("Ir a:", opciones)
    
    st.markdown("---")
    st.caption(f"Versión 2.7 - {get_peru_time().strftime('%Y')}")
    if st.button("🗑️ Vaciar Carrito"):
        st.session_state.carrito = []
        st.rerun()

# ==============================================================================
# VISTA: TIENDA ONLINE
# ==============================================================================
if menu == "🛒 Tienda Online":
    notificacion_simulada()

    if st.session_state.carrito:
        cant_items = len(st.session_state.carrito)
        st.markdown(f"""
            <a href="#mi-pedido" class="floating-cart">
                <span>🛒 VER MI PEDIDO ({cant_items})</span>
            </a>
        """, unsafe_allow_html=True)

    if st.session_state.pedido_exitoso:
        st.balloons()
        st.success("## ✅ ¡Pedido recibido con éxito!")
        st.markdown(f'<a href="https://wa.me/51963142733?text=Hola%20JorPao!%20Acabo%20de%20hacer%20un%20pedido%20en%20la%20web.%20Mi%20nombre%20es%20{st.session_state.nombre_usuario}" target="_blank"><button style="width:100%;height:60px;background:#25D366;color:white;border:none;border-radius:15px;font-weight:bold;font-size:18px;cursor:pointer;">🟢 ENVIAR WHATSAPP DE CONFIRMACIÓN</button></a>', unsafe_allow_html=True)
        if st.button("⬅️ Regresar a la Vitrina"): 
            st.session_state.pedido_exitoso = False
            st.rerun()
        st.stop()

    tab_tienda, tab_carrito = st.tabs(["🛍️ VER VITRINA", "🛒 MI PEDIDO"])

    with tab_tienda:
        tit_clima, cat_sug, msg_clima = obtener_sugerencia_clima()
        st.markdown(f"""
            <div class="clima-section">
                <h3 style="margin:0; color:#E65100;">{tit_clima}</h3>
                <p class="sugerencia-texto" style="margin:5px 0 0 0; font-size:1.1em; color:#444;"><b>Sugerencia de la Vecina:</b> {msg_clima}</p>
            </div>
        """, unsafe_allow_html=True)

        col_u1, col_u2 = st.columns(2)
        with col_u1:
            st.session_state.nombre_usuario = st.text_input("¿Cómo te llamas, vecino/a?", value=st.session_state.nombre_usuario)
        with col_u2:
            zona = st.selectbox("📍 ¿Dónde te encuentras?", ["Selecciona...", "Residencial Aeropuerto", "Playa Rímac", "Otro (Consultar por WA)"])
        
        if zona == "Otro (Consultar por WA)": 
            st.warning("⚠️ El delivery automático es solo para Aeropuerto y Playa Rímac. Para otras zonas, coordina por WhatsApp."); st.stop()
        elif zona == "Selecciona...": 
            st.info("Selecciona tu zona para ver los productos disponibles."); st.stop()

        # Combos con campo de ganancia neta manual
        df_combos = load_data("combos")
        if not df_combos.empty:
            df_combos = df_combos[df_combos['activo'] == 1]
            if not df_combos.empty:
                st.subheader("🎁 Super Combos JorPao")
                cols_c = st.columns(2)
                for idx, (_, c) in enumerate(df_combos.iterrows()):
                    with cols_c[idx % 2]:
                        st.markdown(f"""
                        <div class="product-card" style="border: 2px solid #FFD700; background: #FFFDE7;">
                            <h4 style="margin:0; color:#FF4500;">{c['nombre_combo']}</h4>
                            <p style="margin:5px 0; font-size: 0.9em; color: #555;">Incluye: {c['productos_ids']}</p>
                            <p style="font-weight:bold; font-size:1.3em; color: #2E7D32;">S/ {float(c['precio_combo']):.2f}</p>
                        </div>
                        """, unsafe_allow_html=True)
                        if st.button(f"Pedir {c['nombre_combo']}", key=f"btn_c_{c['id']}", use_container_width=True):
                            # Se hereda ganancia_neta si existe en el sheet
                            gn = float(c['ganancia_neta']) if 'ganancia_neta' in c else 0
                            st.session_state.carrito.append({
                                'id': f"C-{c['id']}", 'nombre': f"COMBO: {c['nombre_combo']}", 
                                'venta': float(c['precio_combo']), 'costo': float(c['precio_combo']) - gn,
                                'imagen_path': None
                            })
                            st.toast(f"¡{c['nombre_combo']} al carrito!")

        # Categorías y Productos
        df_cats = load_data("categorias")
        df_p = load_data("productos")
        
        if not df_p.empty:
            df_p = df_p[df_p['stock'].astype(int) > 0]
            st.subheader("🍨 Nuestra Vitrina")
            
            for _, cat in df_cats.iterrows():
                prods_cat = df_p[df_p['categoria'] == cat['nombre']]
                if not prods_cat.empty:
                    with st.expander(f"✨ {cat['nombre'].upper()}", expanded=(cat['nombre'] == cat_sug)):
                        for _, p in prods_cat.iterrows():
                            st.markdown('<div class="product-card">', unsafe_allow_html=True)
                            c1, c2, c3 = st.columns([1, 2, 1])
                            img_p = p['imagen_path'] if p['imagen_path'] and os.path.exists(str(p['imagen_path'])) else None
                            if img_p:
                                c1.image(img_p, width=120)
                            else:
                                c1.markdown("🖼️\n(Sin foto)")
                                
                            c2.markdown(f"### {p['nombre']}")
                            c2.markdown(f"**Precio: S/ {float(p['venta']):.2f}**")
                            c2.caption(f"Quedan: {int(p['stock'])} unidades")
                            
                            if c3.button("Añadir ➕", key=f"add_{p['id']}", use_container_width=True):
                                st.session_state.carrito.append(p.to_dict())
                                st.toast(f"✅ {p['nombre']} en carrito")
                            st.markdown('</div>', unsafe_allow_html=True)

    with tab_carrito:
        st.markdown('<div id="mi-pedido"></div>', unsafe_allow_html=True)
        
        # CONSULTA TEMPORAL DEL PEDIDO (Para que el cliente vea qué pidió)
        if st.session_state.ultimo_pedido_id:
            df_hist = load_data("pedidos")
            mi_p = df_hist[df_hist['id'] == st.session_state.ultimo_pedido_id]
            if not mi_p.empty:
                st.markdown("### 📄 Tu último pedido realizado")
                with st.container(border=True):
                    row_p = mi_p.iloc[0]
                    st.write(f"**Pedido #{row_p['id']}** - {row_p['estado']}")
                    items_p = json.loads(row_p['productos_json'])
                    for it in items_p:
                        st.write(f"• {it['nombre']} (S/ {float(it['venta']):.2f})")
                    st.write(f"**Total: S/ {float(row_p['total']):.2f}**")
                    
                    # Generar texto para descarga
                    txt_ticket = f"Antojitos JorPao - Pedido #{row_p['id']}\nCliente: {row_p['cliente']}\nTotal: S/ {row_p['total']}\nFecha: {row_p['fecha']}"
                    st.download_button("📥 Descargar Resumen (TXT)", txt_ticket, file_name=f"pedido_{row_p['id']}.txt")
                st.markdown("---")

        if st.session_state.carrito:
            st.markdown("### 🛒 Resumen de tu Compra")
            delivery_cost = 2.0
            
            # REDISEÑO ESTÉTICO DEL CARRITO
            for index, row in enumerate(st.session_state.carrito):
                with st.container(border=True):
                    col_img, col_txt, col_del = st.columns([1, 4, 1])
                    with col_img:
                        img_c = row.get('imagen_path')
                        if img_c and os.path.exists(str(img_c)): st.image(img_c, width=60)
                        else: st.markdown("📦")
                    with col_txt:
                        st.write(f"**{row['nombre']}**")
                        st.write(f"Precio: S/ {float(row['venta']):.2f}")
                    with col_del:
                        if st.button("🗑️", key=f"rem_{index}"):
                            st.session_state.carrito.pop(index)
                            st.rerun()

            subtotal = sum(float(it['venta']) for it in st.session_state.carrito)
            total = subtotal + delivery_cost
            
            st.markdown(f"**Subtotal:** S/ {subtotal:.2f} | **Delivery:** S/ {delivery_cost:.2f}")
            st.markdown(f"## **Total: S/ {total:.2f}**")

            with st.container(border=True):
                st.subheader("📝 Datos Finales")
                u_cel = st.text_input("Tu número de Celular", max_chars=9)
                u_dir = st.text_area("Dirección exacta / Nro Dpto / Referencia")
                metodo = st.radio("¿Cómo deseas pagar?", ["Yape / Plin", "Efectivo"])
                
                cap_pago = None
                vuelto_de = 0
                if metodo == "Yape / Plin":
                    st.markdown('<div style="background:#00D1B2; color:white; padding:10px; border-radius:10px; text-align:center;"><b>Yape/Plin: 963 142 733</b> (Paula Ottiniano)</div>', unsafe_allow_html=True)
                    cap_pago = st.file_uploader("Sube una captura de tu pago", type=['png','jpg','jpeg'])
                else:
                    vuelto_de = st.number_input("¿Con cuánto pagarás?", min_value=total)

                if st.button("🚀 CONFIRMAR Y ENVIAR PEDIDO", type="primary", use_container_width=True):
                    if not u_cel or not u_dir or len(u_cel) < 9:
                        st.error("Datos incompletos.")
                    else:
                        p_path = ""
                        if cap_pago:
                            p_path = f"capturas_yape/p_{u_cel}_{get_peru_time().strftime('%H%M%S')}.png"
                            with open(p_path, "wb") as f: f.write(cap_pago.getbuffer())
                        
                        df_pedidos_all = load_data("pedidos")
                        nuevo_id = int(df_pedidos_all['id'].max() + 1) if not df_pedidos_all.empty else 1
                        
                        # GANANCIA INCLUYE DELIVERY Y MANEJA COSTOS DE COMBOS
                        ganancia_p = sum(float(it['venta']) - float(it.get('costo', 0)) for it in st.session_state.carrito)
                        ganancia_total = ganancia_p + delivery_cost
                        
                        nuevo_pedido = pd.DataFrame([{
                            "id": nuevo_id, "fecha": get_peru_time().strftime("%Y-%m-%d %H:%M"),
                            "cliente": st.session_state.nombre_usuario, "celular": u_cel, 
                            "direccion": u_dir, "zona": zona, "total": total,
                            "productos_json": json.dumps(st.session_state.carrito), 
                            "ganancia": ganancia_total, "metodo_pago": metodo, 
                            "monto_pagado": vuelto_de, "captura_pago": p_path, "estado": "Nuevo"
                        }])
                        
                        update_data(pd.concat([df_pedidos_all, nuevo_pedido], ignore_index=True), "pedidos")
                        
                        # Actualizar Stock
                        df_prods_upd = load_data("productos")
                        for it in st.session_state.carrito:
                            if str(it.get('id')).isdigit():
                                df_prods_upd.loc[df_prods_upd['id'] == int(it['id']), 'stock'] -= 1
                        update_data(df_prods_upd, "productos")
                        
                        st.session_state.ultimo_pedido_id = nuevo_id
                        st.session_state.carrito = []
                        st.session_state.pedido_exitoso = True
                        st.rerun()
        elif not st.session_state.ultimo_pedido_id:
            st.info("Tu carrito está vacío.")

# ==============================================================================
# VISTA: GESTIÓN DE INVENTARIO (ADMIN)
# ==============================================================================
elif menu == "⚙️ Gestión de Inventario" and is_admin:
    st.header("⚙️ Gestión de Inventario")
    t_stock, t_add, t_cat = st.tabs(["Stock Actual", "Añadir Producto", "Categorías"])
    
    with t_stock:
        df_inv = load_data("productos")
        if not df_inv.empty:
            df_edit = st.data_editor(df_inv, num_rows="dynamic")
            if st.button("Guardar Cambios"):
                update_data(df_edit, "productos")
                st.success("Actualizado.")

    with t_add:
        with st.form("nuevo_prod"):
            n_name = st.text_input("Nombre")
            df_cl = load_data("categorias")
            n_cat = st.selectbox("Categoría", df_cl['nombre'].tolist() if not df_cl.empty else ["Sin categorías"])
            c1, c2, c3 = st.columns(3)
            n_costo = c1.number_input("Costo (S/)", 0.0)
            n_venta = c2.number_input("Venta (S/)", 0.0)
            n_stock = c3.number_input("Stock", 0, step=1)
            n_img = st.file_uploader("Imagen", type=['png','jpg','jpeg'])
            if st.form_submit_button("Registrar"):
                path_i = f"img_productos/{n_name.replace(' ','_')}.png" if n_img else ""
                if n_img:
                    with open(path_i, "wb") as f: f.write(n_img.getbuffer())
                df_act = load_data("productos")
                nid = int(df_act['id'].max() + 1) if not df_act.empty else 1
                new_p = pd.DataFrame([{"id": nid, "nombre": n_name, "categoria": n_cat, "costo": n_costo, "venta": n_venta, "stock": n_stock, "imagen_path": path_i}])
                update_data(pd.concat([df_act, new_p], ignore_index=True), "productos")
                st.success("Producto guardado.")

    with t_cat:
        df_ca = load_data("categorias")
        st.dataframe(df_ca)
        with st.form("nc"):
            nn = st.text_input("Nueva Categoría")
            if st.form_submit_button("Añadir"):
                if nn:
                    nid = int(df_ca['id'].max() + 1) if not df_ca.empty else 1
                    update_data(pd.concat([df_ca, pd.DataFrame([{"id": nid, "nombre": nn}])], ignore_index=True), "categorias")
                    st.rerun()

# ==============================================================================
# VISTA: REPORTES (ADMIN)
# ==============================================================================
elif menu == "📊 Análisis y Reportes" and is_admin:
    st.header("📊 Análisis de Ventas")
    df_v = load_data("pedidos")
    if not df_v.empty:
        df_v['total'] = df_v['total'].astype(float)
        df_v['ganancia'] = df_v['ganancia'].astype(float)
        m1, m2, m3 = st.columns(3)
        m1.metric("Ventas Totales", f"S/ {df_v['total'].sum():.2f}")
        m2.metric("Ganancia Neta (Inc. Delivery)", f"S/ {df_v['ganancia'].sum():.2f}")
        m3.metric("Pedidos", len(df_v))
        
        st.subheader("Pedidos Pendientes")
        pendientes = df_v[df_v['estado'] == 'Nuevo']
        for _, ped in pendientes.iterrows():
            with st.container(border=True):
                st.write(f"**#{ped['id']} - {ped['cliente']}** (S/ {ped['total']})")
                if st.button("Marcar Entregado ✅", key=f"ent_{ped['id']}"):
                    df_v.loc[df_v['id'] == ped['id'], 'estado'] = 'Entregado'
                    update_data(df_v, "pedidos")
                    st.rerun()
        st.download_button("Exportar Excel", to_excel(df_v), file_name="ventas.xlsx")

# ==============================================================================
# VISTA: COMBOS (ADMIN)
# ==============================================================================
elif menu == "🎁 Gestionar Combos" and is_admin:
    st.header("🎁 Configuración de Combos")
    with st.container(border=True):
        c_n = st.text_input("Nombre del Combo")
        c_p = st.number_input("Precio Venta", 0.0)
        c_g = st.number_input("Ganancia Neta por el Combo (S/)", 0.0, help="Digita cuánto ganas libre por este combo")
        
        df_ps = load_data("productos")
        col1, col2, col3 = st.columns([3, 1, 1])
        sel_p = col1.selectbox("Producto", df_ps['nombre'].tolist() if not df_ps.empty else [])
        sel_c = col2.number_input("Cant.", 1)
        if col3.button("➕"):
            st.session_state.temp_combo_items.append(f"{sel_c}x {sel_p}")
        
        if st.session_state.temp_combo_items:
            st.write("Lista: " + " + ".join(st.session_state.temp_combo_items))
            if st.button("Limpiar"): st.session_state.temp_combo_items = []
        
        if st.button("Guardar Combo"):
            df_co = load_data("combos")
            nid = int(df_co['id'].max() + 1) if not df_co.empty else 1
            new_c = pd.DataFrame([{
                "id": nid, "nombre_combo": c_n, "productos_ids": ", ".join(st.session_state.temp_combo_items), 
                "precio_combo": c_p, "ganancia_neta": c_g, "activo": 1
            }])
            update_data(pd.concat([df_co, new_c], ignore_index=True), "combos")
            st.session_state.temp_combo_items = []
            st.success("Combo Creado.")

# ==============================================================================
# VISTA: RESEÑAS
# ==============================================================================
elif menu == "✍️ Dejar Reseña":
    st.title("💬 Reseñas de Vecinos")
    with st.form("fr"):
        n = st.text_input("Nombre")
        m = st.text_area("Comentario")
        if st.form_submit_button("Publicar"):
            df_r = load_data("resenas")
            rid = int(df_r['id'].max() + 1) if not df_r.empty else 1
            update_data(pd.concat([df_r, pd.DataFrame([{"id": rid, "cliente": n, "mensaje": m, "fecha": get_peru_time().strftime("%d/%m/%Y")}])], ignore_index=True), "resenas")
            st.success("Gracias!")
    
    df_rv = load_data("resenas")
    if not df_rv.empty:
        for _, r in df_rv.sort_values('id', ascending=False).iterrows():
            st.markdown(f'<div style="background:white; padding:10px; border-radius:10px; margin-bottom:5px; color:#333;"><b>{r["cliente"]}</b>: {r["mensaje"]}</div>', unsafe_allow_html=True)

# ==============================================================================
# VISTA: COMPROBANTES (ADMIN)
# ==============================================================================
elif menu == "📸 Ver Comprobantes" and is_admin:
    st.header("📸 Galería de Pagos")
    df_im = load_data("pedidos")
    df_im = df_im[df_im['captura_pago'] != ""]
    for _, r in df_im.iterrows():
        with st.container(border=True):
            st.write(f"Pedido #{r['id']} - {r['cliente']}")
            if os.path.exists(str(r['captura_pago'])): st.image(r['captura_pago'], width=300)