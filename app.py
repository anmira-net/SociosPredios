import streamlit as st
import pymysql
import pymysql.cursors
import pandas as pd
import re
from datetime import datetime, date

# ---------------------------------------------------------
# 1. CONFIGURACIÓN DE PÁGINA Y ESTILOS CORPORATIVOS (ANMIRA)
# ---------------------------------------------------------
st.set_page_config(
    page_title="Control de Cuotas - Anmira",
    page_icon="⚡",
    layout="wide"
)

# Estilos CSS limpios (sin afectar componentes de tablas)
st.markdown("""
    <style>
    .main {
        background-color: #F8F9FA;
    }
    .stButton>button {
        background: linear-gradient(90deg, #0077B6 0%, #00A8E8 100%);
        color: white;
        border: none;
        border-radius: 6px;
        font-weight: bold;
        padding: 0.5rem 1rem;
    }
    .stButton>button:hover {
        background: linear-gradient(90deg, #0D3B66 0%, #0077B6 100%);
        color: white;
    }
    [data-testid="stMetricValue"] {
        color: #0077B6;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 2. CONEXIÓN A BASE DE DATOS (NEUBOX)
# ---------------------------------------------------------
DB_CONFIG = {
    "host": "svgr348.serverneubox.com.mx",
    "user": "anmirane_admin",
    "password": "AndreaMia2026+-",
    "database": "anmirane_Socios",
    "port": 3306,
    "charset": "utf8mb4",
    "connect_timeout": 10,
    "cursorclass": pymysql.cursors.DictCursor
}

def get_connection():
    return pymysql.connect(**DB_CONFIG)

# ---------------------------------------------------------
# 3. CONTROL DE SESIÓN Y LOGIN CON CONTROL DE LICENCIAS
# ---------------------------------------------------------
if 'user' not in st.session_state:
    st.session_state['user'] = None

def login(usuario, password):
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            sql = "SELECT * FROM usuarios WHERE usuario = %s AND password_hash = %s AND activo = 1"
            cursor.execute(sql, (usuario, password))
            return cursor.fetchone()
    finally:
        conn.close()

# Pantalla de Login si no hay sesión activa
if st.session_state['user'] is None:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        try:
            st.image("Anmira Blanco.jpg", use_container_width=True)
        except:
            st.title("⚡ Anmira")
        
        st.subheader("🔐 Iniciar Sesión - Control de Cuotas")
        usr = st.text_input("Usuario")
        pwd = st.text_input("Contraseña", type="password")
        
        if st.button("Ingresar al Sistema", use_container_width=True):
            user = login(usr, pwd)
            if user:
                # Validar Expiración de Licencia para Supervisor y Capturista
                if user['tipo_licencia'] == 'Paga' and user['fecha_expiracion_licencia']:
                    if user['fecha_expiracion_licencia'] < date.today():
                        st.error("❌ Su licencia está caducada. Por favor comuníquese con el equipo de Anmira.")
                        st.stop()
                
                st.session_state['user'] = user
                st.rerun()
            else:
                st.error("⚠️ Usuario o contraseña incorrectos.")
    st.stop()

# Usuario en sesión
current_user = st.session_state['user']
rol = current_user['rol']

# Barra Lateral con Marca e Información de Usuario
try:
    st.sidebar.image("Anmira Blanco.jpg", use_container_width=True)
except:
    st.sidebar.markdown("## ⚡ **Anmira**")

st.sidebar.write(f"👤 **Usuario:** {current_user['usuario']}")
st.sidebar.write(f"🛡️ **Rol:** {rol}")
st.sidebar.write(f"📜 **Licencia:** {current_user['tipo_licencia']}")

if st.sidebar.button("🚪 Cerrar Sesión", use_container_width=True):
    st.session_state['user'] = None
    st.rerun()

# ---------------------------------------------------------
# 4. NAVEGACIÓN Y PERMISOS POR ROL
# ---------------------------------------------------------
st.title("📊 Control de Cuotas Mensuales")

pestañas_permitidas = []
if rol == "Administrador General":
    pestañas_permitidas = ["⚙️ Configuración", "📁 Catálogos", "📝 Captura de Cuotas", "📈 Dashboard y Estadísticas"]
elif rol == "Supervisor":
    pestañas_permitidas = ["📁 Catálogos", "📝 Captura de Cuotas", "📈 Dashboard y Estadísticas"]
elif rol == "Capturista":
    pestañas_permitidas = ["📁 Catálogos", "📝 Captura de Cuotas", "📈 Dashboard y Estadísticas"]
elif rol == "Consultante":
    pestañas_permitidas = ["📈 Dashboard y Estadísticas"]

tab_seleccionada = st.sidebar.radio("Menú Principal", pestañas_permitidas)

# ---------------------------------------------------------
# MÓDULO 1: CONFIGURACIÓN (Administrador General)
# ---------------------------------------------------------
if tab_seleccionada == "⚙️ Configuración":
    st.header("⚙️ Configuración General del Sistema")
    
    sub1, sub2, sub3 = st.tabs(["👥 Usuarios y Licencias", "📥 Carga Inicial (Excel)", "🔄 Reiniciar BD"])
    
    with sub1:
        st.subheader("➕ Alta de Usuarios")
        with st.form("form_alta_usuario", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                nuevo_user = st.text_input("Nombre de Usuario *")
                nuevo_correo = st.text_input("Correo Electrónico *")
                nuevo_pass = st.text_input("Contraseña *", type="password")
            with c2:
                nuevo_rol = st.selectbox("Rol *", ["Administrador General", "Supervisor", "Capturista", "Consultante"])
                
                es_de_paga = nuevo_rol in ["Supervisor", "Capturista"]
                tipo_lic_label = "Paga (Suscripción)" if es_de_paga else "Libre (Gratuita)"
                st.info(f"**Tipo de Licencia:** {tipo_lic_label}")
                
                if es_de_paga:
                    fecha_exp = st.date_input("Fecha Expiración Licencia *", value=date(2027, 12, 31))
                else:
                    fecha_exp = None
            
            submitted = st.form_submit_button("➕ Registrar Usuario", use_container_width=True)
            if submitted:
                if not nuevo_user or not nuevo_correo or not nuevo_pass:
                    st.warning("⚠️ Todos los campos con asterisco (*) son obligatorios.")
                else:
                    tipo_lic = "Paga" if es_de_paga else "Libre"
                    
                    conn = get_connection()
                    try:
                        with conn.cursor() as cursor:
                            sql = """INSERT INTO usuarios (usuario, correo, password_hash, rol, tipo_licencia, fecha_expiracion_licencia)
                                     VALUES (%s, %s, %s, %s, %s, %s)"""
                            cursor.execute(sql, (nuevo_user, nuevo_correo, nuevo_pass, nuevo_rol, tipo_lic, fecha_exp))
                            conn.commit()
                            st.success(f"✅ Usuario '{nuevo_user}' registrado con éxito.")
                            st.rerun()
                    except pymysql.err.IntegrityError:
                        st.error(f"❌ El nombre de usuario '{nuevo_user}' ya existe.")
                    except Exception as e:
                        st.error(f"Error al registrar usuario: {e}")
                    finally:
                        conn.close()

        st.markdown("---")
        st.subheader("✏️ Modificar / Editar Usuario Existente")

        # Traer lista de usuarios para seleccionar a cuál editar
        conn = get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT id, usuario, correo, rol, tipo_licencia, fecha_expiracion_licencia, activo FROM usuarios ORDER BY usuario ASC")
                lista_usuarios = cursor.fetchall()
        finally:
            conn.close()

        if lista_usuarios:
            user_opt_dict = {f"{u['usuario']} ({u['rol']})": u for u in lista_usuarios}
            selected_user_label = st.selectbox("Selecciona el usuario a editar:", list(user_opt_dict.keys()))
            u_selected = user_opt_dict[selected_user_label]

            with st.form("form_editar_usuario"):
                st.markdown(f"Editing usuario: **{u_selected['usuario']}** (ID: {u_selected['id']})")
                
                col_e1, col_e2 = st.columns(2)
                
                with col_e1:
                    edit_correo = st.text_input("Correo Electrónico", value=u_selected['correo'])
                    edit_pass = st.text_input("Nueva Contraseña (dejar en blanco para conservar la actual)", type="password")
                    edit_activo = st.selectbox("Estado de la cuenta", ["Activo", "Inactivo"], index=0 if u_selected['activo'] == 1 else 1)
                
                with col_e2:
                    roles_list = ["Administrador General", "Supervisor", "Capturista", "Consultante"]
                    idx_rol = roles_list.index(u_selected['rol']) if u_selected['rol'] in roles_list else 0
                    edit_rol = st.selectbox("Rol del Usuario", roles_list, index=idx_rol)
                    
                    edit_es_paga = edit_rol in ["Supervisor", "Capturista"]
                    edit_tipo_lic = "Paga" if edit_es_paga else "Libre"
                    st.info(f"**Licencia según rol:** {edit_tipo_lic}")
                    
                    val_fecha_default = u_selected['fecha_expiracion_licencia'] if u_selected['fecha_expiracion_licencia'] else date(2027, 12, 31)
                    if edit_es_paga:
                        edit_fecha_exp = st.date_input("Fecha Caducidad / Expiración Licencia", value=val_fecha_default)
                    else:
                        edit_fecha_exp = None

                btn_guardar_edit = st.form_submit_button("💾 Guardar Cambios", use_container_width=True)
                
                if btn_guardar_edit:
                    conn = get_connection()
                    try:
                        with conn.cursor() as cursor:
                            activo_val = 1 if edit_activo == "Activo" else 0
                            
                            if edit_pass.strip():
                                sql_update = """
                                    UPDATE usuarios 
                                    SET correo = %s, password_hash = %s, rol = %s, tipo_licencia = %s, fecha_expiracion_licencia = %s, activo = %s
                                    WHERE id = %s
                                """
                                cursor.execute(sql_update, (edit_correo, edit_pass, edit_rol, edit_tipo_lic, edit_fecha_exp, activo_val, u_selected['id']))
                            else:
                                sql_update = """
                                    UPDATE usuarios 
                                    SET correo = %s, rol = %s, tipo_licencia = %s, fecha_expiracion_licencia = %s, activo = %s
                                    WHERE id = %s
                                """
                                cursor.execute(sql_update, (edit_correo, edit_rol, edit_tipo_lic, edit_fecha_exp, activo_val, u_selected['id']))
                            
                            conn.commit()
                            st.success(f"✅ ¡El usuario '{u_selected['usuario']}' fue actualizado correctamente!")
                            st.rerun()
                    except Exception as e:
                        st.error(f"Error al actualizar usuario: {e}")
                    finally:
                        conn.close()

        st.markdown("---")
        st.subheader("📋 Usuarios Registrados en el Sistema")
        
        conn = get_connection()
        try:
            sql_usuarios = """
                SELECT 
                    id,
                    usuario,
                    correo,
                    rol,
                    tipo_licencia,
                    IFNULL(DATE_FORMAT(fecha_expiracion_licencia, '%Y-%m-%d'), 'Sin expiración') AS fecha_exp,
                    activo
                FROM usuarios
                ORDER BY id ASC
            """
            cursor = conn.cursor()
            cursor.execute(sql_usuarios)
            usuarios = cursor.fetchall()
            
            if usuarios:
                rows_html = ""
                for idx, u in enumerate(usuarios):
                    bg_color = "#f9f9f9" if idx % 2 == 0 else "#ffffff"
                    estado_str = "🟢 Activo" if u['activo'] == 1 else "🔴 Inactivo"
                    
                    rows_html += f"""
                    <tr style="background-color: {bg_color}; border-bottom: 1px solid #e0e0e0;">
                        <td style="padding: 10px; font-weight: bold; text-align: center;">{u['id']}</td>
                        <td style="padding: 10px;">{u['usuario']}</td>
                        <td style="padding: 10px;">{u['correo']}</td>
                        <td style="padding: 10px;">{u['rol']}</td>
                        <td style="padding: 10px; text-align: center;">{u['tipo_licencia']}</td>
                        <td style="padding: 10px; text-align: center;">{u['fecha_exp']}</td>
                        <td style="padding: 10px; text-align: center;">{estado_str}</td>
                    </tr>
                    """

                table_html = f"""
                <div style="font-family: Arial, sans-serif; width: 100%; overflow-x: auto;">
                    <table style="width: 100%; border-collapse: collapse; box-shadow: 0 2px 5px rgba(0,0,0,0.1); border-radius: 6px; overflow: hidden;">
                        <thead>
                            <tr style="background-color: #0D3B66; color: #ffffff; text-align: left; font-size: 14px;">
                                <th style="padding: 12px; text-align: center; width: 50px;">ID</th>
                                <th style="padding: 12px;">Usuario</th>
                                <th style="padding: 12px;">Correo Electrónico</th>
                                <th style="padding: 12px;">Rol</th>
                                <th style="padding: 12px; text-align: center;">Licencia</th>
                                <th style="padding: 12px; text-align: center;">Expiración</th>
                                <th style="padding: 12px; text-align: center;">Estado</th>
                            </tr>
                        </thead>
                        <tbody style="font-size: 13px; color: #333333;">
                            {rows_html}
                        </tbody>
                    </table>
                </div>
                """
                
                import streamlit.components.v1 as components
                altura_tabla = max(180, (len(usuarios) * 45) + 60)
                components.html(table_html, height=altura_tabla, scrolling=True)
            else:
                st.info("No hay usuarios registrados en la base de datos.")
        except Exception as e:
            st.error(f"Error al cargar la tabla de usuarios: {e}")
        finally:
            conn.close()

    with sub2:
        st.subheader("📥 Carga e Importación Inicial desde Excel")
        st.info("💡 Este proceso registrará las pestañas del Excel (`COAHUILA` y `DURANGO`) como los Estados/Localidades principales y asociará los Socios, Predios y Pagos correspondientes.")
        
        uploaded_file = st.file_uploader("Selecciona el archivo Excel oficial (PROYECTO BC 19 MARZO 2026.xlsx)", type=["xlsx", "xls"])
        
        if uploaded_file is not None:
            if st.button("🚀 Iniciar Importación a la Base de Datos", use_container_width=True):
                progreso = st.progress(0, text="Iniciando conexión con MariaDB...")
                
                try:
                    conn = get_connection()
                    cursor = conn.cursor()
                    
                    cursor.execute("SELECT id FROM cuotas WHERE activa = 1 LIMIT 1")
                    cuota_res = cursor.fetchone()
                    if not cuota_res:
                        cursor.execute("INSERT INTO cuotas (concepto, monto, activa) VALUES ('Cuota Mensual Por Predio', 50.00, 1)")
                        cuota_id = cursor.lastrowid
                    else:
                        cuota_id = cuota_res['id']

                    MESES_MAP = {
                        'ABRIL': 4, 'MAYO': 5, 'JUNIO': 6, 'JULIO': 7, 
                        'AGOS': 8, 'AGOSTO': 8, 'SEP': 9, 'OCT': 10, 
                        'NOV': 11, 'DIC': 12, 'ENERO': 1, 'FEB': 2, 'MARZO': 3
                    }

                    hojas_config = [
                        {'nombre': 'COAHUILA', 'skiprows': 0},
                        {'nombre': 'DURANGO', 'skiprows': 6}
                    ]

                    total_socios_cargados = 0
                    total_predios_cargados = 0
                    total_pagos_cargados = 0

                    for index_h, h in enumerate(hojas_config):
                        progreso.progress(20 + (index_h * 40), text=f"Procesando pestaña/localidad: {h['nombre']}...")
                        
                        cursor.execute(
                            "SELECT id FROM localidades WHERE estado = %s OR comunidad = %s LIMIT 1", 
                            (h['nombre'], h['nombre'])
                        )
                        loc_res = cursor.fetchone()
                        if not loc_res:
                            cursor.execute(
                                "INSERT INTO localidades (comunidad, municipio, estado) VALUES (%s, %s, %s)", 
                                (h['nombre'], 'GENERAL', h['nombre'])
                            )
                            loc_id = cursor.lastrowid
                        else:
                            loc_id = loc_res['id']

                        df = pd.read_excel(uploaded_file, sheet_name=h['nombre'], skiprows=h['skiprows'])
                        df.columns = [str(col).strip() for col in df.columns]

                        for idx, row in df.iterrows():
                            nombre_socio = str(row.get('NOMBRE', '')).strip()
                            no_socio = str(row.get('NO. DE SOCIO', '')).strip()

                            if not nombre_socio or nombre_socio == 'nan' or 'BASE DE DATOS' in nombre_socio or 'TOTAL' in nombre_socio.upper():
                                continue

                            no_socio_val = no_socio if no_socio != 'nan' and no_socio != '' else None
                            tel_val = str(row.get('TELEFONO', '')).strip()
                            if tel_val == 'nan': tel_val = None

                            if no_socio_val:
                                cursor.execute("SELECT id FROM socios WHERE no_socio = %s", (no_socio_val,))
                                socio_existente = cursor.fetchone()
                                
                                if socio_existente:
                                    socio_id = socio_existente['id']
                                    cursor.execute(
                                        "UPDATE socios SET nombre_completo = %s, telefono = %s WHERE id = %s",
                                        (nombre_socio, tel_val, socio_id)
                                    )
                                else:
                                    cursor.execute(
                                        "INSERT INTO socios (no_socio, nombre_completo, telefono) VALUES (%s, %s, %s)",
                                        (no_socio_val, nombre_socio, tel_val)
                                    )
                                    socio_id = cursor.lastrowid
                            else:
                                cursor.execute(
                                    "INSERT INTO socios (no_socio, nombre_completo, telefono) VALUES (%s, %s, %s)",
                                    (None, nombre_socio, tel_val)
                                )
                                socio_id = cursor.lastrowid

                            total_socios_cargados += 1

                            cant_predios = 1
                            num_cert = row.get('TOTAL DE CERTIFICADOS')
                            if pd.notnull(num_cert) and str(num_cert).replace('.','').isdigit():
                                cant_predios = max(1, int(float(num_cert)))
                            else:
                                match = re.search(r'\((\d+)\s*PREDIOS?\)', nombre_socio, re.IGNORECASE)
                                if match:
                                    cant_predios = int(match.group(1))

                            predio_ids = []
                            for p in range(1, cant_predios + 1):
                                num_p_str = f"{no_socio_val if no_socio_val else f'S{socio_id}'}-P{p}"
                                cursor.execute(
                                    "INSERT INTO predios (socio_id, localidad_id, num_predio) VALUES (%s, %s, %s)", 
                                    (socio_id, loc_id, num_p_str)
                                )
                                predio_ids.append(cursor.lastrowid)
                                total_predios_cargados += 1

                            for col_m, num_m in MESES_MAP.items():
                                if col_m in row and pd.notnull(row[col_m]):
                                    try:
                                        monto_bruto = float(row[col_m])
                                        if monto_bruto > 0:
                                            monto_por_predio = monto_bruto / len(predio_ids)
                                            anio_p = 2025 if num_m >= 4 else 2026
                                            
                                            for pid in predio_ids:
                                                cursor.execute("""
                                                    INSERT INTO pagos (predio_id, cuota_id, anio, mes, monto_pagado, capturado_por)
                                                    VALUES (%s, %s, %s, %s, %s, 'MIGRACION_EXCEL')
                                                    ON DUPLICATE KEY UPDATE monto_pagado = VALUES(monto_pagado)
                                                """, (pid, cuota_id, anio_p, num_m, monto_por_predio))
                                                total_pagos_cargados += 1
                                    except ValueError:
                                        pass

                    conn.commit()
                    progreso.progress(100, text="¡Importación Finalizada!")
                    
                    st.success("🎉 **¡Carga Masiva Completada con Éxito!**")
                    
                    c_res1, c_res2, c_res3 = st.columns(3)
                    c_res1.metric("Socios Cargados", f"{total_socios_cargados:,}")
                    c_res2.metric("Predios Creados", f"{total_predios_cargados:,}")
                    c_res3.metric("Pagos Creados", f"{total_pagos_cargados:,}")

                except Exception as e:
                    st.error(f"❌ Ocurrió un error inesperado durante la importación: {e}")
                finally:
                    conn.close()

    with sub3:
        st.subheader("🔴 Reinicializar Base de Datos")
        st.warning("⚠️ Esta acción eliminará permanentemente todas las localidades, socios, predios y pagos.")
        if st.button("Borrar Datos y Reiniciar Tablas"):
            conn = get_connection()
            try:
                with conn.cursor() as cursor:
                    cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")
                    cursor.execute("TRUNCATE TABLE pagos;")
                    cursor.execute("TRUNCATE TABLE predios;")
                    cursor.execute("TRUNCATE TABLE socios;")
                    cursor.execute("TRUNCATE TABLE localidades;")
                    cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")
                    conn.commit()
                    st.success("✅ La base de datos fue reiniciada correctamente.")
            finally:
                conn.close()

# ---------------------------------------------------------
# MÓDULO 2: CATÁLOGOS (Supervisor y Capturista)
# ---------------------------------------------------------
elif "Catálogos" in tab_seleccionada:
    st.header("📁 Gestión de Catálogos")
    
    cat1, cat2, cat3 = st.tabs(["📍 Localidades", "👥 Socios y Predios", "💵 Cuotas"])
    
    with cat1:
        st.subheader("Catálogo de Localidades")
        if rol in ["Administrador General", "Supervisor"]:
            with st.form("form_loc"):
                col_a, col_b, col_c = st.columns(3)
                comunidad_in = col_a.text_input("Comunidad / Localidad *")
                municipio_in = col_b.text_input("Municipio")
                estado_in = col_c.selectbox("Estado", ["COAHUILA", "DURANGO"])
                
                if st.form_submit_button("➕ Guardar Localidad", use_container_width=True):
                    if not comunidad_in.strip():
                        st.warning("⚠️ El nombre de la comunidad/localidad es obligatorio.")
                    else:
                        conn = get_connection()
                        try:
                            with conn.cursor() as cursor:
                                cursor.execute(
                                    "INSERT INTO localidades (comunidad, municipio, estado) VALUES (%s, %s, %s)",
                                    (comunidad_in.strip(), municipio_in.strip() if municipio_in else 'N/A', estado_in)
                                )
                                conn.commit()
                                st.success("✅ Localidad guardada con éxito.")
                                st.rerun()
                        except Exception as e:
                            st.error(f"Error al guardar localidad: {e}")
                        finally:
                            conn.close()
        
        st.markdown("---")
        st.subheader("📋 Localidades Registradas")
        
        conn = get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT id, comunidad, municipio, estado 
                    FROM localidades 
                    ORDER BY id ASC
                """)
                localidades = cursor.fetchall()
            
            if localidades:
                rows_html = ""
                for idx, loc in enumerate(localidades):
                    bg_color = "#f9f9f9" if idx % 2 == 0 else "#ffffff"
                    muni_val = loc['municipio'] if loc['municipio'] else 'N/A'
                    
                    rows_html += f"""
                    <tr style="background-color: {bg_color}; border-bottom: 1px solid #e0e0e0;">
                        <td style="padding: 10px; font-weight: bold; text-align: center;">{loc['id']}</td>
                        <td style="padding: 10px;">{loc['comunidad']}</td>
                        <td style="padding: 10px;">{muni_val}</td>
                        <td style="padding: 10px; text-align: center;">{loc['estado']}</td>
                    </tr>
                    """

                table_html = f"""
                <div style="font-family: Arial, sans-serif; width: 100%; overflow-x: auto;">
                    <table style="width: 100%; border-collapse: collapse; box-shadow: 0 2px 5px rgba(0,0,0,0.1); border-radius: 6px; overflow: hidden;">
                        <thead>
                            <tr style="background-color: #0D3B66; color: #ffffff; text-align: left; font-size: 14px;">
                                <th style="padding: 12px; text-align: center; width: 60px;">ID</th>
                                <th style="padding: 12px;">Comunidad / Localidad</th>
                                <th style="padding: 12px;">Municipio</th>
                                <th style="padding: 12px; text-align: center;">Estado</th>
                            </tr>
                        </thead>
                        <tbody style="font-size: 13px; color: #333333;">
                            {rows_html}
                        </tbody>
                    </table>
                </div>
                """
                
                import streamlit.components.v1 as components
                altura_tabla = max(180, (len(localidades) * 45) + 60)
                components.html(table_html, height=altura_tabla, scrolling=True)
            else:
                st.info("No hay localidades registradas en el sistema.")
        except Exception as e:
            st.error(f"Error al cargar el catálogo de localidades: {e}")
        finally:
            conn.close()

    with cat2:
        st.subheader("👥 Gestión de Socios y Predios")

        tab_soc_alta, tab_soc_edit = st.tabs(["➕ Registrar Nuevo Socio", "✏️ Consultar y Editar Socio / Predios"])

        with tab_soc_alta:
            conn = get_connection()
            try:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT id, CONCAT(comunidad, ' (', estado, ')') as nombre FROM localidades ORDER BY comunidad ASC")
                    locs = cursor.fetchall()
                    loc_dict = {l['nombre']: l['id'] for l in locs}
            finally:
                conn.close()

            if loc_dict:
                with st.form("form_alta_socio_predios", clear_on_submit=True):
                    c1, c2 = st.columns(2)
                    no_socio_i = c1.text_input("Número / Clave de Socio * (Ej. C-200)")
                    nombre_i = c2.text_input("Nombre Completo del Socio *")
                    tel_i = c1.text_input("Teléfono de Contacto")
                    num_predios_i = c2.number_input("Cantidad Inicial de Predios a Asignar", min_value=1, max_value=50, value=1)
                    
                    st.markdown("---")
                    st.write("**Ubicación e Identificadores de los Predios:**")
                    predios_data = []
                    for idx in range(int(num_predios_i)):
                        col_p1, col_p2 = st.columns(2)
                        ident_def = f"{no_socio_i.strip() if no_socio_i.strip() else 'P'}-P{idx+1}"
                        ident = col_p1.text_input(f"Identificador Predio #{idx+1} *", value=ident_def, key=f"alta_id_p_{idx}")
                        loc_p = col_p2.selectbox(f"Localidad Predio #{idx+1}", list(loc_dict.keys()), key=f"alta_loc_p_{idx}")
                        predios_data.append({'num': ident.strip(), 'loc_id': loc_dict[loc_p]})
                    
                    if st.form_submit_button("➕ Registrar Socio y Predios", use_container_width=True):
                        if not nombre_i.strip() or not no_socio_i.strip():
                            st.warning("⚠️ El nombre del socio y su clave/número son obligatorios.")
                        else:
                            conn = get_connection()
                            try:
                                with conn.cursor() as cursor:
                                    cursor.execute(
                                        "INSERT INTO socios (no_socio, nombre_completo, telefono) VALUES (%s, %s, %s)",
                                        (no_socio_i.strip(), nombre_i.strip(), tel_i.strip() if tel_i else None)
                                    )
                                    s_id = cursor.lastrowid
                                    
                                    for p in predios_data:
                                        cursor.execute(
                                            "INSERT INTO predios (socio_id, localidad_id, num_predio) VALUES (%s, %s, %s)",
                                            (s_id, p['loc_id'], p['num'])
                                        )
                                    conn.commit()
                                    st.success(f"✅ Socio '{nombre_i.strip()}' registrado exitosamente con {len(predios_data)} predio(s).")
                                    st.rerun()
                            except pymysql.err.IntegrityError:
                                st.error(f"❌ La clave / número de socio '{no_socio_i.strip()}' ya existe en el sistema. Elija una clave diferente.")
                            except Exception as e:
                                st.error(f"Error al registrar socio: {e}")
                            finally:
                                conn.close()
            else:
                st.info("⚠️ Primero debe registrar al menos una Localidad en la pestaña anterior.")

        with tab_soc_edit:
            conn = get_connection()
            try:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        SELECT id, no_socio, nombre_completo, telefono 
                        FROM socios 
                        ORDER BY nombre_completo ASC
                    """)
                    socios_registrados = cursor.fetchall()
                    
                    cursor.execute("SELECT id, CONCAT(comunidad, ' (', estado, ')') as nombre FROM localidades ORDER BY comunidad ASC")
                    locs_edit = cursor.fetchall()
                    loc_dict_edit = {l['nombre']: l['id'] for l in locs_edit}
                    loc_id_to_name = {l['id']: l['nombre'] for l in locs_edit}
            finally:
                conn.close()

            if socios_registrados:
                socio_map = {f"{s['nombre_completo']} | Clave: {s['no_socio'] if s['no_socio'] else 'Sin Clave'}": s for s in socios_registrados}
                socio_sel_label = st.selectbox("🔍 Buscar y Seleccionar Socio a Administrar:", list(socio_map.keys()))
                s_actual = socio_map[socio_sel_label]

                st.markdown("---")
                col_e1, col_e2 = st.columns([2, 1])

                with col_e1:
                    st.subheader("📝 Datos Generales del Socio")
                    with st.form("form_edit_socio_general"):
                        st.text_input("Clave / Número de Socio (🔒 Inamovible)", value=s_actual['no_socio'] if s_actual['no_socio'] else '', disabled=True)
                        edit_socio_nombre = st.text_input("Nombre Completo del Socio *", value=s_actual['nombre_completo'])
                        edit_socio_tel = st.text_input("Teléfono de Contacto", value=s_actual['telefono'] if s_actual['telefono'] else '')

                        if st.form_submit_button("💾 Actualizar Datos del Socio"):
                            if not edit_socio_nombre.strip():
                                st.warning("⚠️ El nombre del socio no puede estar vacío.")
                            else:
                                conn = get_connection()
                                try:
                                    with conn.cursor() as cursor:
                                        cursor.execute(
                                            "UPDATE socios SET nombre_completo = %s, telefono = %s WHERE id = %s",
                                            (edit_socio_nombre.strip(), edit_socio_tel.strip() if edit_socio_tel else None, s_actual['id'])
                                        )
                                        conn.commit()
                                        st.success("✅ Datos del socio actualizados correctamente.")
                                        st.rerun()
                                except Exception as e:
                                    st.error(f"Error al actualizar socio: {e}")
                                finally:
                                    conn.close()

                with col_e2:
                    st.subheader("🗑️ Eliminar Socio")
                    st.caption("Solo se permite eliminar un socio si **ninguno** de sus predios tiene pagos registrados en el historial.")
                    if st.button("🔴 Eliminar Socio Completo", use_container_width=True):
                        conn = get_connection()
                        try:
                            with conn.cursor() as cursor:
                                cursor.execute("""
                                    SELECT COUNT(pg.id) as total_pagos 
                                    FROM pagos pg 
                                    JOIN predios p ON pg.predio_id = p.id 
                                    WHERE p.socio_id = %s
                                """, (s_actual['id'],))
                                check_pagos = cursor.fetchone()
                                
                                if check_pagos and check_pagos['total_pagos'] > 0:
                                    st.error(f"❌ **No se puede eliminar el socio:** Existen **{check_pagos['total_pagos']}** pagos registrados en el historial para sus predios.")
                                else:
                                    cursor.execute("DELETE FROM predios WHERE socio_id = %s", (s_actual['id'],))
                                    cursor.execute("DELETE FROM socios WHERE id = %s", (s_actual['id'],))
                                    conn.commit()
                                    st.success(f"✅ El socio '{s_actual['nombre_completo']}' y sus predios fueron eliminados con éxito.")
                                    st.rerun()
                        except Exception as e:
                            st.error(f"Error al intentar eliminar el socio: {e}")
                        finally:
                            conn.close()

                st.markdown("---")
                st.subheader("🏞️ Predios Asignados al Socio")

                conn = get_connection()
                try:
                    with conn.cursor() as cursor:
                        cursor.execute("""
                            SELECT p.id, p.num_predio, p.localidad_id, l.comunidad, l.estado,
                                   (SELECT COUNT(pg.id) FROM pagos pg WHERE pg.predio_id = p.id) as total_pagos
                            FROM predios p
                            JOIN localidades l ON p.localidad_id = l.id
                            WHERE p.socio_id = %s
                            ORDER BY p.id ASC
                        """, (s_actual['id'],))
                        predios_socio = cursor.fetchall()
                finally:
                    conn.close()

                if predios_socio:
                    for pr in predios_socio:
                        with st.expander(f"📍 Predio: **{pr['num_predio']}** | Ubicación: {pr['comunidad']} ({pr['estado']}) | Pagos registrados: {pr['total_pagos']}"):
                            col_p_e1, col_p_e2, col_p_e3 = st.columns([2, 2, 1])
                            
                            with col_p_e1:
                                nuevo_num_p = st.text_input("Identificador del Predio", value=pr['num_predio'], key=f"edit_num_p_{pr['id']}")
                            with col_p_e2:
                                loc_actual_nombre = loc_id_to_name.get(pr['localidad_id'], list(loc_dict_edit.keys())[0])
                                idx_loc_actual = list(loc_dict_edit.keys()).index(loc_actual_nombre) if loc_actual_nombre in loc_dict_edit else 0
                                nueva_loc_p = st.selectbox("Localidad del Predio", list(loc_dict_edit.keys()), index=idx_loc_actual, key=f"edit_loc_p_{pr['id']}")
                            
                            with col_p_e3:
                                st.write("Acciones")
                                if st.button("💾 Guardar", key=f"btn_save_p_{pr['id']}"):
                                    conn = get_connection()
                                    try:
                                        with conn.cursor() as cursor:
                                            cursor.execute(
                                                "UPDATE predios SET num_predio = %s, localidad_id = %s WHERE id = %s",
                                                (nuevo_num_p.strip(), loc_dict_edit[nueva_loc_p], pr['id'])
                                            )
                                            conn.commit()
                                            st.success("✅ Predio actualizado.")
                                            st.rerun()
                                    finally:
                                        conn.close()
                                
                                if st.button("🗑️ Borrar", key=f"btn_del_p_{pr['id']}"):
                                    if pr['total_pagos'] > 0:
                                        st.error(f"❌ **No se puede borrar:** Este predio tiene {pr['total_pagos']} pago(s) registrado(s).")
                                    else:
                                        conn = get_connection()
                                        try:
                                            with conn.cursor() as cursor:
                                                cursor.execute("DELETE FROM predios WHERE id = %s", (pr['id'],))
                                                conn.commit()
                                                st.success("✅ Predio eliminado.")
                                                st.rerun()
                                        finally:
                                            conn.close()
                else:
                    st.info("Este socio no tiene predios asignados actualmente.")

                st.markdown("##### ➕ Agregar Nuevo Predio a este Socio")
                with st.form("form_add_predio_socio", clear_on_submit=True):
                    col_add1, col_add2 = st.columns(2)
                    ident_nuevo = col_add1.text_input("Identificador del Nuevo Predio * (Ej. " + (s_actual['no_socio'] if s_actual['no_socio'] else 'P') + f"-P{len(predios_socio)+1})")
                    loc_nueva = col_add2.selectbox("Localidad del Nuevo Predio", list(loc_dict_edit.keys()))
                    
                    if st.form_submit_button("➕ Asignar Nuevo Predio al Socio"):
                        if not ident_nuevo.strip():
                            st.warning("⚠️ El identificador del predio es obligatorio.")
                        else:
                            conn = get_connection()
                            try:
                                with conn.cursor() as cursor:
                                    cursor.execute(
                                        "INSERT INTO predios (socio_id, localidad_id, num_predio) VALUES (%s, %s, %s)",
                                        (s_actual['id'], loc_dict_edit[loc_nueva], ident_nuevo.strip())
                                    )
                                    conn.commit()
                                    st.success(f"✅ Nuevo predio '{ident_nuevo.strip()}' asignado al socio.")
                                    st.rerun()
                            finally:
                                conn.close()
            else:
                st.info("No hay socios registrados para consultar.")

        st.markdown("---")
        st.subheader("📋 Listado General de Socios y Predios")
        
        conn = get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        s.id,
                        IFNULL(s.no_socio, 'Sin Clave') as no_socio,
                        s.nombre_completo,
                        IFNULL(s.telefono, 'Sin Teléfono') as telefono,
                        COUNT(p.id) as total_predios
                    FROM socios s
                    LEFT JOIN predios p ON s.id = p.socio_id
                    GROUP BY s.id
                    ORDER BY s.id ASC
                """)
                socios_tabla = cursor.fetchall()
            
            if socios_tabla:
                rows_html = ""
                for idx, soc in enumerate(socios_tabla):
                    bg_color = "#f9f9f9" if idx % 2 == 0 else "#ffffff"
                    
                    rows_html += f"""
                    <tr style="background-color: {bg_color}; border-bottom: 1px solid #e0e0e0;">
                        <td style="padding: 10px; font-weight: bold; text-align: center;">{soc['id']}</td>
                        <td style="padding: 10px; font-weight: bold; text-align: center;">{soc['no_socio']}</td>
                        <td style="padding: 10px;">{soc['nombre_completo']}</td>
                        <td style="padding: 10px; text-align: center;">{soc['telefono']}</td>
                        <td style="padding: 10px; text-align: center; font-weight: bold; color: #0077B6;">{soc['total_predios']}</td>
                    </tr>
                    """

                table_html = f"""
                <div style="font-family: Arial, sans-serif; width: 100%; overflow-x: auto;">
                    <table style="width: 100%; border-collapse: collapse; box-shadow: 0 2px 5px rgba(0,0,0,0.1); border-radius: 6px; overflow: hidden;">
                        <thead>
                            <tr style="background-color: #0D3B66; color: #ffffff; text-align: left; font-size: 14px;">
                                <th style="padding: 12px; text-align: center; width: 50px;">ID</th>
                                <th style="padding: 12px; text-align: center; width: 120px;">Clave / Socio</th>
                                <th style="padding: 12px;">Nombre Completo</th>
                                <th style="padding: 12px; text-align: center;">Teléfono</th>
                                <th style="padding: 12px; text-align: center; width: 120px;">Total Predios</th>
                            </tr>
                        </thead>
                        <tbody style="font-size: 13px; color: #333333;">
                            {rows_html}
                        </tbody>
                    </table>
                </div>
                """
                
                import streamlit.components.v1 as components
                altura_tabla = max(200, (len(socios_tabla) * 42) + 60)
                components.html(table_html, height=altura_tabla, scrolling=True)
            else:
                st.info("No hay socios registrados en el sistema.")
        except Exception as e:
            st.error(f"Error al cargar el listado de socios: {e}")
        finally:
            conn.close()

    with cat3:
        st.subheader("💵 Catálogo de Cuotas Mensuales")
        
        if rol in ["Administrador General", "Supervisor"]:
            with st.form("form_cuotas", clear_on_submit=True):
                col_q1, col_q2 = st.columns(2)
                concepto_i = col_q1.text_input("Concepto de la Cuota *", value="Cuota Mensual Por Predio")
                monto_i = col_q2.number_input("Monto por Predio ($) *", value=50.0, step=5.0, min_value=1.0)
                
                if st.form_submit_button("➕ Registrar Nueva Cuota", use_container_width=True):
                    if not concepto_i.strip():
                        st.warning("⚠️ El concepto de la cuota no puede estar vacío.")
                    else:
                        conn = get_connection()
                        try:
                            with conn.cursor() as cursor:
                                cursor.execute("UPDATE cuotas SET activa = 0 WHERE activa = 1")
                                cursor.execute(
                                    "INSERT INTO cuotas (concepto, monto, activa) VALUES (%s, %s, 1)",
                                    (concepto_i.strip(), monto_i)
                                )
                                conn.commit()
                                st.success(f"✅ Nueva cuota de **${monto_i:,.2f}** ('{concepto_i.strip()}') registrada y establecida como activa.")
                                st.rerun()
                        except Exception as e:
                            st.error(f"Error al registrar la cuota: {e}")
                        finally:
                            conn.close()

        st.markdown("---")
        st.subheader("📋 Historial de Cuotas Registradas")
        
        conn = get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        id, 
                        concepto, 
                        monto, 
                        activa
                    FROM cuotas 
                    ORDER BY id DESC
                """)
                cuotas_lista = cursor.fetchall()
            
            if cuotas_lista:
                rows_html = ""
                for idx, c in enumerate(cuotas_lista):
                    bg_color = "#f9f9f9" if idx % 2 == 0 else "#ffffff"
                    
                    if c['activa'] == 1:
                        estado_str = "<span style='color:#2E7D32; font-weight:bold;'>🟢 ACTIVA (VIGENTE)</span>"
                    else:
                        estado_str = "<span style='color:#757575;'>⚪ Inactiva (Histórico)</span>"
                    
                    rows_html += f"""
                    <tr style="background-color: {bg_color}; border-bottom: 1px solid #e0e0e0;">
                        <td style="padding: 10px; font-weight: bold; text-align: center;">{c['id']}</td>
                        <td style="padding: 10px;">{c['concepto']}</td>
                        <td style="padding: 10px; font-weight: bold; color: #0077B6; text-align: right;">${c['monto']:,.2f}</td>
                        <td style="padding: 10px; text-align: center;">{estado_str}</td>
                    </tr>
                    """

                table_html = f"""
                <div style="font-family: Arial, sans-serif; width: 100%; overflow-x: auto;">
                    <table style="width: 100%; border-collapse: collapse; box-shadow: 0 2px 5px rgba(0,0,0,0.1); border-radius: 6px; overflow: hidden;">
                        <thead>
                            <tr style="background-color: #0D3B66; color: #ffffff; text-align: left; font-size: 14px;">
                                <th style="padding: 12px; text-align: center; width: 60px;">ID</th>
                                <th style="padding: 12px;">Concepto</th>
                                <th style="padding: 12px; text-align: right; width: 180px;">Monto por Predio</th>
                                <th style="padding: 12px; text-align: center; width: 200px;">Estado</th>
                            </tr>
                        </thead>
                        <tbody style="font-size: 13px; color: #333333;">
                            {rows_html}
                        </tbody>
                    </table>
                </div>
                """
                
                import streamlit.components.v1 as components
                altura_tabla = max(180, (len(cuotas_lista) * 45) + 60)
                components.html(table_html, height=altura_tabla, scrolling=True)
            else:
                st.info("No hay cuotas registradas en la base de datos.")
        except Exception as e:
            st.error(f"Error al cargar el catálogo de cuotas: {e}")
        finally:
            conn.close()

# ---------------------------------------------------------
# MÓDULO 3: CAPTURA DE CUOTAS, ELIMINACIÓN Y ESTADO DE CUENTA
# ---------------------------------------------------------
elif tab_seleccionada == "📝 Captura de Cuotas":
    st.header("📝 Captura, Registro y Estado de Cuenta de Socios")

    tab_cap1, tab_cap2 = st.tabs(["💳 Captura y Matriz de Pagos", "📄 Imprimir Estado de Cuenta (PDF)"])

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT id, no_socio, nombre_completo, CONCAT(IFNULL(no_socio, 'S/C'), ' - ', nombre_completo) as socio 
                FROM socios 
                ORDER BY nombre_completo ASC
            """)
            socios_list = cursor.fetchall()
            
            cursor.execute("SELECT id, monto FROM cuotas WHERE activa = 1 ORDER BY id DESC LIMIT 1")
            cuota_act = cursor.fetchone()
    finally:
        conn.close()

    MESES_NOMBRES = {
        1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril",
        5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto",
        9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"
    }

    if socios_list:
        # =========================================================
        # PESTAÑA 1: CAPTURA, MATRIZ Y ELIMINACIÓN DE PAGOS
        # =========================================================
        with tab_cap1:
            socio_sel = st.selectbox("Seleccione el Socio a consultar:", options=socios_list, format_func=lambda x: x['socio'], key="sb_socio_cap1")
            
            if socio_sel:
                conn = get_connection()
                try:
                    with conn.cursor() as cursor:
                        cursor.execute("""
                            SELECT p.id, p.num_predio, l.comunidad, l.estado 
                            FROM predios p 
                            JOIN localidades l ON p.localidad_id = l.id 
                            WHERE p.socio_id = %s
                            ORDER BY p.id ASC
                        """, (socio_sel['id'],))
                        predios_socio = cursor.fetchall()
                finally:
                    conn.close()

                # ---------------------------------------------------------
                # 1. MATRIZ VISUAL DE CUMPLIMIENTO
                # ---------------------------------------------------------
                st.markdown("---")
                st.subheader("📊 Matriz de Cumplimiento de Pagos")
                c_a1, c_a2 = st.columns([1, 3])
                anio_matriz = c_a1.number_input("Año a consultar:", min_value=2020, max_value=2030, value=2026, key="ni_anio_mat")

                if predios_socio:
                    conn = get_connection()
                    try:
                        with conn.cursor() as cursor:
                            cursor.execute("""
                                SELECT pg.predio_id, pg.mes, pg.monto_pagado
                                FROM pagos pg
                                JOIN predios p ON pg.predio_id = p.id
                                WHERE p.socio_id = %s AND pg.anio = %s
                            """, (socio_sel['id'], anio_matriz))
                            pagos_existentes = cursor.fetchall()
                            pagados_set = {(p['predio_id'], p['mes']): p['monto_pagado'] for p in pagos_existentes}
                    finally:
                        conn.close()

                    rows_matriz = ""
                    for p in predios_socio:
                        cols_meses = ""
                        for m in range(1, 13):
                            monto_p = pagados_set.get((p['id'], m))
                            if monto_p is not None:
                                cols_meses += f'<td style="padding: 8px; text-align: center; background-color: #E8F5E9; color: #2E7D32; font-weight: bold; border: 1px solid #c8e6c9;">🟢 ${monto_p:,.0f}</td>'
                            else:
                                cols_meses += '<td style="padding: 8px; text-align: center; background-color: #FFEBEE; color: #C62828; font-size: 11px; border: 1px solid #ffcdd2;">🔴 Pendiente</td>'

                        rows_matriz += f"""
                        <tr>
                            <td style="padding: 8px; font-weight: bold; background-color: #f5f5f5; border: 1px solid #dddddd;">{p['num_predio']}</td>
                            {cols_meses}
                        </tr>
                        """

                    headers_meses = "".join([f'<th style="padding: 8px; text-align: center; border: 1px solid #dddddd;">{MESES_NOMBRES[m][:3]}</th>' for m in range(1, 13)])
                    
                    tabla_matriz_html = f"""
                    <div style="font-family: Arial, sans-serif; width: 100%; overflow-x: auto;">
                        <table style="width: 100%; border-collapse: collapse; font-size: 12px; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.08);">
                            <thead>
                                <tr style="background-color: #0D3B66; color: #ffffff;">
                                    <th style="padding: 8px; border: 1px solid #dddddd;">Predio</th>
                                    {headers_meses}
                                </tr>
                            </thead>
                            <tbody>
                                {rows_matriz}
                            </tbody>
                        </table>
                    </div>
                    """
                    import streamlit.components.v1 as components
                    altura_matriz = max(150, (len(predios_socio) * 40) + 55)
                    components.html(tabla_matriz_html, height=altura_matriz, scrolling=True)

                # ---------------------------------------------------------
                # 2. CAPTURA DE PAGOS RETROACTIVOS
                # ---------------------------------------------------------
                st.markdown("---")
                st.subheader("💳 Registrar Pago de Meses (Pasados o Actuales)")
                with st.form("form_pago_retroactivo_mod"):
                    col_f1, col_f2 = st.columns(2)
                    anio_cobro = col_f1.number_input("Año del Pago", min_value=2020, max_value=2030, value=2026, key="ni_anio_cobro")
                    meses_seleccionados = col_f2.multiselect(
                        "Selecciona Mes(es) a Pagar * (puedes marcar varios)",
                        options=list(MESES_NOMBRES.keys()),
                        format_func=lambda x: f"{x} - {MESES_NOMBRES[x]}",
                        default=[datetime.now().month],
                        key="ms_meses_cobro"
                    )
                    
                    monto_sugerido = cuota_act['monto'] if cuota_act else 50.0
                    st.info(f"💡 **Cuota activa por mes/predio:** `${monto_sugerido:,.2f}`")

                    st.write("**Selecciona los Predios a aplicar el pago:**")
                    predios_a_pagar = []
                    for pr in predios_socio:
                        chk = st.checkbox(f"📍 Predio `{pr['num_predio']}` ({pr['comunidad']})", value=True, key=f"chk_p_mod_{pr['id']}")
                        if chk:
                            predios_a_pagar.append(pr)

                    total_cuotas = len(meses_seleccionados) * len(predios_a_pagar)
                    total_monto_cobro = total_cuotas * monto_sugerido
                    st.markdown(f"### 💵 Total a Cobrar: **${total_monto_cobro:,.2f}** ({total_cuotas} mensualidad/es)")

                    if st.form_submit_button("🚀 Registrar Pago", use_container_width=True):
                        if not cuota_act:
                            st.error("⚠️ No hay cuota activa en el catálogo.")
                        elif not meses_seleccionados or not predios_a_pagar:
                            st.warning("⚠️ Selecciona al menos un mes y un predio.")
                        else:
                            conn = get_connection()
                            reg_ok, reg_dup = 0, 0
                            try:
                                with conn.cursor() as cursor:
                                    for pr in predios_a_pagar:
                                        for m_num in meses_seleccionados:
                                            try:
                                                cursor.execute("""
                                                    INSERT INTO pagos (predio_id, cuota_id, anio, mes, monto_pagado, capturado_por)
                                                    VALUES (%s, %s, %s, %s, %s, %s)
                                                """, (pr['id'], cuota_act['id'], anio_cobro, m_num, monto_sugerido, current_user['usuario']))
                                                reg_ok += 1
                                            except pymysql.err.IntegrityError:
                                                reg_dup += 1
                                    conn.commit()
                                    if reg_ok > 0:
                                        st.success(f"🎉 Se registraron {reg_ok} pago(s) correctamente.")
                                    if reg_dup > 0:
                                        st.warning(f"⚠️ {reg_dup} pago(s) ya existían previamente y fueron omitidos.")
                                    st.rerun()
                            except Exception as e:
                                st.error(f"Error al registrar pago: {e}")
                            finally:
                                conn.close()

                # ---------------------------------------------------------
                # 3. HISTORIAL Y ELIMINACIÓN DE PAGOS INCORRECTOS
                # ---------------------------------------------------------
                st.markdown("---")
                st.subheader("📜 Historial de Pagos y Cancelación de Capturas")
                
                conn = get_connection()
                try:
                    with conn.cursor() as cursor:
                        cursor.execute("""
                            SELECT 
                                pg.id as pago_id,
                                p.num_predio,
                                pg.anio,
                                pg.mes,
                                pg.monto_pagado,
                                IFNULL(DATE_FORMAT(pg.fecha_pago, '%%Y-%%m-%%d %%H:%%i'), 'N/A') as fecha_pago,
                                pg.capturado_por
                            FROM pagos pg
                            JOIN predios p ON pg.predio_id = p.id
                            WHERE p.socio_id = %s
                            ORDER BY pg.anio DESC, pg.mes DESC, p.num_predio ASC
                        """, (socio_sel['id'],))
                        historial_pagos = cursor.fetchall()

                    if historial_pagos:
                        rows_html = ""
                        for idx, h in enumerate(historial_pagos):
                            bg_color = "#f9f9f9" if idx % 2 == 0 else "#ffffff"
                            rows_html += f"""
                            <tr style="background-color: {bg_color}; border-bottom: 1px solid #e0e0e0;">
                                <td style="padding: 8px; font-weight: bold; text-align: center;">{h['pago_id']}</td>
                                <td style="padding: 8px; font-weight: bold; text-align: center;">{h['num_predio']}</td>
                                <td style="padding: 8px; text-align: center;">{h['anio']}</td>
                                <td style="padding: 8px; text-align: center;">{h['mes']} ({MESES_NOMBRES.get(h['mes'], h['mes'])})</td>
                                <td style="padding: 8px; font-weight: bold; color: #0077B6; text-align: right;">${h['monto_pagado']:,.2f}</td>
                                <td style="padding: 8px; text-align: center;">{h['fecha_pago']}</td>
                                <td style="padding: 8px; text-align: center;">{h['capturado_por']}</td>
                            </tr>
                            """

                        table_html = f"""
                        <div style="font-family: Arial, sans-serif; width: 100%; overflow-x: auto;">
                            <table style="width: 100%; border-collapse: collapse; box-shadow: 0 2px 5px rgba(0,0,0,0.1); border-radius: 6px;">
                                <thead>
                                    <tr style="background-color: #0D3B66; color: #ffffff; font-size: 13px;">
                                        <th style="padding: 10px; text-align: center;">ID Pago</th>
                                        <th style="padding: 10px; text-align: center;">Predio</th>
                                        <th style="padding: 10px; text-align: center;">Año</th>
                                        <th style="padding: 10px; text-align: center;">Mes</th>
                                        <th style="padding: 10px; text-align: right;">Monto Pagado</th>
                                        <th style="padding: 10px; text-align: center;">Fecha Registro</th>
                                        <th style="padding: 10px; text-align: center;">Capturado Por</th>
                                    </tr>
                                </thead>
                                <tbody style="font-size: 12px; color: #333333;">
                                    {rows_html}
                                </tbody>
                            </table>
                        </div>
                        """
                        altura_tabla = max(180, (len(historial_pagos) * 40) + 60)
                        components.html(table_html, height=altura_tabla, scrolling=True)

                        # Formulario de eliminación de pago
                        if rol in ["Administrador General", "Supervisor"]:
                            st.markdown("##### 🗑️ Cancelar / Eliminar un Pago Capturado Incorrectamente")
                            pago_dict = {f"ID Pago #{h['pago_id']} | Predio: {h['num_predio']} | Periodo: {h['mes']}/{h['anio']} | Monto: ${h['monto_pagado']:,.2f}": h['pago_id'] for h in historial_pagos}
                            
                            c_del1, c_del2 = st.columns([3, 1])
                            pago_del_sel = c_del1.selectbox("Selecciona el Pago a Eliminar:", list(pago_dict.keys()), key="sb_pago_del")
                            
                            if c_del2.button("🔴 Eliminar Pago", use_container_width=True, key="btn_del_pago"):
                                id_pago_borrar = pago_dict[pago_del_sel]
                                conn = get_connection()
                                try:
                                    with conn.cursor() as cursor:
                                        cursor.execute("DELETE FROM pagos WHERE id = %s", (id_pago_borrar,))
                                        conn.commit()
                                        st.success(f"✅ El pago #{id_pago_borrar} fue eliminado correctamente.")
                                        st.rerun()
                                except Exception as e:
                                    st.error(f"Error al eliminar pago: {e}")
                                finally:
                                    conn.close()
                except Exception as e:
                    st.error(f"Error al cargar historial: {e}")
                finally:
                    conn.close()
