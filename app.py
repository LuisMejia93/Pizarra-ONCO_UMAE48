import streamlit as st
import pandas as pd

# --- CONFIGURACIÓN VISUAL ---
st.set_page_config(page_title="Pizarra Hospitalización", layout="wide", page_icon="🏥")

# Estilo CSS para limpiar la vista y ajustar la tabla de camas libres
st.markdown("""
<style>
    .block-container {padding-top: 1rem; padding-bottom: 0rem;}
    [data-testid="stMetricValue"] {font-size: 24px;}
    
    /* Estilo para la caja de camas libres */
    .free-beds {
        background-color: #e8f5e9;
        padding: 15px;
        border-radius: 8px;
        border: 1px solid #c8e6c9;
        color: #2e7d32;
        font-weight: bold;
        text-align: center;
        margin-bottom: 10px;
    }
</style>
""", unsafe_allow_html=True)

# --- CARGA DE DATOS ---
@st.cache_data(ttl=60)
def load_data():
    # Tu enlace CSV de la hoja PIZARRA
    url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRhMC2GYC8sSB7fc_rs-esiotsbnWzU8Qq0BXIP4xzDeHoP5FoR3I5PCPiWq8rY8_jMDt3iKJaPmitC/pub?gid=276720072&single=true&output=csv"
    
    try:
        df = pd.read_csv(url)
        
        # Limpieza de columnas
        df.columns = df.columns.str.strip().str.upper()
        rename_map = {
            'ESTANCIA HOSPITALARIA': 'ESTANCIA',
            'INGRESO POR': 'MOTIVO',
            'FECHA DE INGRESO': 'INGRESO'
        }
        df.rename(columns=rename_map, inplace=True)
        
        # Eliminar filas donde no hay paciente
        if 'PACIENTE' in df.columns:
            df = df.dropna(subset=['PACIENTE'])
        
        # Asegurar que CAMA sea numérico para los cálculos
        if 'CAMA' in df.columns:
            df['CAMA'] = pd.to_numeric(df['CAMA'], errors='coerce')

        return df
    except Exception as e:
        return pd.DataFrame()

df = load_data()

# --- INTERFAZ ---
if not df.empty:
    
    # 1. CÁLCULOS DE CAMAS (621 - 642)
    total_pacientes = len(df)
    hem_count = len(df[df['ESP'].str.contains('HEM', case=False, na=False)])
    onc_count = len(df[df['ESP'].str.contains('ONC', case=False, na=False)])
    
    # Lógica de camas vacías
    rango_camas = set(range(621, 643)) 
    camas_ocupadas = set(df['CAMA'].dropna().astype(int).unique())
    camas_libres = sorted(list(rango_camas - camas_ocupadas))
    
    # 2. ENCABEZADO Y KPIs
    st.title("🏥 Gestión de Camas")
    
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    kpi1.metric("Total Pacientes", total_pacientes)
    kpi2.metric("Hematología (HEM)", hem_count)
    kpi3.metric("Oncología (ONC)", onc_count)
    kpi4.metric("Camas Disponibles", len(camas_libres), delta=f"De {len(rango_camas)} totales")

    # Visualizador de Camas Libres
    if camas_libres:
        str_camas = ", ".join(map(str, camas_libres))
        st.markdown(f'<div class="free-beds">✨ Camas Disponibles: {str_camas}</div>', unsafe_allow_html=True)
    else:
        st.error("🚨 SIN CAMAS: El servicio está lleno (620-642 ocupadas).")

    st.divider()

    # 3. CONTENIDO PRINCIPAL
    col_tabla, col_medicos = st.columns([3, 1.2])

    # --- COLUMNA IZQUIERDA: PIZARRA DE PACIENTES ---
    with col_tabla:
        st.subheader("📋 Detalle de Pacientes")
        
        # Función de estilo SIMPLIFICADA (Solo fondo, texto normal)
        def estilo_simple(row):
            # Detectar Especialidad para el color de FONDO
            esp = str(row.get('EVAT', '')).upper()
            bg_color = 'white' # Default
            
            if 'VERDE' in esp:
                bg_color = '#e8f5e9'  # Verde menta
            elif 'ROJO' in esp:
                bg_color = '#fce4ec'  # Rosa suave

            elif 'AMARILLO' in esp:
                bg_color = '#fffde7'  # Amarillo crema suave

            # Texto siempre negro (ya no cambia por días de estancia)
            return [f'background-color: {bg_color}; color: black' for _ in row]

        # Columnas a mostrar
        cols = [c for c in ['CAMA', 'ESP', 'PACIENTE', 'EVAT','MOTIVO','ESTANCIA', 'MEDICO'] if c in df.columns]
        
        # Ordenar por número de cama
        df_sorted = df.sort_values(by='CAMA')
        
        st.dataframe(
            df_sorted[cols].style.apply(estilo_simple, axis=1)
            .format({"CAMA": "{:.0f}"}), 
            use_container_width=True,
            height=600,
            hide_index=True
        )

    # --- COLUMNA DERECHA: TABLA DE MÉDICOS ---
    with col_medicos:
        st.subheader("👨‍⚕️ Pacientes por Médico")
        
        if 'MEDICO' in df.columns:
            # Contar y ordenar
            conteo = df['MEDICO'].value_counts().reset_index()
            conteo.columns = ['Médico', 'Total']
            
            # Mostrar tabla con barra de progreso visual
            st.dataframe(
                conteo,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Médico": st.column_config.TextColumn("Médico", width="medium"),
                    "Total": st.column_config.ProgressColumn(
                        "Carga",
                        format="%d",
                        min_value=0,
                        max_value=int(conteo['Total'].max()) + 2, # Escala dinámica
                    )
                }
            )
        else:
            st.warning("No se encontró columna MEDICO")

else:

    st.warning("No hay datos para mostrar.")



