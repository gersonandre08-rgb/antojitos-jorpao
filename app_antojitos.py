import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import json
import os
from datetime import datetime
import io
import random
import pytz
from streamlit_geolocation import streamlit_geolocation

def to_excel(df):
    output = io.BytesIO()
    # Usamos xlsxwriter para crear el archivo Excel en memoria
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Reporte')
    return output.getvalue()

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
    
    # 1. Definimos el costo de delivery (Editable solo si es Admin o dejarlo fuera si quieres que sea siempre visible)
    if pwd == "jyp2026.": 
        is_admin = True
        opciones.extend(["⚙️ Gestión de Inventario", "📊 Análisis y Reportes", "🎁 Gestionar Combos", "📸 Ver Comprobantes"])
        
        st.markdown("---")
        st.markdown("### ⚙️ Configuración Admin")
        # El valor se guarda en st.session_state para que persista entre menús
        costo_delivery = st.number_input(
            "Costo de Delivery (S/)", 
            min_value=0.0, 
            value=2.0, 
            step=0.5,
            help="Este valor afectará el total del carrito y los reportes de ganancia."
        )
    else:
        # Si no es admin, usamos el valor por defecto de 2.0
        costo_delivery = 2.0

    st.markdown("---")
    menu = st.radio("Ir a:", opciones)
    
    st.markdown("---")
    st.caption(f"Versión 1.5 - {get_peru_time().strftime('%Y')}")
    
    if st.button("🗑️ Vaciar Carrito"):
        st.session_state.carrito = []
        st.rerun()