# =========================================================
        # PESTAÑA 2: IMPRESIÓN DE ESTADO DE CUENTA POR SOCIO Y PREDIO
        # =========================================================
        with tab_cap2:
            st.subheader("🖨️ Estado de Cuenta Oficial (Desglose por Socio y Predios)")
            socio_sel_ec = st.selectbox(
                "Seleccione el Socio para generar Estado de Cuenta:", 
                options=socios_list, 
                format_func=lambda x: x['socio'], 
                key="sb_socio_ec"
            )
            
            if socio_sel_ec:
                conn = get_connection()
                try:
                    with conn.cursor() as cursor:
                        # 1. Información General del Socio
                        cursor.execute("SELECT id, no_socio, nombre_completo, telefono FROM socios WHERE id = %s", (socio_sel_ec['id'],))
                        datos_socio = cursor.fetchone()

                        # 2. Obtener la lista de todos los predios del socio
                        cursor.execute("""
                            SELECT p.id, p.num_predio, l.comunidad, l.estado 
                            FROM predios p 
                            JOIN localidades l ON p.localidad_id = l.id 
                            WHERE p.socio_id = %s 
                            ORDER BY p.num_predio ASC
                        """, (socio_sel_ec['id'],))
                        lista_predios_ec = cursor.fetchall()

                        # 3. Consultar todos los pagos del socio agrupados por predio
                        cursor.execute("""
                            SELECT pg.predio_id, p.num_predio, pg.anio, pg.mes, pg.monto_pagado, 
                                   IFNULL(DATE_FORMAT(pg.fecha_pago, '%%d-%%m-%%Y %%H:%%i'), 'N/A') as fecha
                            FROM pagos pg
                            JOIN predios p ON pg.predio_id = p.id
                            WHERE p.socio_id = %s
                            ORDER BY p.num_predio ASC, pg.anio DESC, pg.mes DESC
                        """, (socio_sel_ec['id'],))
                        todos_los_pagos = cursor.fetchall()
                finally:
                    conn.close()

                # Mapear pagos por ID de Predio
                pagos_por_predio = {}
                for p_idx in lista_predios_ec:
                    pagos_por_predio[p_idx['id']] = []
                
                total_general_socio = 0.0
                total_cuotas_socio = 0

                for pg in todos_los_pagos:
                    p_id = pg['predio_id']
                    if p_id in pagos_por_predio:
                        pagos_por_predio[p_id].append(pg)
                        total_general_socio += float(pg['monto_pagado'])
                        total_cuotas_socio += 1

                fecha_generacion_str = datetime.now().strftime('%d-%m-%Y a las %H:%M:%S hrs')
                
                st.info("🔒 **Instrucciones:** Presione **Ctrl + P** en su navegador y elija 'Guardar como PDF' para generar la versión impresa inmutable.")

                # Construir bloques HTML para cada predio
                bloques_predios_html = ""
                
                for idx_pr, pr in enumerate(lista_predios_ec):
                    pagos_p = pagos_por_predio.get(pr['id'], [])
                    total_monto_predio = sum([float(x['monto_pagado']) for x in pagos_p])
                    total_cuotas_predio = len(pagos_p)

                    rows_p_html = ""
                    for dp in pagos_p:
                        rows_p_html += f"""
                        <tr style="border-bottom: 1px solid #eeeeee;">
                            <td style="padding: 7px; text-align: center; font-weight: bold;">{dp['num_predio']}</td>
                            <td style="padding: 7px; text-align: center;">{dp['anio']}</td>
                            <td style="padding: 7px; text-align: center;">{MESES_NOMBRES.get(dp['mes'], dp['mes'])}</td>
                            <td style="padding: 7px; text-align: right; font-weight: bold; color: #0077B6;">${dp['monto_pagado']:,.2f}</td>
                            <td style="padding: 7px; text-align: center;">{dp['fecha']}</td>
                        </tr>
                        """

                    if not rows_p_html:
                        rows_p_html = '<tr><td colspan="5" style="padding:12px; text-align:center; color:#888;">Sin pagos registrados para este predio.</td></tr>'

                    bloques_predios_html += f"""
                    <div style="background-color: #ffffff; border: 1.5px solid #0D3B66; border-radius: 6px; padding: 15px; margin-bottom: 25px; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
                        <div style="display: flex; justify-content: space-between; align-items: center; background-color: #0D3B66; color: white; padding: 10px 15px; border-radius: 4px; margin-bottom: 15px;">
                            <div>
                                <span style="font-size: 14px; font-weight: bold;">📍 PREDIO #{idx_pr + 1}: {pr['num_predio']}</span>
                                <span style="font-size: 12px; margin-left: 10px; color: #E0F2FE;">({pr['comunidad']}, {pr['estado']})</span>
                            </div>
                            <div style="text-align: right; font-size: 13px;">
                                Total Predio: <strong>${total_monto_predio:,.2f} MXN</strong> ({total_cuotas_predio} cuotas)
                            </div>
                        </div>

                        <table style="width: 100%; border-collapse: collapse; font-size: 12px;">
                            <thead>
                                <tr style="background-color: #F1F5F9; color: #0D3B66; border-bottom: 2px solid #CBD5E1;">
                                    <th style="padding: 8px; text-align: center;">Identificador</th>
                                    <th style="padding: 8px; text-align: center;">Año Ejercicio</th>
                                    <th style="padding: 8px; text-align: center;">Mes Pagado</th>
                                    <th style="padding: 8px; text-align: right;">Monto Aportado</th>
                                    <th style="padding: 8px; text-align: center;">Fecha de Registro</th>
                                </tr>
                            </thead>
                            <tbody>
                                {rows_p_html}
                            </tbody>
                        </table>
                    </div>
                    """

                estado_cuenta_html = f"""
                <div style="font-family: Arial, sans-serif; background-color: #ffffff; padding: 25px; border: 2px solid #0D3B66; border-radius: 8px; max-width: 900px; margin: auto;">
                    
                    <!-- ENCABEZADO Y FECHA DE EMISIÓN -->
                    <div style="background-color: #F8FAFC; border: 2px solid #0D3B66; padding: 10px; border-radius: 6px; text-align: center; margin-bottom: 20px;">
                        <span style="font-size: 11px; color: #64748B; font-weight: bold; text-transform: uppercase;">📅 FECHA Y HORA OFICIAL DE GENERACIÓN</span><br>
                        <span style="font-size: 18px; color: #0D3B66; font-weight: 800;">{fecha_generacion_str}</span>
                    </div>

                    <div style="display: flex; justify-content: space-between; border-bottom: 2px solid #0D3B66; padding-bottom: 15px; margin-bottom: 20px;">
                        <div>
                            <h2 style="color: #0D3B66; margin: 0;">ANMIRA - SISTEMA DE CONTROL DE CUOTAS</h2>
                            <p style="margin: 5px 0 0 0; color: #555555; font-size: 14px;"><strong>ESTADO DE CUENTA INDIVIDUAL POR SOCIO Y PREDIOS</strong></p>
                        </div>
                        <div style="text-align: right; font-size: 12px; color: #666666;">
                            <p style="margin: 0; background-color: #0D3B66; color: white; padding: 4px 8px; border-radius: 4px; display: inline-block;"><strong>REPORTE PDF INMUTABLE</strong></p>
                            <p style="margin: 5px 0 0 0;">Estatus Socio: <span style="color: green; font-weight: bold;">ACTIVO</span></p>
                        </div>
                    </div>

                    <!-- RESUMEN DEL SOCIO -->
                    <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px; font-size: 13px; background-color: #f8f9fa; border: 1px solid #dddddd;">
                        <tr>
                            <td style="padding: 10px; font-weight: bold; width: 18%;">Clave Socio:</td>
                            <td style="padding: 10px; width: 32%;">{datos_socio['no_socio'] if datos_socio['no_socio'] else 'N/A'}</td>
                            <td style="padding: 10px; font-weight: bold; width: 18%;">Teléfono:</td>
                            <td style="padding: 10px; width: 32%;">{datos_socio['telefono'] if datos_socio['telefono'] else 'N/A'}</td>
                        </tr>
                        <tr>
                            <td style="padding: 10px; font-weight: bold;">Nombre Socio:</td>
                            <td style="padding: 10px;" colspan="3"><strong style="font-size: 15px; color: #0D3B66;">{datos_socio['nombre_completo']}</strong></td>
                        </tr>
                        <tr>
                            <td style="padding: 10px; font-weight: bold;">Total Predios Registrados:</td>
                            <td style="padding: 10px;" colspan="3"><strong>{len(lista_predios_ec)} Predio(s) Activo(s)</strong></td>
                        </tr>
                    </table>

                    <!-- TARJETAS DE MÉTRICAS GENERALES -->
                    <div style="display: flex; gap: 20px; margin-bottom: 25px;">
                        <div style="flex: 1; background-color: #E8F5E9; padding: 12px; border-radius: 6px; text-align: center; border: 1px solid #c8e6c9;">
                            <span style="font-size: 11px; color: #2E7D32; font-weight: bold;">TOTAL CUOTAS PAGADAS (TODOS LOS PREDIOS)</span>
                            <h3 style="margin: 4px 0 0 0; color: #2E7D32;">{total_cuotas_socio} Aportaciones</h3>
                        </div>
                        <div style="flex: 1; background-color: #E0F7FA; padding: 12px; border-radius: 6px; text-align: center; border: 1px solid #b2ebf2;">
                            <span style="font-size: 11px; color: #0077B6; font-weight: bold;">RECAUDACIÓN TOTAL DEL SOCIO</span>
                            <h3 style="margin: 4px 0 0 0; color: #0077B6;">${total_general_socio:,.2f} MXN</h3>
                        </div>
                    </div>

                    <h3 style="color: #0D3B66; border-bottom: 2px solid #0D3B66; padding-bottom: 6px; margin-bottom: 20px;">Desglose Detallado por Predio</h3>
                    
                    {bloques_predios_html}

                    <div style="margin-top: 30px; padding-top: 15px; border-top: 1px dashed #aaaaaa; text-align: center; font-size: 11px; color: #777777;">
                        Documento oficial e inmutable emitido por el Sistema de Administración Anmira.<br>
                        Para imprimir o guardar como PDF presione <strong>Ctrl + P</strong> en su navegador.
                    </div>
                </div>
                """
                
                # Ajustar la altura del iframe dinámicamente según la cantidad de predios y pagos
                altura_ec = max(600, (len(lista_predios_ec) * 220) + (len(todos_los_pagos) * 35) + 300)
                components.html(estado_cuenta_html, height=altura_ec, scrolling=True)
    else:
        st.info("No hay socios registrados en la base de datos.")

