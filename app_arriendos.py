import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Buscador de Arriendos", layout="wide", page_icon="🏡")

st.title("🏡 Dashboard de Arriendos - Esteban y Berta")
st.markdown("---")

FILE_PATH = "registro_departamentos.csv"

def load_data():
    if os.path.exists(FILE_PATH):
        df = pd.read_csv(FILE_PATH)
        
        # Formatear columna de fecha
        if "Fecha Visita" in df.columns:
            df["Fecha Visita"] = pd.to_datetime(df["Fecha Visita"], errors='coerce').dt.date
            
        # Asignar tipo texto a columnas descriptivas
        cols_texto = ["Dirección/Comuna", "Estado Visita", "Opinión Final", "Link", "Notas"]
        for col in cols_texto:
            if col in df.columns:
                df[col] = df[col].fillna("").astype(str)
                
        return df
    else:
        # Crear DataFrame vacío con estructura inicial
        df_vacio = pd.DataFrame(columns=[
            "Dirección/Comuna", "Precio", "Fecha Visita", 
            "Estado Visita", "Opinión Final", "Link", "Notas"
        ])
        cols_texto = ["Dirección/Comuna", "Estado Visita", "Opinión Final", "Link", "Notas"]
        for col in cols_texto:
            df_vacio[col] = df_vacio[col].astype(str)
        return df_vacio

df = load_data()

# Panel de métricas
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Total Opciones", len(df))
with col2:
    st.metric("Visitas Agendadas", len(df[df["Estado Visita"] == "Visita agendada"]) if not df.empty else 0)
with col3:
    st.metric("Posibles / Muy posibles", len(df[df["Opinión Final"].isin(["Posible", "Muy posible"])]) if not df.empty else 0)
with col4:
    st.metric("Descartados", len(df[df["Opinión Final"] == "Descartado"]) if not df.empty else 0)

st.markdown("### 📋 Registro Principal")
st.info("💡 **Tip:** Haz clic en el nombre de cualquier columna para ordenar. Haz doble clic en una celda para editar.")

# Definir colores según el estado de la visita y opinión
def color_filas(row):
    if row["Estado Visita"] == "Visitado":
        return ['background-color: #d4edda; color: #155724'] * len(row)
    elif row["Opinión Final"] == "Descartado":
        return ['background-color: #f8d7da; color: #721c24'] * len(row)
    elif row["Opinión Final"] == "Muy posible":
        return ['background-color: #cce5ff; color: #004085'] * len(row)
    return [''] * len(row)

if not df.empty:
    styled_df = df.style.apply(color_filas, axis=1)
else:
    styled_df = df

# Tabla interactiva
edited_df = st.data_editor(
    styled_df,
    num_rows="dynamic",
    column_config={
        "Fecha Visita": st.column_config.DateColumn(
            "📅 Fecha Visita",
            help="Abre un calendario para elegir la fecha",
            format="DD/MM/YYYY"
        ),
        "Estado Visita": st.column_config.SelectboxColumn(
            "🚦 Estado Visita",
            options=["Por contactar", "Visita agendada", "Visitado"],
            required=True,
            default="Por contactar"
        ),
        "Opinión Final": st.column_config.SelectboxColumn(
            "⭐ Opinión Final",
            options=["-", "Descartado", "Posible", "Muy posible"],
            required=True,
            default="-"
        ),
        "Precio": st.column_config.NumberColumn(
            "💰 Precio (CLP)",
            format="$ %d",
            step=10000
        ),
        "Link": st.column_config.LinkColumn("🔗 Link al aviso"),
        "Dirección/Comuna": st.column_config.TextColumn("📍 Dirección/Comuna"),
        "Notas": st.column_config.TextColumn("📝 Notas")
    },
    use_container_width=True,
    hide_index=True
)

# Guardar cambios
if st.button("💾 Guardar Cambios", type="primary"):
    edited_df.to_csv(FILE_PATH, index=False)
    st.success("¡Datos guardados!")
    st.rerun()

# Sección de próximas visitas
st.markdown("---")
st.markdown("### 🗓️ Próximas Visitas Agendadas")
if not df.empty:
    agendadas = df[df["Estado Visita"] == "Visita agendada"].copy()
    if not agendadas.empty:
        agendadas = agendadas.sort_values(by="Fecha Visita", na_position="last")
        st.dataframe(
            agendadas[["Fecha Visita", "Dirección/Comuna", "Precio", "Link"]], 
            use_container_width=True, 
            hide_index=True
        )
    else:
        st.write("No hay visitas agendadas por el momento.")