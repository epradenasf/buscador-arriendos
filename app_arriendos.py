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
        
        if "Fecha Visita" in df.columns:
            df["Fecha Visita"] = pd.to_datetime(df["Fecha Visita"], errors='coerce').dt.date
            
        # Crear nuevas columnas si el CSV antiguo no las tiene
        for col in ["Habitaciones", "Baños"]:
            if col not in df.columns:
                df[col] = 0.0
        if "Balcón" not in df.columns:
            df["Balcón"] = False
        if "Dirección/Comuna" not in df.columns:
            df["Dirección/Comuna"] = ""
            
        cols_texto = ["Dirección/Comuna", "Estado Visita", "Opinión Final", "Link", "Notas"]
        for col in cols_texto:
            if col in df.columns:
                df[col] = df[col].fillna("").astype(str)
        return df
    else:
        df_vacio = pd.DataFrame(columns=[
            "Dirección/Comuna", "Precio", "Habitaciones", "Baños", "Balcón",
            "Fecha Visita", "Estado Visita", "Opinión Final", "Link", "Notas"
        ])
        cols_texto = ["Dirección/Comuna", "Estado Visita", "Opinión Final", "Link", "Notas"]
        for col in cols_texto:
            df_vacio[col] = df_vacio[col].astype(str)
        df_vacio["Habitaciones"] = df_vacio["Habitaciones"].astype(float)
        df_vacio["Baños"] = df_vacio["Baños"].astype(float)
        df_vacio["Balcón"] = df_vacio["Balcón"].astype(bool)
        return df_vacio

df = load_data()

# Generar Links de Google Maps dinámicamente según la dirección
df["Mapa"] = "https://www.google.com/maps/search/?api=1&query=" + df["Dirección/Comuna"].str.replace(" ", "+")

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

# SECCIÓN DE FILTROS
st.write("🔍 **Filtros de Búsqueda:**")
col_f1, col_f2 = st.columns(2)
with col_f1:
    f_estado = st.multiselect("Filtrar por Estado:", df["Estado Visita"].unique() if not df.empty else [])
with col_f2:
    f_opinion = st.multiselect("Filtrar por Opinión:", df["Opinión Final"].unique() if not df.empty else [])

# Aplicar filtros al DataFrame
df_filtrado = df.copy()
if f_estado:
    df_filtrado = df_filtrado[df_filtrado["Estado Visita"].isin(f_estado)]
if f_opinion:
    df_filtrado = df_filtrado[df_filtrado["Opinión Final"].isin(f_opinion)]

st.info("💡 **Tip:** Haz clic en el nombre de cualquier columna (ej. 'Precio') para ordenar. **Para eliminar una fila, asegúrate de no tener ningún filtro activo.**")

def color_filas(row):
    if row["Estado Visita"] == "Visitado":
        return ['background-color: #d4edda; color: #155724'] * len(row)
    elif row["Opinión Final"] == "Descartado":
        return ['background-color: #f8d7da; color: #721c24'] * len(row)
    elif row["Opinión Final"] == "Muy posible":
        return ['background-color: #cce5ff; color: #004085'] * len(row)
    return [''] * len(row)

if not df_filtrado.empty:
    styled_df = df_filtrado.style.apply(color_filas, axis=1)
else:
    styled_df = df_filtrado

# TABLA INTERACTIVA ACTUALIZADA
edited_df = st.data_editor(
    styled_df,
    num_rows="dynamic",
    column_config={
        "Fecha Visita": st.column_config.DateColumn("📅 Fecha", format="DD/MM/YYYY"),
        "Estado Visita": st.column_config.SelectboxColumn("🚦 Estado", options=["Por contactar", "Visita agendada", "Visitado"], required=True),
        "Opinión Final": st.column_config.SelectboxColumn("⭐ Opinión", options=["-", "Descartado", "Posible", "Muy posible"], required=True),
        "Precio": st.column_config.NumberColumn("💰 Precio (CLP)", format="$ %d", step=10000),
        "Habitaciones": st.column_config.NumberColumn("🛏️ Hab.", min_value=0, step=1),
        "Baños": st.column_config.NumberColumn("🛁 Baños", min_value=0, step=0.5),
        "Balcón": st.column_config.CheckboxColumn("🪴 Balcón"),
        "Dirección/Comuna": st.column_config.TextColumn("📍 Dirección"),
        "Mapa": st.column_config.LinkColumn("🗺️ Mapa", display_text="Ver en Mapa"),
        "Link": st.column_config.LinkColumn("🔗 Aviso"),
        "Notas": st.column_config.TextColumn("📝 Notas")
    },
    use_container_width=True,
    hide_index=True
)

if st.button("💾 Guardar Cambios", type="primary"):
    # Remover columna Mapa antes de guardar porque se genera sola
    if "Mapa" in edited_df.columns:
        edited_df = edited_df.drop(columns=["Mapa"])
    
    # Lógica de guardado seguro con filtros activos
    if f_estado or f_opinion:
        df.update(edited_df)
        nuevas_filas = edited_df[~edited_df.index.isin(df.index)]
        df = pd.concat([df, nuevas_filas])
        df.to_csv(FILE_PATH, index=False)
    else:
        edited_df.to_csv(FILE_PATH, index=False)
        
    st.success("¡Datos guardados!")
    st.rerun()

st.markdown("---")
st.markdown("### 🗓️ Próximas Visitas Agendadas")
if not df.empty:
    agendadas = df[df["Estado Visita"] == "Visita agendada"].copy()
    if not agendadas.empty:
        agendadas = agendadas.sort_values(by="Fecha Visita", na_position="last")
        st.dataframe(agendadas[["Fecha Visita", "Dirección/Comuna", "Precio", "Link"]], use_container_width=True, hide_index=True)
    else:
        st.write("No hay visitas agendadas por el momento.")