# ---------------------------------------------------------
# MÓDULO 4: DASHBOARD, ESTADÍSTICAS Y EXPORTACIÓN A EXCEL
# ---------------------------------------------------------
elif tab_seleccionada == "📈 Dashboard y Estadísticas":
    st.header("📈 Dashboard y Métricas de Recaudación")
    
    conn = get_connection()
    try:
        df_pagos = pd.read_sql("SELECT * FROM pagos", conn)
        df_socios = pd.read_sql("SELECT * FROM socios", conn)
        df_predios = pd.read_sql("SELECT * FROM predios", conn)
    finally:
        conn.close()

    # Conversión segura a formato numérico de montos
    if not df_pagos.empty:
        df_pagos['monto_pagado'] = pd.to_numeric(df_pagos['monto_pagado'], errors='coerce').fillna(0.0)
        total_recaudado = float(df_pagos['monto_pagado'].sum())
    else:
        total_recaudado = 0.0

    # Tarjetas Métricas Principales
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Recaudado Acumulado", f"${total_recaudado:,.2f}")
    m2.metric("Socios Registrados", f"{len(df_socios):,}")
    m3.metric("Predios Activos", f"{len(df_predios):,}")
    m4.metric("Pagos Capturados", f"{len(df_pagos):,}")

    st.markdown("---")
    st.subheader("🔍 Análisis Estadístico de Cumplimiento")

    if not df_pagos.empty:
        MESES_MAP_NOMBRES = {
            1: "01-Ene", 2: "02-Feb", 3: "03-Mar", 4: "04-Abr",
            5: "05-May", 6: "06-Jun", 7: "07-Jul", 8: "08-Ago",
            9: "09-Sep", 10: "10-Oct", 11: "11-Nov", 12: "12-Dic"
        }

        col_g1, col_g2 = st.columns(2)
        
        with col_g1:
            st.subheader("📊 Recaudación Mensual Global ($)")
            df_chart = df_pagos.groupby('mes')['monto_pagado'].sum().reset_index()
            df_chart['Mes'] = df_chart['mes'].map(MESES_MAP_NOMBRES)
            df_chart = df_chart.sort_values('mes')
            st.bar_chart(df_chart, x="Mes", y="monto_pagado")

        with col_g2:
            st.subheader("🏆 Top 10 Socios con Mayor Cumplimiento")
            conn = get_connection()
            try:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        SELECT 
                            s.nombre_completo as socio, 
                            COUNT(pg.id) as total_cuotas,
                            SUM(pg.monto_pagado) as total_pagado
                        FROM pagos pg
                        JOIN predios p ON pg.predio_id = p.id
                        JOIN socios s ON p.socio_id = s.id
                        GROUP BY s.id, s.nombre_completo
                        ORDER BY total_pagado DESC
                        LIMIT 10
                    """)
                    top_socios = cursor.fetchall()

                if top_socios:
                    rows_top = ""
                    for idx, t in enumerate(top_socios):
                        bg = "#f9f9f9" if idx % 2 == 0 else "#ffffff"
                        rows_top += f"""
                        <tr style="background-color: {bg}; border-bottom: 1px solid #e0e0e0;">
                            <td style="padding: 8px; font-weight: bold; text-align: center;">#{idx+1}</td>
                            <td style="padding: 8px;">{t['socio']}</td>
                            <td style="padding: 8px; text-align: center; font-weight: bold; color: #0077B6;">{t['total_cuotas']}</td>
                            <td style="padding: 8px; text-align: right; font-weight: bold; color: #2E7D32;">${t['total_pagado']:,.2f}</td>
                        </tr>
                        """

                    html_top = f"""
                    <div style="font-family: Arial, sans-serif; width: 100%; overflow-x: auto;">
                        <table style="width: 100%; border-collapse: collapse; font-size: 13px; box-shadow: 0 2px 4px rgba(0,0,0,0.08); border-radius: 6px; overflow: hidden;">
                            <thead>
                                <tr style="background-color: #0D3B66; color: #ffffff;">
                                    <th style="padding: 10px; text-align: center; width: 40px;">#</th>
                                    <th style="padding: 10px; text-align: left;">Socio</th>
                                    <th style="padding: 10px; text-align: center; width: 90px;">Cuotas</th>
                                    <th style="padding: 10px; text-align: right; width: 110px;">Total Pagado</th>
                                </tr>
                            </thead>
                            <tbody>
                                {rows_top}
                            </tbody>
                        </table>
                    </div>
                    """
                    import streamlit.components.v1 as components
                    altura_top = max(180, (len(top_socios) * 40) + 50)
                    components.html(html_top, height=altura_top, scrolling=True)
                else:
                    st.info("Sin registros disponibles.")
            finally:
                conn.close()

        st.markdown("---")
        st.subheader("⚠️ Socios Pendientes de Pago o Menor Aportación")
        
        conn = get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        IFNULL(s.no_socio, 'S/C') as no_socio,
                        s.nombre_completo as socio, 
                        IFNULL(s.telefono, 'Sin Teléfono') as telefono,
                        COUNT(pg.id) as total_cuotas,
                        IFNULL(SUM(pg.monto_pagado), 0) as total_pagado
                    FROM socios s
                    LEFT JOIN predios p ON s.id = p.socio_id
                    LEFT JOIN pagos pg ON p.id = pg.predio_id
                    GROUP BY s.id, s.no_socio, s.nombre_completo, s.telefono
                    ORDER BY total_pagado ASC, total_cuotas ASC
                    LIMIT 10
                """)
                low_socios = cursor.fetchall()

            if low_socios:
                rows_low = ""
                for idx, l in enumerate(low_socios):
                    bg = "#f9f9f9" if idx % 2 == 0 else "#ffffff"
                    color_monto = "#C62828" if l['total_pagado'] == 0 else "#D97706"
                    
                    rows_low += f"""
                    <tr style="background-color: {bg}; border-bottom: 1px solid #e0e0e0;">
                        <td style="padding: 8px; font-weight: bold; text-align: center;">{l['no_socio']}</td>
                        <td style="padding: 8px; font-weight: bold;">{l['socio']}</td>
                        <td style="padding: 8px; text-align: center;">{l['telefono']}</td>
                        <td style="padding: 8px; text-align: center;">{l['total_cuotas']}</td>
                        <td style="padding: 8px; text-align: right; font-weight: bold; color: {color_monto};">${l['total_pagado']:,.2f}</td>
                    </tr>
                    """

                html_low = f"""
                <div style="font-family: Arial, sans-serif; width: 100%; overflow-x: auto;">
                    <table style="width: 100%; border-collapse: collapse; font-size: 13px; box-shadow: 0 2px 4px rgba(0,0,0,0.08); border-radius: 6px; overflow: hidden;">
                        <thead>
                            <tr style="background-color: #0D3B66; color: #ffffff;">
                                <th style="padding: 10px; text-align: center; width: 100px;">Clave</th>
                                <th style="padding: 10px; text-align: left;">Socio</th>
                                <th style="padding: 10px; text-align: center; width: 130px;">Teléfono</th>
                                <th style="padding: 10px; text-align: center; width: 100px;">Cuotas</th>
                                <th style="padding: 10px; text-align: right; width: 130px;">Total Aportado</th>
                            </tr>
                        </thead>
                        <tbody>
                            {rows_low}
                        </tbody>
                    </table>
                </div>
                """
                altura_low = max(180, (len(low_socios) * 40) + 50)
                components.html(html_low, height=altura_low, scrolling=True)
            else:
                st.info("Sin registros de socios disponibles.")
        finally:
            conn.close()
