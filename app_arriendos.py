import streamlit as st
import pandas as pd
import os
import re

st.set_page_config(page_title="Buscador de Arriendos", layout="wide", page_icon="🏡")

st.title("🏡 Dashboard de Arriendos - Esteban y Berta")
st.markdown("---")

FILE_PATH = "registro_departamentos.csv"

CORE_COLUMNS = [
    "Dirección/Comuna", "Precio", "GGCC", "Habitaciones", "Baños", "Balcón", 
    "Teléfono", "Link", "Fecha Visita", "Estado Visita", "Notas", "Opinión Final"
]

def load_data():
    if os.path.exists(FILE_PATH):
        # Forzar que la columna Teléfono se lea siempre como texto (str)
        df = pd.read_csv(FILE_PATH, dtype={"Teléfono": str})
        
        for col in CORE_COLUMNS:
            if col not in df.columns:
                if col in ["Precio", "GGCC"]:
                    df[col] = 0.0
                elif col in ["Habitaciones", "Baños"]:
                    df[col] = 0.0
                elif col == "Balcón":
                    df[col] = False
                elif col == "Fecha Visita":
                    df[col] = pd.NaT
                else:
                    df[col] = ""
                    
        if "Fecha Visita" in df.columns:
            df["Fecha Visita"] = pd.to_datetime(df["Fecha Visita"], errors='coerce').dt.date
            
        for col in ["Dirección/Comuna", "Teléfono", "Estado Visita", "Opinión Final", "Link", "Notas"]:
            df[col] = df[col].fillna("").astype(str)
            # Limpiar por si quedó algún .0 heredado del archivo anterior
            if col == "Teléfono":
                df[col] = df[col].str.replace(r'\.0$', '', regex=True)
            
        return df
    else:
        return pd.DataFrame(columns=CORE_COLUMNS)

df = load_data()

df["Mapa"] = "https://www.google.com/maps/search/?api=1&query=" + df["Dirección/Comuna"].str.replace(" ", "+")
df["WhatsApp"] = df["Teléfono"].apply(lambda x: f"https://wa.me/{re.sub(r'[^0-9]', '', str(x))}" if pd.notna(x) and str(x).strip() != "" else "")

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
st.info("💡 **Tip:** Rellena los datos, escribe la dirección y haz clic en **Guardar Cambios** para activar el mapa y asegurar que todo quede registrado.")

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

edited_df = st.data_editor(
    styled_df,
    num_rows="dynamic",
    column_order=[
        "Dirección/Comuna", "Mapa", "Precio", "GGCC", "Habitaciones", "Baños", "Balcón", 
        "Teléfono", "WhatsApp", "Link", "Fecha Visita", "Estado Visita", 
        "Notas", "Opinión Final"
    ],
    column_config={
        "Dirección/Comuna": st.column_config.TextColumn("📍 Dirección", required=True),
        "Mapa": st.column_config.LinkColumn("🗺️ Mapa", display_text="Ver"),
        "Precio": st.column_config.NumberColumn("💰 Precio", format="$ %d", step=10000, default=0),
        "GGCC": st.column_config.NumberColumn("🏢 GGCC", format="$ %d", step=5000, default=0),
        "Habitaciones": st.column_config.NumberColumn("🛏️ Hab.", min_value=0, step=1, default=1),
        "Baños": st.column_config.NumberColumn("🛁 Baños", min_value=0, step=0.5, default=1),
        "Balcón": st.column_config.CheckboxColumn("🪴 Balcón", default=False),
        "Teléfono": st.column_config.TextColumn("📞 Teléfono (+569...)"),
        "WhatsApp": st.column_config.LinkColumn("💬 WhatsApp", display_text="Abrir Chat"),
        "Link": st.column_config.LinkColumn("🔗 Aviso", display_text="Ver Link"),
        "Fecha Visita": st.column_config.DateColumn("📅 Fecha", format="DD/MM/YYYY"),
        "Estado Visita": st.column_config.SelectboxColumn("🚦 Estado", options=["Por contactar", "Espera de respuesta", "Visita agendada", "Visitado"], required=True, default="Por contactar"),
        "Notas": st.column_config.TextColumn("📝 Notas"),
        "Opinión Final": st.column_config.SelectboxColumn("⭐ Opinión", options=["-", "Descartado", "Posible", "Muy posible"], required=True, default="-")
    },
    use_container_width=True,
    hide_index=True
)

if st.button("💾 Guardar Cambios", type="primary"):
    save_df = edited_df[[col for col in CORE_COLUMNS if col in edited_df.columns]].copy()
    
    for col in ["Dirección/Comuna", "Teléfono", "Estado Visita", "Opinión Final", "Link", "Notas"]:
        if col in save_df.columns:
            save_df[col] = save_df[col].fillna("").astype(str)
            if col == "Teléfono":
                save_df[col] = save_df[col].str.replace(r'\.0$', '', regex=True)
            
    save_df.to_csv(FILE_PATH, index=False)
    st.success("¡Datos guardados con éxito!")
    st.rerun()

st.markdown("---")
st.markdown("### 🔍 Filtrar y Buscar Departamentos")
col_f1, col_f2 = st.columns(2)
with col_f1:
    f_estado = st.multiselect("Filtrar por Estado:", df["Estado Visita"].unique() if not df.empty else [])
with col_f2:
    f_opinion = st.multiselect("Filtrar por Opinión:", df["Opinión Final"].unique() if not df.empty else [])

df_filtrado = df.copy()
if f_estado:
    df_filtrado = df_filtrado[df_filtrado["Estado Visita"].isin(f_estado)]
if f_opinion:
    df_filtrado = df_filtrado[df_filtrado["Opinión Final"].isin(f_opinion)]

if f_estado or f_opinion:
    st.dataframe(df_filtrado[["Dirección/Comuna", "Precio", "GGCC", "Estado Visita", "Opinión Final", "Link"]], use_container_width=True, hide_index=True)

st.markdown("---")
st.markdown("### 🗓️ Próximas Visitas")
if not df.empty:
    agendadas = df[df["Estado Visita"] == "Visita agendada"].copy()
    if not agendadas.empty:
        agendadas = agendadas.sort_values(by="Fecha Visita", na_position="last")
        st.dataframe(agendadas[["Fecha Visita", "Dirección/Comuna", "Precio", "GGCC", "Teléfono", "Link"]], use_container_width=True, hide_index=True)
    else:
        st.write("No hay visitas agendadas por el momento.")
