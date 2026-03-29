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

# Estilos CSS - Tu diseño original de 561 líneas
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
    
    /* --- ESTILOS PARA PESTAÑAS (TABS) MEJORADAS --- */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
        display: flex;
        justify-content: center;
        background-color: rgba(0, 0, 0, 0.05);
        padding: 8px;
        border-radius: 20px;
        margin-bottom: 20px;
    }

    .stTabs [data-baseweb="tab"] {
        height: 80px; /* Altura considerable para fácil acceso */
        width: 100%;
        min-width: 180px;
        background-color: #f0f2f6;
        border-radius: 15px !important;
        margin: 5px;
        border: 2px solid transparent;
        transition: all 0.3s ease;
        box-shadow: 0px 2px 5px rgba(0,0,0,0.1);
    }

    .stTabs [data-baseweb="tab"] p {
        font-size: 22px !important; /* Texto grande y legible */
        font-weight: 800 !important;
        color: #31333F !important;
        text-transform: uppercase;
    }

    /* Pestaña activa (Seleccionada) */
    .stTabs [aria-selected="true"] {
        background-color: #FF4500 !important; /* Naranja fuerte de la marca */
        border: 3px solid white !important;
        box-shadow: 0px 5px 15px rgba(0,0,0,0.3);
        transform: translateY(-3px);
    }

    .stTabs [aria-selected="true"] p {
        color: white !important;
    }

    /* --- AJUSTES RESPONSIVOS (CELULARES) --- */
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
        .stTabs [data-baseweb="tab"] {
            height: 70px;
            min-width: 130px;
        }
        .stTabs [data-baseweb="tab"] p {
            font-size: 16px !important; /* Ajuste para evitar desbordamiento */
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
# Reemplazo de SQLite por GSheets manteniendo la misma lógica de acceso
conn_gs = st.connection("gsheets", type=GSheetsConnection)

def load_data(worksheet):
    try:
        return conn_gs.read(worksheet=worksheet, ttl=0)
    except Exception:
        # En caso de que la pestaña no exista todavía en el setup inicial
        return pd.DataFrame()

def update_data(df, worksheet):
    conn_gs.update(worksheet=worksheet, data=df)
    st.cache_data.clear()

# Directorios para persistencia de medios (en local/git)
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

# --- 5. SIDEBAR ---
with st.sidebar:
    # Usando el nombre del archivo exacto que proporcionaste
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
    st.caption(f"Versión 2.5 - {get_peru_time().strftime('%Y')}")
    if st.button("🗑️ Vaciar Carrito"):
        st.session_state.carrito = []
        st.rerun()

# ==============================================================================
# VISTA: TIENDA ONLINE (LÓGICA COMPLETA)
# ==============================================================================
if menu == "🛒 Tienda Online":
    notificacion_simulada()

    # --- 1. BOTÓN FLOTANTE (REDIRECCIÓN AL RESUMEN) ---
    if st.session_state.carrito and not st.session_state.pedido_exitoso:
        cant_items = len(st.session_state.carrito)
        st.markdown(f"""
            <style>
            .floating-cart {{
                position: fixed; bottom: 85px; right: 20px; z-index: 999;
                background: #FF4500; color: white; padding: 15px 20px;
                border-radius: 50px; text-decoration: none !important; font-weight: bold;
                box-shadow: 2px 4px 10px rgba(0,0,0,0.3); border: 2px solid white;
                display: flex; align-items: center; transition: 0.3s;
            }}
            .floating-cart:hover {{ transform: scale(1.05); color: white; }}
            </style>
            <a href="#mi-pedido" class="floating-cart">
                <span>🛒 VER MI RESUMEN ({cant_items})</span>
            </a>
        """, unsafe_allow_html=True)

    # --- 2. PANTALLA DE ÉXITO Y SEGUIMIENTO POST-ENVÍO ---
    if st.session_state.pedido_exitoso:
        st.balloons()
        st.success("## ✅ ¡Pedido recibido con éxito!")
        st.markdown(f"""
            ### Pasos a seguir:
            1. Haz clic en el botón verde de abajo para avisarnos por WhatsApp.
            2. La vecina confirmará tu pedido en unos minutos.
            3. ¡Prepara el hambre! 😋
        """)
        st.markdown(f'<a href="https://wa.me/51963142733?text=Hola%20JorPao!%20Acabo%20de%20hacer%20un%20pedido%20en%20la%20web.%20Mi%20nombre%20es%20{st.session_state.nombre_usuario}" target="_blank"><button style="width:100%;height:60px;background:#25D366;color:white;border:none;border-radius:15px;font-weight:bold;font-size:18px;cursor:pointer;">🟢 ENVIAR WHATSAPP DE CONFIRMACIÓN</button></a>', unsafe_allow_html=True)
        
        # Nueva opción para ver el pedido solicitado después de enviar
        if st.button("📋 Ver resumen de mi pedido solicitado", use_container_width=True):
            st.session_state.mostrar_detalle_ultimo = True
        
        if st.session_state.get('mostrar_detalle_ultimo'):
            try:
                df_ultimo = pd.read_json(st.session_state.ultimo_pedido_json)
                with st.expander("📝 Detalle de tu pedido enviado", expanded=True):
                    for _, item in df_ultimo.iterrows():
                        st.write(f"• {item['nombre']} - S/ {float(item['venta']):.2f}")
                    st.divider()
                    st.write(f"**Total pagado: S/ {df_ultimo['venta'].astype(float).sum() + 2.0:.2f}**")
            except:
                st.info("Tu pedido ya está en proceso.")

        if st.button("⬅️ Regresar a la Vitrina"): 
            st.session_state.pedido_exitoso = False
            st.session_state.mostrar_detalle_ultimo = False
            st.rerun()
        st.stop()

    tab_tienda, tab_carrito = st.tabs(["🛍️ VER VITRINA", "🛒 MI PEDIDO"])

    with tab_tienda:
        # Widget de Clima
        tit_clima, cat_sug, msg_clima = obtener_sugerencia_clima()
        st.markdown(f"""
            <div class="clima-section">
                <h3 style="margin:0; color:#E65100;">{tit_clima}</h3>
                <p class="sugerencia-texto" style="margin:5px 0 0 0; font-size:1.1em; color:#444;"><b>Sugerencia de la Vecina:</b> {msg_clima}</p>
            </div>
        """, unsafe_allow_html=True)

        # Datos del Cliente
        col_u1, col_u2 = st.columns(2)
        with col_u1:
            st.session_state.nombre_usuario = st.text_input("¿Cómo te llamas, vecino/a?", value=st.session_state.nombre_usuario)
        with col_u2:
            zona = st.selectbox("📍 ¿Dónde te encuentras?", ["Selecciona...", "Residencial Aeropuerto", "Playa Rímac", "Otro (Consultar por WA)"])
        
        if zona == "Otro (Consultar por WA)": 
            st.warning("⚠️ El delivery automático es solo para Aeropuerto y Playa Rímac. Para otras zonas, coordina por WhatsApp."); st.stop()
        elif zona == "Selecciona...": 
            st.info("Selecciona tu zona para ver los productos disponibles."); st.stop()

        # Sección de Combos
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
                            st.session_state.carrito.append({'id': f"C-{c['id']}", 'nombre': f"COMBO: {c['nombre_combo']}", 'venta': float(c['precio_combo']), 'costo': 0, 'imagen_path': ""})
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
        # Ancla para el botón flotante
        st.markdown('<div id="mi-pedido"></div>', unsafe_allow_html=True)
        if st.session_state.carrito:
            st.markdown("### 🛒 Tu Lista de Antojitos")
            
            for index, row in enumerate(st.session_state.carrito):
                with st.container(border=True):
                    col_img, col_info, col_p, col_x = st.columns([1, 2, 1, 1])
                    img_c = row.get('imagen_path', "")
                    if img_c and os.path.exists(str(img_c)):
                        col_img.image(img_c, width=60)
                    else:
                        col_img.markdown("🍪")
                    
                    col_info.write(f"**{row['nombre']}**")
                    col_p.write(f"S/ {float(row['venta']):.2f}")
                    if col_x.button("❌", key=f"rem_{index}"):
                        st.session_state.carrito.pop(index)
                        st.rerun()

            # Cálculos
            df_cart = pd.DataFrame(st.session_state.carrito)
            delivery_cost = 2.0
            subtotal = df_cart['venta'].astype(float).sum()
            total = subtotal + delivery_cost

            st.markdown("---")
            st.markdown(f"**Subtotal:** S/ {subtotal:.2f} | **Delivery:** S/ {delivery_cost:.2f}")
            st.markdown(f"## **Total: S/ {total:.2f}**")

            with st.container(border=True):
                st.subheader("📝 Datos Finales")
                u_cel = st.text_input("Tu número de Celular", max_chars=9, placeholder="999888777")
                u_dir = st.text_area("Dirección exacta / Nro Dpto / Referencia")
                
                metodo = st.radio("¿Cómo deseas pagar?", ["Yape / Plin", "Efectivo"], horizontal=True)
                cap_pago = None
                vuelto_de = 0
                
                if metodo == "Yape / Plin":
                    st.markdown("""
                        <div style="background:#00D1B2; color:white; padding:15px; border-radius:10px; text-align:center;">
                            <b>Yape/Plin al: 963 142 733</b><br>A nombre de: Paula Ottiniano
                        </div>
                    """, unsafe_allow_html=True)
                    cap_pago = st.file_uploader("Sube una captura de tu pago para agilizar", type=['png','jpg','jpeg'])
                else:
                    vuelto_de = st.number_input("¿Con cuánto pagarás? (Para llevarte vuelto)", min_value=total)

                # --- RESUMEN DE CONFIRMACIÓN ANTES DEL BOTÓN ---
                st.info(f"💡 Vecino/a, vas a pedir **{len(st.session_state.carrito)} productos**. El total es **S/ {total:.2f}**.")

                if st.button("🚀 CONFIRMAR Y ENVIAR PEDIDO", type="primary", use_container_width=True):
                    if not u_cel or not u_dir or len(u_cel) < 9:
                        st.error("Por favor, completa tu celular (9 dígitos) y dirección correctamente.")
                    else:
                        # Guardar copia del pedido para seguimiento post-compra
                        st.session_state.ultimo_pedido_json = df_cart.to_json(orient='records')
                        
                        # Guardar captura si existe
                        p_path = ""
                        if cap_pago:
                            if not os.path.exists("capturas_yape"): os.makedirs("capturas_yape")
                            p_path = f"capturas_yape/p_{u_cel}_{get_peru_time().strftime('%H%M%S')}.png"
                            with open(p_path, "wb") as f: f.write(cap_pago.getbuffer())
                        
                        # Guardar en GSheets
                        df_pedidos_all = load_data("pedidos")
                        nuevo_id = int(df_pedidos_all['id'].max() + 1) if not df_pedidos_all.empty else 1
                        
                        try:
                            ganancia_prod = (df_cart['venta'].astype(float) - df_cart['costo'].astype(float)).sum()
                            ganancia_final = ganancia_prod + delivery_cost
                        except:
                            ganancia_final = delivery_cost
                            
                        nuevo_pedido = pd.DataFrame([{
                            "id": nuevo_id, 
                            "fecha": get_peru_time().strftime("%Y-%m-%d %H:%M"),
                            "cliente": st.session_state.nombre_usuario, 
                            "celular": u_cel, 
                            "direccion": u_dir, 
                            "zona": zona,
                            "productos_json": st.session_state.ultimo_pedido_json, 
                            "total": total,
                            "ganancia": ganancia_final, 
                            "metodo_pago": metodo, 
                            "monto_pagado": vuelto_de,
                            "captura_pago": p_path, 
                            "estado": "Nuevo"
                        }])
                        
                        update_data(pd.concat([df_pedidos_all, nuevo_pedido], ignore_index=True), "pedidos")
                        
                        # Actualizar Stock
                        df_prods_upd = load_data("productos")
                        for pid in df_cart['id']:
                            if str(pid).isdigit():
                                df_prods_upd.loc[df_prods_upd['id'] == int(pid), 'stock'] -= 1
                        update_data(df_prods_upd, "productos")
                        
                        st.session_state.carrito = []
                        st.session_state.pedido_exitoso = True
                        st.rerun()
        else:
            st.info("Tu carrito está vacío. ¡Mira nuestra vitrina y elige algo rico!")

# ==============================================================================
# VISTA: GESTIÓN DE INVENTARIO (ADMIN)
# ==============================================================================
elif menu == "⚙️ Gestión de Inventario" and is_admin:
    st.header("⚙️ Gestión de Inventario")
    
    t_stock, t_add, t_cat = st.tabs(["Stock Actual", "Añadir Producto", "Categorías"])
    
    with t_stock:
        df_inv = load_data("productos")
        if not df_inv.empty:
            st.subheader("Editar Productos en Vivo")
            df_edit = st.data_editor(df_inv, num_rows="dynamic")
            if st.button("Guardar Cambios en Inventario"):
                update_data(df_edit, "productos")
                st.success("¡Base de datos de productos actualizada!")
        else:
            st.write("No hay productos registrados.")

    with t_add:
        with st.form("nuevo_prod_form"):
            col_f1, col_f2 = st.columns(2)
            n_name = col_f1.text_input("Nombre del Producto")
            df_c_list = load_data("categorias")
            n_cat = col_f2.selectbox("Categoría", df_c_list['nombre'].tolist() if not df_c_list.empty else ["Sin categorías"])
            
            col_f3, col_f4, col_f5 = st.columns(3)
            n_costo = col_f3.number_input("Costo de Compra (S/)", min_value=0.0)
            n_venta = col_f4.number_input("Precio de Venta (S/)", min_value=0.0)
            n_stock = col_f5.number_input("Stock Inicial", min_value=0, step=1)
            
            n_img = st.file_uploader("Imagen del Producto", type=['png','jpg','jpeg'])
            
            if st.form_submit_button("Registrar Producto"):
                if n_name:
                    path_img = ""
                    if n_img:
                        path_img = f"img_productos/{n_name.replace(' ','_')}.png"
                        with open(path_img, "wb") as f: f.write(n_img.getbuffer())
                    
                    df_actual = load_data("productos")
                    next_id = int(df_actual['id'].max() + 1) if not df_actual.empty else 1
                    
                    nuevo_p = pd.DataFrame([{
                        "id": next_id, "nombre": n_name, "categoria": n_cat, 
                        "costo": n_costo, "venta": n_venta, "stock": n_stock, 
                        "imagen_path": path_img
                    }])
                    update_data(pd.concat([df_actual, nuevo_p], ignore_index=True), "productos")
                    st.success(f"Producto '{n_name}' registrado.")
                else:
                    st.error("El nombre es obligatorio.")

    with t_cat:
        st.subheader("Categorías Disponibles")
        df_c_admin = load_data("categorias")
        st.dataframe(df_c_admin, use_container_width=True)
        
        with st.form("nueva_cat"):
            new_cat_name = st.text_input("Nombre de Nueva Categoría")
            if st.form_submit_button("Añadir Categoría"):
                if new_cat_name:
                    next_cid = int(df_c_admin['id'].max() + 1) if not df_c_admin.empty else 1
                    df_c_admin = pd.concat([df_c_admin, pd.DataFrame([{"id": next_cid, "nombre": new_cat_name}])], ignore_index=True)
                    update_data(df_c_admin, "categorias")
                    st.rerun()

# ==============================================================================
# VISTA: REPORTES Y BANDEJA (ADMIN)
# ==============================================================================
elif menu == "📊 Análisis y Reportes" and is_admin:
    st.header("📊 Análisis de Ventas")
    df_v = load_data("pedidos")
    
    if not df_v.empty:
        # --- LIMPIEZA AUTOMÁTICA DE PRUEBAS ---
        antes_limpieza = len(df_v)
        df_v = df_v[~df_v['cliente'].str.lower().str.strip().isin(['prueba', 'pruebas'])]
        if len(df_v) < antes_limpieza:
            update_data(df_v, "pedidos")
            st.rerun()

        # Conversión de datos
        df_v['total'] = df_v['total'].astype(float)
        df_v['ganancia'] = df_v['ganancia'].astype(float)
        
        # --- CÁLCULO DE GANANCIA CORRECTO ---
        # Sumamos la ganancia de productos guardada + S/ 2.00 por cada fila (pedido)
        ganancia_productos = df_v['ganancia'].sum()
        ganancia_delivery = len(df_v) * 2.0
        ganancia_total_real = ganancia_productos + ganancia_delivery
        
        # Métricas
        m1, m2, m3, m4 = st.columns(4)
        total_ventas = df_v['total'].sum()
        m1.metric("Ventas Totales", f"S/ {total_ventas:.2f}")
        
        porcentaje_rentabilidad = (ganancia_total_real / total_ventas * 100) if total_ventas > 0 else 0
        m2.metric("Ganancia Total", f"S/ {ganancia_total_real:.2f}", delta=f"{porcentaje_rentabilidad:.1f}%")
        
        m3.metric("Pedidos", len(df_v))
        m4.metric("Ticket Promedio", f"S/ {df_v['total'].mean():.2f}")

        # --- NUEVO GRÁFICO CIRCULAR (PORCENTAJES) ---
        st.subheader("🍕 Distribución de Ventas")
        
        # Extraemos los nombres de productos de todos los JSON para el gráfico
        lista_nombres = []
        for p_json in df_v['productos_json']:
            try:
                items = json.loads(p_json)
                for it in items:
                    lista_nombres.append(it['nombre'])
            except:
                continue
        
        if lista_nombres:
            df_pie = pd.Series(lista_nombres).value_counts().reset_index()
            df_pie.columns = ['Producto', 'Cantidad']
            
            # Usamos plotly para un gráfico redondo profesional
            import plotly.express as px
            fig = px.pie(df_pie, values='Cantidad', names='Producto', 
                         hole=0.4, # Lo hace tipo "Donut" que es más moderno
                         color_discrete_sequence=px.colors.sequential.OrRd_r)
            fig.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No hay suficientes datos para generar el gráfico circular.")

        # Bandeja de Pedidos Activos
        st.subheader("🔔 Bandeja de Pedidos Activos")
        pendientes = df_v[df_v['estado'] == 'Nuevo'].sort_values('id', ascending=False)
        
        if pendientes.empty:
            st.success("¡No hay pedidos pendientes!")
        else:
            for _, ped in pendientes.iterrows():
                with st.container(border=True):
                    c_info, c_accion = st.columns([3, 1])
                    c_info.markdown(f"**Pedido #{ped['id']} - {ped['cliente']}**")
                    c_info.write(f"📍 {ped['direccion']} | 📱 {ped['celular']}")
                    c_info.write(f"💰 S/ {ped['total']} ({ped['metodo_pago']})")
                    
                    if c_accion.button(f"Entregado ✅", key=f"btn_ent_{ped['id']}", use_container_width=True):
                        df_v.loc[df_v['id'] == ped['id'], 'estado'] = 'Entregado'
                        update_data(df_v, "pedidos")
                        st.rerun()
                    
                    if c_accion.button(f"Eliminar 🗑️", key=f"btn_del_{ped['id']}", use_container_width=True):
                        df_v = df_v[df_v['id'] != ped['id']]
                        update_data(df_v, "pedidos")
                        st.rerun()

        st.markdown("---")
        st.subheader("📥 Exportar Reporte")
        st.download_button("Descargar Excel", data=to_excel(df_v), 
                           file_name=f"ventas_jorpao_{get_peru_time().strftime('%Y%m%d')}.xlsx",
                           use_container_width=True)
    else:
        st.info("Aún no hay datos de ventas.")

# ==============================================================================
# VISTA: COMBOS (ADMIN)
# ==============================================================================
elif menu == "🎁 Gestionar Combos" and is_admin:
    st.header("🎁 Configuración de Combos")
    
    with st.container(border=True):
        st.subheader("Crear Nuevo Combo")
        c_n = st.text_input("Nombre del Combo (Ej: Combo Peliculero)")
        c_p = st.number_input("Precio del Combo", min_value=0.0)
        
        st.write("Añadir productos al combo:")
        df_p_sel = load_data("productos")
        col_ps, col_pc, col_pb = st.columns([3, 1, 1])
        
        sel_p = col_ps.selectbox("Producto", df_p_sel['nombre'].tolist() if not df_p_sel.empty else [])
        sel_c = col_pc.number_input("Cant.", min_value=1, value=1)
        
        if col_pb.button("➕"):
            st.session_state.temp_combo_items.append(f"{sel_c}x {sel_p}")
            
        if st.session_state.temp_combo_items:
            st.write("**Lista actual:** " + " + ".join(st.session_state.temp_combo_items))
            if st.button("Limpiar lista"): st.session_state.temp_combo_items = []
        
        if st.button("Guardar Combo"):
            if c_n and st.session_state.temp_combo_items:
                df_combos_act = load_data("combos")
                nid = int(df_combos_act['id'].max() + 1) if not df_combos_act.empty else 1
                receta = ", ".join(st.session_state.temp_combo_items)
                new_c = pd.DataFrame([{"id": nid, "nombre_combo": c_n, "productos_ids": receta, "precio_combo": c_p, "activo": 1}])
                update_data(pd.concat([df_combos_act, new_c], ignore_index=True), "combos")
                st.session_state.temp_combo_items = []
                st.success("¡Combo registrado!")
                st.rerun()

# ==============================================================================
# VISTA: RESEÑAS
# ==============================================================================
elif menu == "✍️ Dejar Reseña":
    st.title("💬 Comentarios de nuestros Vecinos")
    
    with st.form("form_resena"):
        st.write("¿Qué te pareció tu antojito?")
        r_nom = st.text_input("Nombre")
        r_msg = st.text_area("Comentario")
        r_star = st.slider("Calificación", 1, 5, 5)
        
        if st.form_submit_button("Publicar"):
            if r_nom and r_msg:
                df_res_act = load_data("resenas")
                rid = int(df_res_act['id'].max() + 1) if not df_res_act.empty else 1
                new_r = pd.DataFrame([{
                    "id": rid, "cliente": r_nom, "mensaje": r_msg, 
                    "fecha": get_peru_time().strftime("%d/%m/%Y")
                }])
                update_data(pd.concat([df_res_act, new_r], ignore_index=True), "resenas")
                st.success("¡Gracias por tu comentario!")
                st.rerun()

    st.markdown("---")
    df_res_ver = load_data("resenas")
    if not df_res_ver.empty:
        for _, r in df_res_ver.sort_values('id', ascending=False).iterrows():
            st.markdown(f"""
                <div style="background:white; padding:15px; border-radius:15px; margin-bottom:10px; color:#333; border-left:5px solid #FFD700;">
                    <b>{r['cliente']}</b> <small>({r['fecha']})</small><br>
                    {r['mensaje']}
                </div>
            """, unsafe_allow_html=True)

# ==============================================================================
# VISTA: COMPROBANTES (ADMIN)
# ==============================================================================
elif menu == "📸 Ver Comprobantes" and is_admin:
    st.header("📸 Galería de Pagos Yape/Plin")
    df_img = load_data("pedidos")
    df_img = df_img[df_img['captura_pago'] != ""]
    
    if not df_img.empty:
        for _, row in df_img.iterrows():
            with st.container(border=True):
                st.write(f"Pedido #{row['id']} - {row['cliente']}")
                if os.path.exists(str(row['captura_pago'])):
                    st.image(row['captura_pago'], width=300)
                else:
                    st.error("Archivo no encontrado en el servidor.")
    else:
        st.write("No hay capturas de pantalla registradas.")