# =========================================================
        # SECCIÓN DE EXPORTACIÓN GENERAL A EXCEL POR RANGO DE FECHAS
        # =========================================================
        st.markdown("---")
        st.subheader("📊 Exportación General de Saldos y Pagos (Excel)")
        st.caption("Genere y descargue reportes generales o detallados seleccionando un rango personalizado de fechas (ej. Enero 2025 a Diciembre 2026).")

        MESES_NOMBRES = {
            1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril",
            5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto",
            9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"
        }

        with st.form("form_export_excel_rango"):
            st.markdown("##### 📅 Selecciona el Rango de Periodo a Consultar")
            col_r1, col_r2, col_r3, col_r4 = st.columns(4)
            
            mes_inicio = col_r1.selectbox("Mes Inicio:", options=list(MESES_NOMBRES.keys()), format_func=lambda x: MESES_NOMBRES[x], index=0, key="sb_mes_ini_ex")
            anio_inicio = col_r2.number_input("Año Inicio:", min_value=2020, max_value=2030, value=2025, key="ni_anio_ini_ex")
            
            mes_fin = col_r3.selectbox("Mes Fin:", options=list(MESES_NOMBRES.keys()), format_func=lambda x: MESES_NOMBRES[x], index=11, key="sb_mes_fin_ex")
            anio_fin = col_r4.number_input("Año Fin:", min_value=2020, max_value=2030, value=2026, key="ni_anio_fin_ex")

            tipo_reporte = st.radio(
                "Tipo de Reporte a Generar:",
                options=["📋 Resumido (Totales por Predio en el Rango)", "🗓️ Detallado Mes a Mes (Matriz Completa del Rango)"],
                key="rb_tipo_rep_rango"
            )

            btn_generar_excel = st.form_submit_button("📁 Generar y Descargar Reporte Excel", use_container_width=True)

        if btn_generar_excel:
            import io
            import openpyxl
            from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
            from openpyxl.utils import get_column_letter

            # Validar que el periodo inicial sea menor o igual al final
            periodo_inicial_num = (anio_inicio * 100) + mes_inicio
            periodo_final_num = (anio_fin * 100) + mes_fin

            if periodo_inicial_num > periodo_final_num:
                st.error("⚠️ La fecha de inicio no puede ser posterior a la fecha de fin.")
            else:
                conn = get_connection()
                try:
                    wb = openpyxl.Workbook()
                    ws = wb.active
                    
                    # Estilos corporativos
                    fill_header = PatternFill(start_color="0D3B66", end_color="0D3B66", fill_type="solid")
                    font_header = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
                    
                    fill_title = PatternFill(start_color="F8FAFC", end_color="F8FAFC", fill_type="solid")
                    font_title = Font(name="Calibri", size=14, bold=True, color="0D3B66")
                    
                    fill_zebra = PatternFill(start_color="F9FAFB", end_color="F9FAFB", fill_type="solid")
                    font_data = Font(name="Calibri", size=11, color="333333")
                    
                    font_total = Font(name="Calibri", size=11, bold=True, color="0D3B66")
                    fill_total = PatternFill(start_color="E2E8F0", end_color="E2E8F0", fill_type="solid")

                    fill_pagado = PatternFill(start_color="E8F5E9", end_color="E8F5E9", fill_type="solid")
                    font_pagado = Font(name="Calibri", size=11, color="2E7D32", bold=True)

                    border_thin = Border(
                        left=Side(style='thin', color='DDDDDD'),
                        right=Side(style='thin', color='DDDDDD'),
                        top=Side(style='thin', color='DDDDDD'),
                        bottom=Side(style='thin', color='DDDDDD')
                    )

                    rango_texto = f"{MESES_NOMBRES[mes_inicio]} {anio_inicio} a {MESES_NOMBRES[mes_fin]} {anio_fin}"

                    # =========================================================
                    # OPCIÓN 1: REPORTE RESUMIDO POR RANGO DE FECHAS
                    # =========================================================
                    if "Resumido" in tipo_reporte:
                        ws.title = "Resumen de Pagos"
                        
                        with conn.cursor() as cursor:
                            sql_ex = """
                                SELECT 
                                    IFNULL(s.no_socio, 'S/C') as no_socio,
                                    s.nombre_completo as socio,
                                    IFNULL(s.telefono, 'Sin Teléfono') as telefono,
                                    l.comunidad,
                                    l.estado,
                                    p.num_predio,
                                    COUNT(pg.id) as cuotas_pagadas,
                                    IFNULL(SUM(pg.monto_pagado), 0) as total_monto
                                FROM socios s
                                JOIN predios p ON s.id = p.socio_id
                                JOIN localidades l ON p.localidad_id = l.id
                                LEFT JOIN pagos pg ON p.id = pg.predio_id 
                                     AND ((pg.anio * 100) + pg.mes) >= %s 
                                     AND ((pg.anio * 100) + pg.mes) <= %s
                                GROUP BY s.id, s.no_socio, s.nombre_completo, s.telefono, l.comunidad, l.estado, p.id, p.num_predio
                                ORDER BY s.nombre_completo ASC, p.num_predio ASC
                            """
                            cursor.execute(sql_ex, (periodo_inicial_num, periodo_final_num))
                            rows_export = cursor.fetchall()

                        if rows_export:
                            ws.merge_cells("A1:H1")
                            ws["A1"] = "ANMIRA - REPORTES DE CONTROL DE CUOTAS Y PREDIOS (RESUMIDO)"
                            ws["A1"].font = font_title; ws["A1"].fill = fill_title

                            ws.merge_cells("A2:H2")
                            ws["A2"] = f"Rango Consultado: {rango_texto} — Fecha Emisión: {datetime.now().strftime('%d/%m/%Y %H:%M hrs')}"
                            ws["A2"].font = Font(name="Calibri", size=10, italic=True, color="666666")

                            headers = ["Clave Socio", "Nombre del Socio", "Teléfono", "Ubicación / Comunidad", "Estado", "Número Predio", "Cuotas Pagadas en Rango", "Total Aportado en Rango ($)"]
                            ws.append([])
                            ws.append(headers)

                            for col_num in range(1, len(headers) + 1):
                                cell = ws.cell(row=4, column=col_num)
                                cell.fill = fill_header; cell.font = font_header
                                cell.alignment = Alignment(horizontal="center" if col_num in [1, 3, 5, 6, 7] else "left" if col_num in [2, 4] else "right")

                            row_start = 5
                            for idx, r in enumerate(rows_export):
                                current_row = row_start + idx
                                val_cuotas = int(r['cuotas_pagadas']) if r['cuotas_pagadas'] else 0
                                val_monto = float(r['total_monto']) if r['total_monto'] else 0.0

                                ws.append([
                                    str(r['no_socio']), str(r['socio']), str(r['telefono']),
                                    str(r['comunidad']), str(r['estado']), str(r['num_predio']),
                                    val_cuotas, val_monto
                                ])

                                is_even = (idx % 2 == 0)
                                for c_idx in range(1, 9):
                                    cell = ws.cell(row=current_row, column=c_idx)
                                    cell.font = font_data; cell.border = border_thin
                                    if is_even: cell.fill = fill_zebra
                                    if c_idx in [1, 3, 5, 6]: cell.alignment = Alignment(horizontal="center")
                                    elif c_idx == 7: cell.alignment = Alignment(horizontal="center"); cell.number_format = '#,##0'
                                    elif c_idx == 8: cell.alignment = Alignment(horizontal="right"); cell.number_format = '"$"#,##0.00'

                            total_row_idx = row_start + len(rows_export)
                            ws.cell(row=total_row_idx, column=1, value="TOTAL GENERAL EN RANGO")
                            ws.merge_cells(start_row=total_row_idx, start_column=1, end_row=total_row_idx, end_column=6)
                            ws.cell(row=total_row_idx, column=7, value=f"=SUM(G{row_start}:G{total_row_idx-1})")
                            ws.cell(row=total_row_idx, column=8, value=f"=SUM(H{row_start}:H{total_row_idx-1})")

                            for c_idx in range(1, 9):
                                cell = ws.cell(row=total_row_idx, column=c_idx)
                                cell.font = font_total; cell.fill = fill_total; cell.border = border_thin
                                if c_idx == 7: cell.alignment = Alignment(horizontal="center"); cell.number_format = '#,##0'
                                elif c_idx == 8: cell.alignment = Alignment(horizontal="right"); cell.number_format = '"$"#,##0.00'

                    # =========================================================
                    # OPCIÓN 2: REPORTE DETALLADO MATRIZ POR RANGO DE FECHAS
                    # =========================================================
                    else:
                        ws.title = "Matriz Detallada Rango"

                        # Construir la lista de periodos (Mes/Año) dinámicamente
                        periodos_lista = []
                        curr_a = anio_inicio
                        curr_m = mes_inicio

                        while (curr_a * 100 + curr_m) <= periodo_final_num:
                            periodos_lista.append((curr_a, curr_m))
                            curr_m += 1
                            if curr_m > 12:
                                curr_m = 1
                                curr_a += 1

                        with conn.cursor() as cursor:
                            cursor.execute("""
                                SELECT 
                                    p.id as predio_id,
                                    IFNULL(s.no_socio, 'S/C') as no_socio,
                                    s.nombre_completo as socio,
                                    IFNULL(s.telefono, 'Sin Teléfono') as telefono,
                                    l.comunidad,
                                    l.estado,
                                    p.num_predio
                                FROM socios s
                                JOIN predios p ON s.id = p.socio_id
                                JOIN localidades l ON p.localidad_id = l.id
                                ORDER BY s.nombre_completo ASC, p.num_predio ASC
                            """)
                            lista_predios = cursor.fetchall()

                            cursor.execute("""
                                SELECT pg.predio_id, pg.anio, pg.mes, pg.monto_pagado
                                FROM pagos pg
                                JOIN predios p ON pg.predio_id = p.id
                                WHERE ((pg.anio * 100) + pg.mes) >= %s 
                                  AND ((pg.anio * 100) + pg.mes) <= %s
                            """, (periodo_inicial_num, periodo_final_num))
                            pagos_rango = cursor.fetchall()

                        # Mapa: (predio_id, anio, mes) -> monto
                        mapa_pagos = {(p['predio_id'], p['anio'], p['mes']): float(p['monto_pagado']) for p in pagos_rango}

                        if lista_predios:
                            total_columnas = 6 + len(periodos_lista) + 2
                            letra_fin_encabezado = get_column_letter(total_columnas)

                            ws.merge_cells(f"A1:{letra_fin_encabezado}1")
                            ws["A1"] = "ANMIRA - MATRIZ DETALLADA DE PAGOS POR RANGO DE FECHAS"
                            ws["A1"].font = font_title; ws["A1"].fill = fill_title

                            ws.merge_cells(f"A2:{letra_fin_encabezado}2")
                            ws["A2"] = f"Rango Consultado: {rango_texto} — Fecha Emisión: {datetime.now().strftime('%d/%m/%Y %H:%M hrs')}"
                            ws["A2"].font = Font(name="Calibri", size=10, italic=True, color="666666")

                            headers = ["Clave Socio", "Nombre del Socio", "Teléfono", "Ubicación", "Estado", "Número Predio"] + \
                                      [f"{MESES_NOMBRES[m][:3].upper()}-{a}" for a, m in periodos_lista] + \
                                      ["Total Cuotas", "Total Aportado ($)"]
                            
                            ws.append([])
                            ws.append(headers)

                            for col_num in range(1, len(headers) + 1):
                                cell = ws.cell(row=4, column=col_num)
                                cell.fill = fill_header; cell.font = font_header
                                cell.alignment = Alignment(horizontal="center" if col_num not in [2, 4] else "left")

                            row_start = 5
                            for idx, pr in enumerate(lista_predios):
                                current_row = row_start + idx
                                p_id = pr['predio_id']

                                fila = [
                                    str(pr['no_socio']), str(pr['socio']), str(pr['telefono']),
                                    str(pr['comunidad']), str(pr['estado']), str(pr['num_predio'])
                                ]

                                cuotas_p = 0
                                monto_tot_p = 0.0

                                # Evaluar dinámicamente cada mes-año del rango
                                for a, m in periodos_lista:
                                    monto_m = mapa_pagos.get((p_id, a, m))
                                    if monto_m is not None:
                                        fila.append(monto_m)
                                        cuotas_p += 1
                                        monto_tot_p += monto_m
                                    else:
                                        fila.append(0)

                                fila.append(cuotas_p)
                                fila.append(monto_tot_p)

                                ws.append(fila)

                                is_even = (idx % 2 == 0)
                                for c_idx in range(1, total_columnas + 1):
                                    cell = ws.cell(row=current_row, column=c_idx)
                                    cell.font = font_data; cell.border = border_thin
                                    if is_even: cell.fill = fill_zebra

                                    if c_idx in [1, 3, 5, 6]:
                                        cell.alignment = Alignment(horizontal="center")
                                    elif 7 <= c_idx <= (6 + len(periodos_lista)):
                                        if cell.value > 0:
                                            cell.fill = fill_pagado
                                            cell.font = font_pagado
                                            cell.alignment = Alignment(horizontal="right")
                                            cell.number_format = '"$"#,##0'
                                        else:
                                            cell.number_format = '"-"'
                                            cell.alignment = Alignment(horizontal="center")
                                    elif c_idx == total_columnas - 1:
                                        cell.alignment = Alignment(horizontal="center")
                                        cell.number_format = '#,##0'
                                    elif c_idx == total_columnas:
                                        cell.alignment = Alignment(horizontal="right")
                                        cell.number_format = '"$"#,##0.00'

                            # Totales generales por columna
                            total_row_idx = row_start + len(lista_predios)
                            ws.cell(row=total_row_idx, column=1, value="TOTAL GENERAL")
                            ws.merge_cells(start_row=total_row_idx, start_column=1, end_row=total_row_idx, end_column=6)

                            for col_m in range(7, total_columnas + 1):
                                col_letra = get_column_letter(col_m)
                                ws.cell(row=total_row_idx, column=col_m, value=f"=SUM({col_letra}{row_start}:{col_letra}{total_row_idx-1})")

                            for c_idx in range(1, total_columnas + 1):
                                cell = ws.cell(row=total_row_idx, column=c_idx)
                                cell.font = font_total; cell.fill = fill_total; cell.border = border_thin
                                if 7 <= c_idx <= (6 + len(periodos_lista)) or c_idx == total_columnas:
                                    cell.alignment = Alignment(horizontal="right")
                                    cell.number_format = '"$"#,##0.00'
                                elif c_idx == total_columnas - 1:
                                    cell.alignment = Alignment(horizontal="center")
                                    cell.number_format = '#,##0'

                    # Auto-ajuste de ancho de columnas
                    for col in ws.columns:
                        max_len = 0
                        col_letter = get_column_letter(col[0].column)
                        for cell in col:
                            if cell.row > 2 and cell.value is not None:
                                max_len = max(max_len, len(str(cell.value)))
                        ws.column_dimensions[col_letter].width = max(max_len + 3, 11)

                    buffer = io.BytesIO()
                    wb.save(buffer)
                    buffer.seek(0)

                    nombre_archivo = f"Reporte_Pagos_{anio_inicio}_{anio_fin}.xlsx"

                    st.success(f"✅ ¡Reporte generado con éxito para el rango: **{rango_texto}**!")
                    st.download_button(
                        label="📥 Descargar Reporte en Excel (.xlsx)",
                        data=buffer.getvalue(),
                        file_name=nombre_archivo,
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )
                except Exception as e:
                    st.error(f"Error al generar el reporte de Excel: {e}")
                finally:
                    conn.close()