# ==============================================================================
# VISTA: TIENDA ONLINE (LÓGICA COMPLETA)
# ==============================================================================
if menu == "🛒 Tienda Online":
    notificacion_simulada()

    # --- NUEVO: BOTÓN FLOTANTE DE WHATSAPP ---
    # Mensaje inicial basado en si hay algo en el carrito o no
    if st.session_state.carrito:
        texto_wa = f"Hola JorPao! 👋 Soy {st.session_state.nombre_usuario}. Tengo productos en mi carrito y me gustaría una atención personalizada."
    else:
        texto_wa = "Hola JorPao! 👋 Me gustaría hacer una consulta sobre los antojitos de hoy."
    
    phone_number = "51963142733"
    wa_url = f"https://wa.me/{phone_number}?text={texto_wa.replace(' ', '%20')}"

    st.markdown(f"""
        <style>
        .floating-whatsapp {{
            position: fixed; bottom: 20px; right: 20px; width: 60px; height: 60px;
            background-color: #25d366; color: #fff !important; border-radius: 50px;
            text-align: center; font-size: 30px; box-shadow: 2px 2px 3px #999;
            z-index: 1000; display: flex; align-items: center; justify-content: center;
            text-decoration: none !important; transition: all 0.3s ease;
        }}
        .floating-whatsapp:hover {{ transform: scale(1.1); background-color: #128c7e; }}
        .wa-tooltip {{
            position: fixed; bottom: 30px; right: 90px; background-color: #444;
            color: white; padding: 5px 15px; border-radius: 20px; font-size: 14px;
            z-index: 1000; font-family: sans-serif;
        }}
        </style>
        <div class="wa-tooltip">¿Consultas? ¡Escríbenos!</div>
        <a href="{wa_url}" class="floating-whatsapp" target="_blank">
            <svg style="width:35px;height:35px" viewBox="0 0 24 24">
                <path fill="currentColor" d="M12.04 2C6.5 2 2 6.5 2 12.04C2 13.81 2.46 15.53 3.33 17.04L2 22L7.13 20.69C8.59 21.5 10.23 21.93 11.91 21.93H11.96C17.5 21.93 22 17.43 22 11.91C22 9.23 20.96 6.72 19.05 4.81C17.14 2.89 14.71 2 12.04 2M12.05 3.67C14.25 3.67 16.31 4.53 17.87 6.09C19.44 7.65 20.3 9.72 20.3 11.91C20.3 16.5 16.56 20.24 11.97 20.24H11.93C10.5 20.24 9.11 19.88 7.87 19.19L7.58 19.04L4.5 19.84L5.33 16.88L5.15 16.59C4.41 15.41 4.03 14.06 4.03 12.04C4.03 7.63 7.63 4.03 12.05 3.67M8.67 7.91C8.47 7.45 8.27 7.45 8.08 7.45C7.93 7.45 7.76 7.45 7.58 7.45C7.41 7.45 7.14 7.5 6.91 7.76C6.67 8.03 6 8.65 6 9.92C6 11.19 6.92 12.41 7.05 12.58C7.17 12.75 8.84 15.45 11.46 16.5C12.08 16.75 12.57 16.91 12.95 17.03C13.57 17.23 14.13 17.2 14.58 17.13C15.08 17.06 16.13 16.5 16.35 15.88C16.57 15.26 16.57 14.74 16.5 14.63C16.44 14.53 16.3 14.47 16.08 14.36C15.86 14.25 14.79 13.73 14.59 13.66C14.39 13.59 14.25 13.55 14.1 13.77C13.96 13.99 13.55 14.47 13.42 14.61C13.3 14.75 13.17 14.77 12.95 14.66C12.73 14.55 12.02 14.32 11.18 13.57C10.52 12.98 10.08 12.25 9.95 12.03C9.82 11.81 9.94 11.69 10.05 11.58C10.15 11.48 10.26 11.33 10.37 11.21C10.47 11.09 10.5 11 10.58 10.83C10.66 10.67 10.62 10.5 10.56 10.39C10.5 10.28 10 9.07 9.81 8.61C9.62 8.15 9.42 8.21 9.28 8.21C9.14 8.21 8.97 8.21 8.8 8.21C8.63 8.21 8.36 8.27 8.12 8.54C7.88 8.81 7.21 9.5 7.21 10.84C7.21 12.18 8.19 13.47 8.33 13.67C8.47 13.87 10.21 16.56 12.91 17.63C13.55 17.89 14.03 18.05 14.41 18.17C15.06 18.37 15.64 18.34 16.11 18.27C16.63 18.2 17.72 17.61 17.95 16.96C18.18 16.31 18.18 15.76 18.11 15.65C18.04 15.54 17.9 15.48 17.68 15.37C17.46 15.26 16.34 14.71 16.14 14.64C15.94 14.57 15.8 14.53 15.65 14.75C15.5 14.97 15.08 15.46 14.95 15.6C14.83 15.74 14.7 15.76 14.48 15.65C14.26 15.54 13.55 15.31 12.71 14.56C12.05 13.97 11.61 13.24 11.48 13.02C11.35 12.8 11.47 12.68 11.58 12.57C11.68 12.47 11.79 12.32 11.9 12.2C12.01 12.08 12.04 11.99 12.12 11.82C12.2 11.66 12.16 11.49 12.1 11.38C12.04 11.27 11.54 10.06 11.35 9.6Z" />
            </svg>
        </a>
    """, unsafe_allow_html=True)

    # Pantalla de Éxito
    if st.session_state.pedido_exitoso:
        st.balloons()
        st.success("## ✅ ¡Pedido recibido con éxito!")
        st.markdown("""
            ### Pasos a seguir:
            1. Haz clic en el botón verde de abajo para avisarnos por WhatsApp.
            2. La vecina confirmará tu pedido en unos minutos.
            3. ¡Prepárate para disfrutar! 😋
        """)
        st.markdown(f'<a href="https://wa.me/51963142733?text=Hola%20JorPao!%20Acabo%20de%20hacer%20un%20pedido%20en%20la%20web.%20Mi%20nombre%20es%20{st.session_state.nombre_usuario}" target="_blank"><button style="width:100%;height:60px;background:#25D366;color:white;border:none;border-radius:15px;font-weight:bold;font-size:18px;cursor:pointer;">🟢 ENVIAR WHATSAPP DE CONFIRMACIÓN</button></a>', unsafe_allow_html=True)
        if st.button("⬅️ Regresar a la Vitrina"): 
            st.session_state.pedido_exitoso = False
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
        st.markdown('<div id="mi-pedido"></div>', unsafe_allow_html=True)
        if st.session_state.carrito:
            st.markdown("### 🛒 Tu Lista de Antojitos")
            
            # --- RENDERIZADO DEL CARRITO CON MINIATURAS ---
            for index, row in enumerate(st.session_state.carrito):
                with st.container(border=True):
                    col_img, col_info, col_p, col_x = st.columns([1, 2, 1, 1])
                    
                    # Miniatura
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
            st.markdown(f"**Subtotal:** S/ {subtotal:.2f}")
            st.markdown(f"**Delivery:** S/ {delivery_cost:.2f}")
            st.markdown(f"## **Total: S/ {total:.2f}**")

            with st.container(border=True):
                st.subheader("📝 Datos Finales")
                u_cel = st.text_input("Tu número de Celular", max_chars=9, placeholder="999888777")
                u_dir = st.text_area("Dirección exacta / Nro Dpto / Referencia")

                st.markdown("---")
                st.subheader("📍 Ubicación Exacta")
                st.write("Presiona el botón para que el repartidor llegue más rápido:")
    
                from streamlit_geolocation import streamlit_geolocation
                location = streamlit_geolocation()

                if location.get('latitude'):
                    lat = location['latitude']
                    lon = location['longitude']
                    # Enlace profesional de Google Maps
                    maps_link = f"https://www.google.com/maps?q={lat},{lon}"
                    st.success("✅ ¡Ubicación capturada con éxito!")
                else:
                    maps_link = "No proporcionada"
                    st.warning("⚠️ GPS no activado. El repartidor usará solo la dirección escrita.")
                st.markdown("---")
                
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
                st.info(f"💡 Vecino/a, vas a pedir **{len(st.session_state.carrito)} productos**. El total a pagar es **S/ {total:.2f}** (incluye delivery). ***No olvides enviar el comprobante de pago si es yape***")

                # --- RESUMEN DE CONFIRMACIÓN ANTES DEL BOTÓN ---
                st.info(f"💡 Vecino/a, vas a pedir **{len(st.session_state.carrito)} productos**. El total a pagar es **S/ {total:.2f}** (incluye delivery). ***No olvides enviar el comprobante de pago si es yape***")

                if st.button("🚀 CONFIRMAR Y ENVIAR PEDIDO", type="primary", use_container_width=True):
                    if not u_cel or not u_dir or len(u_cel) < 9:
                        st.error("Por favor, completa tu celular (9 dígitos) y dirección correctamente.")
                    else:
                        # Guardar captura si existe
                        p_path = ""
                        if cap_pago:
                            if not os.path.exists("capturas_yape"): os.makedirs("capturas_yape")
                            p_path = f"capturas_yape/p_{u_cel}_{get_peru_time().strftime('%H%M%S')}.png"
                            with open(p_path, "wb") as f: f.write(cap_pago.getbuffer())
        
                        # Guardar Pedido
                        df_pedidos_all = load_data("pedidos")
                        nuevo_id = int(df_pedidos_all['id'].max() + 1) if not df_pedidos_all.empty else 1
        
                # --- CÁLCULO DE GANANCIA CORREGIDO ---
                        try:
                            # Si el producto tiene 'ganancia_combo' definida (es un combo), usamos esa. 
                            # Si no, usamos la resta tradicional de venta - costo.
                        if 'ganancia_combo' in df_cart.columns and df_cart['ganancia_combo'].notna().any():
                            ganancia_final = df_cart['ganancia_combo'].sum()
                        else:
                            ganancia_prod = (df_cart['venta'].astype(float) - df_cart['costo'].astype(float)).sum()
                            ganancia_final = ganancia_prod # No sumamos delivery para no inflar la ganancia real
                        except:
                            ganancia_final = 0.0
            
                        nuevo_pedido = pd.DataFrame([{
                            "id": nuevo_id, 
                            "fecha": get_peru_time().strftime("%Y-%m-%d %H:%M"),
                            "cliente": st.session_state.nombre_usuario, 
                            "celular": u_cel, 
                            "direccion": u_dir, 
                            "zona": zona,
                            "productos_json": df_cart.to_json(orient='records'), 
                            "total": total,
                            "ganancia": ganancia_final, 
                            "metodo_pago": metodo, 
                            "monto_pagado": vuelto_de,
                            "captura_pago": p_path, 
                            "estado": "Nuevo",
                            "maps_link": maps_link # Se agregó la coma faltante arriba
                        }])
        
                        update_data(pd.concat([df_pedidos_all, nuevo_pedido], ignore_index=True), "pedidos")
        
                        # Actualizar Stock
                        df_prods_upd = load_data("productos")
                        for pid in df_cart['id']:
                            if str(pid).isdigit():
                                df_prods_upd.loc[df_prods_upd['id'] == int(pid), 'stock'] -= 1
                        update_data(df_prods_upd, "productos")
        
                        # --- ENVÍO DE WHATSAPP ---
                        import urllib.parse
                        lista_ws = "\n".join([f"• {row['nombre']}" for _, row in df_cart.iterrows()])
                        mensaje_ws = (
                            f"🛍️ *NUEVO PEDIDO - ANTOJITOS JORPAO*\n"
                            f"👤 *Cliente:* {st.session_state.nombre_usuario}\n"
                            f"📍 *Dirección:* {u_dir}\n"
                            f"📦 *Productos:*\n{lista_ws}\n"
                            f"💰 *Total:* S/ {total:.2f}\n"
                            f"🗺️ *Ubicación:* {maps_link}"
                        )
                        st.write(f"https://wa.me/51999999999?text={urllib.parse.quote(mensaje_ws)}") # Link listo para el vendedor

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
    
    # --- 1. CARGA DE DATOS ---
    try:
        df_v = load_data("pedidos")
    except Exception as e:
        st.error(f"Error al conectar con la base de datos: {e}")
        st.stop()
    
    if not df_v.empty:
        # --- 2. CONVERSIÓN DE DATOS ---
        df_v['total'] = pd.to_numeric(df_v['total'], errors='coerce').fillna(0)
        df_v['ganancia'] = pd.to_numeric(df_v['ganancia'], errors='coerce').fillna(0)
        
        # --- 3. MÉTRICAS (Lógica de ganancia sincronizada con Excel) ---
        total_ventas = df_v['total'].sum()

        # 1. Ganancia Real: Tomamos directamente lo que ya calculaste en el Excel
        # Si el Excel dice 2.90, el panel mostrará exactamente 2.90.
        ganancia_total_real = df_v['ganancia'].sum()

        # 2. Cantidad de pedidos (Total de filas en la hoja)
        cantidad_pedidos = len(df_v)

        # 3. Cálculo de rentabilidad
        porcentaje_rentabilidad = (ganancia_total_real / total_ventas * 100) if total_ventas > 0 else 0

        # Mostrar en pantalla
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Ventas Totales", f"S/ {total_ventas:.2f}")
        m2.metric("Ganancia Total", f"S/ {ganancia_total_real:.2f}", delta=f"{porcentaje_rentabilidad:.1f}% Retorno")
        m3.metric("Pedidos Totales", cantidad_pedidos)
        m4.metric("Ticket Promedio", f"S/ {df_v['total'].mean():.2f}")

        # --- 4. GRÁFICO DE PRODUCTOS ---
        st.subheader("🍕 Distribución de Ventas por Producto")
        lista_nombres = []
        if 'productos_json' in df_v.columns:
            import json
            for p_json in df_v['productos_json']:
                try:
                    if pd.notna(p_json) and p_json != "":
                        items = json.loads(p_json)
                        for it in items:
                            lista_nombres.append(it['nombre'])
                except:
                    continue
        
        if lista_nombres:
            df_pie = pd.Series(lista_nombres).value_counts().reset_index()
            df_pie.columns = ['Producto', 'Cantidad']
            
            import plotly.express as px
            fig = px.pie(df_pie, values='Cantidad', names='Producto', hole=0.4, 
                         color_discrete_sequence=px.colors.sequential.OrRd_r)
            fig.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("💡 No hay datos detallados de productos para mostrar la gráfica.")

        # --- 5. BANDEJA DE GESTIÓN (TODOS LOS PEDIDOS) ---
        st.subheader("📋 Gestión de Pedidos")
        
        # Ordenamos por ID descendente para ver los últimos arriba
        df_display = df_v.sort_values('id', ascending=False)
        
        for _, ped in df_display.iterrows():
            with st.container(border=True):
                c_info, c_accion = st.columns([3, 1])
                
                with c_info:
                    st.markdown(f"**Pedido #{ped['id']} - {ped['cliente']}**")
                    st.write(f"📍 {ped['direccion']} | 📱 {ped['celular']}")
                    st.write(f"💰 **Total: S/ {ped['total']:.2f}** | Estado: `{ped['estado']}`")
                    
                    # --- DETALLE QUIRÚRGICO DE PRODUCTOS ---
                with st.expander("📦 Ver productos del pedido"):
                    try:
                        import json
                        # Convertimos el texto JSON a una lista de Python
                        # Si ya es una lista, la usamos directamente; si es texto, la cargamos
                        items = json.loads(ped['productos_json']) if isinstance(ped['productos_json'], str) else ped['productos_json']
                        
                        # Mostramos cada producto con su cantidad y nombre
                        for it in items:
                            # Usamos .get() por seguridad en caso de que alguna llave falte
                            nombre = it.get('nombre', 'Producto')
                            cantidad = it.get('cantidad', 1)
                            # Intentamos mostrar el subtotal o el precio de venta si el subtotal no existe
                            precio = it.get('subtotal', it.get('venta', 0))
                            
                            st.write(f"• {int(cantidad)}x **{nombre}** - S/ {precio:.2f}")
                    except Exception:
                        # Si hay un error de formato, mostramos el texto crudo para no perder la información
                        st.write(f"Detalle: {ped['productos_json']}")
                
                with c_accion:
                    # Acción: Entregar
                    if ped['estado'] == 'Nuevo':
                        if st.button(f"Entregado ✅", key=f"ent_{ped['id']}", use_container_width=True):
                            df_v.loc[df_v['id'] == ped['id'], 'estado'] = 'Entregado'
                            update_data(df_v, "pedidos")
                            st.toast(f"Pedido #{ped['id']} entregado")
                            st.rerun()
                    
                    # Acción: Eliminar con Confirmación
                    if st.button(f"Eliminar 🗑️", key=f"del_init_{ped['id']}", use_container_width=True):
                        st.session_state[f"confirm_del_{ped['id']}"] = True
                    
                    if st.session_state.get(f"confirm_del_{ped['id']}", False):
                        st.warning(f"¿Borrar pedido #{ped['id']}?")
                        if st.button("SÍ, BORRAR ❗", key=f"conf_{ped['id']}", type="primary"):
                            df_v = df_v[df_v['id'] != ped['id']]
                            update_data(df_v, "pedidos")
                            del st.session_state[f"confirm_del_{ped['id']}"]
                            st.success("Eliminado")
                            st.rerun()
                        if st.button("Cancelar", key=f"canc_{ped['id']}"):
                            del st.session_state[f"confirm_del_{ped['id']}"]
                            st.rerun()

        # --- 6. EXPORTACIÓN ---
        st.markdown("---")
        st.subheader("📥 Exportar Reporte")
        try:
            excel_data = to_excel(df_v) 
            st.download_button(
                label="📥 Descargar Reporte en Excel",
                data=excel_data,
                file_name=f"reporte_ventas_jorpao_{get_peru_time().strftime('%Y%m%d_%H%M')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
        except Exception as e:
            st.warning("Define la función 'to_excel' para habilitar descargas.")

    else:
        st.info("Aún no hay datos de ventas registrados.")

# ==============================================================================
# VISTA: COMBOS (ADMIN)
# ==============================================================================
elif menu == "🎁 Gestionar Combos" and is_admin:
    st.header("🎁 Configuración de Combos")
    
    with st.container(border=True):
        st.subheader("Crear Nuevo Combo")
        c_n = st.text_input("Nombre del Combo (Ej: Combo Peliculero)")
        
        col_pre, col_gan = st.columns(2)
        c_p = col_pre.number_input("Precio de Venta al Público", min_value=0.0)
        # NUEVO: Entrada manual para la ganancia neta del combo
        c_g = col_gan.number_input("Ganancia Neta Manual (S/.)", min_value=0.0, help="Calcula el precio de venta menos tus costos con descuento.")
        
        st.write("Añadir productos al combo:")
        df_p_sel = load_data("productos")
        col_ps, col_pc, col_pb = st.columns([3, 1, 1])
        
        sel_p = col_ps.selectbox("Producto", df_p_sel['nombre'].tolist() if not df_p_sel.empty else [])
        sel_c = col_pc.number_input("Cant.", min_value=1, value=1)
        
        if col_pb.button("➕"):
            st.session_state.temp_combo_items.append(f"{sel_c}x {sel_p}")
            
        if st.session_state.temp_combo_items:
            st.write("**Lista actual:** " + " + ".join(st.session_state.temp_combo_items))
            if st.button("Limpiar lista"): 
                st.session_state.temp_combo_items = []
                st.rerun()
        
        if st.button("Guardar Combo", use_container_width=True):
            if c_n and st.session_state.temp_combo_items:
                df_combos_act = load_data("combos")
                nid = int(df_combos_act['id'].max() + 1) if not df_combos_act.empty else 1
                receta = ", ".join(st.session_state.temp_combo_items)
                
                # Sincronizado con las columnas de tu Sheets: id, nombre, productos, precio, GANANCIA, activo
                new_c = pd.DataFrame([{
                    "id": nid, 
                    "nombre_combo": c_n, 
                    "productos_ids": receta, 
                    "precio_combo": c_p, 
                    "ganancia_combo": c_g, # Se guarda en la columna E
                    "activo": 1
                }])
                
                update_data(pd.concat([df_combos_act, new_c], ignore_index=True), "combos")
                st.session_state.temp_combo_items = []
                st.success(f"¡Combo '{c_n}' registrado con ganancia de S/ {c_g:.2f}!")
                st.rerun()

    # 2. SECCIÓN DE GESTIÓN (EDITAR / BORRAR)
    st.subheader("📋 Combos Registrados")
    df_c_list = load_data("combos")
    
    if not df_c_list.empty:
        for index, row in df_c_list.iterrows():
            with st.container(border=True):
                col_info, col_edit, col_del = st.columns([3, 1, 1])
                
                with col_info:
                    st.markdown(f"**{row['nombre_combo']}**")
                    st.caption(f"Contenido: {row['productos_ids']}")
                    st.write(f"💰 Precio: S/ {row['precio_combo']:.2f}")
                
                # BOTÓN EDITAR: Carga los datos en el formulario superior
                if col_edit.button("📝 Editar", key=f"edit_c_{row['id']}", use_container_width=True):
                    st.session_state.temp_combo_items = row['productos_ids'].split(", ")
                    st.info(f"Cargado '{row['nombre_combo']}' para editar. Modifica arriba y vuelve a guardar.")
                
                # BOTÓN BORRAR: Elimina la fila del Excel
                if col_del.button("🗑️ Borrar", key=f"del_c_{row['id']}", use_container_width=True):
                    df_c_list = df_c_list.drop(index)
                    update_data(df_c_list, "combos")
                    st.success(f"Combo #{row['id']} eliminado")
                    st.rerun()
    else:
        st.info("No hay combos creados todavía.")

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
    
    # Filtramos pedidos que tengan una ruta de captura de pago registrada
    df_img = df_img[df_img['captura_pago'] != ""]
    
    if not df_img.empty:
        # Mostramos de los más recientes a los más antiguos
        for _, row in df_img.sort_values('id', ascending=False).iterrows():
            with st.container(border=True):
                st.subheader(f"Pedido #{row['id']} - {row['cliente']}")
                st.write(f"📅 Fecha: {row['fecha']} | 💰 Total: S/ {row['total']:.2f}")
                
                ruta_foto = str(row['captura_pago'])
                
                if os.path.exists(ruta_foto):
                    # Mostramos la imagen en pantalla
                    st.image(ruta_foto, caption=f"Comprobante de {row['cliente']}", width=350)
                    
                    # --- OPCIÓN DE DESCARGA ---
                    with open(ruta_foto, "rb") as file:
                        btn = st.download_button(
                            label="📥 Descargar Comprobante",
                            data=file,
                            file_name=f"comprobante_pedido_{row['id']}.png",
                            mime="image/png",
                            use_container_width=True
                        )
                else:
                    st.error(f"⚠️ El archivo '{ruta_foto}' no se encuentra en el servidor.")
                    st.info("Esto puede pasar si la imagen se borró de la carpeta temporal o si hubo un error en la subida.")
    else:
        st.info("Aún no hay capturas de pantalla registradas en el sistema.")