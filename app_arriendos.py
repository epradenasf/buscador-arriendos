import streamlit as st
import pandas as pd
import os
import re
import base64
import requests

st.set_page_config(page_title="Buscador de Arriendos", layout="wide", page_icon="🏡")

st.title("🏡 Dashboard de Arriendos - Esteban y Berta")
st.markdown("---")

FILE_PATH = "registro_departamentos.csv"

CORE_COLUMNS = [
    "Dirección/Comuna", "Precio", "GGCC", "Habitaciones", "Baños", "Balcón", 
    "Teléfono", "Link", "Estado Visita", "Fecha Visita", "Notas", "Opinión Final"
]

def guardar_en_github(df_a_guardar):
    df_a_guardar.to_csv(FILE_PATH, index=False)
    
    if "GITHUB_TOKEN" in st.secrets and "REPO_NAME" in st.secrets:
        token = st.secrets["GITHUB_TOKEN"]
        repo = st.secrets["REPO_NAME"]
        url = f"https://api.github.com/repos/{repo}/contents/{FILE_PATH}"
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json"
        }
        
        response = requests.get(url, headers=headers)
        sha = response.json().get("sha") if response.status_code == 200 else None
        
        with open(FILE_PATH, "rb") as f:
            content_bytes = f.read()
        content_encoded = base64.b64encode(content_bytes).decode("utf-8")
        
        data = {
            "message": "Actualización automática de arriendos desde Streamlit",
            "content": content_encoded
        }
        if sha:
            data["sha"] = sha
            
        put_response = requests.put(url, headers=headers, json=data)
        if put_response.status_code not in [200, 201]:
            st.warning("Se guardó localmente, pero hubo un problema al sincronizar con GitHub.")

def load_data():
    if os.path.exists(FILE_PATH):
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
            df["Fecha Visita"] = pd.to_datetime(df["Fecha Visita"], errors='coerce')
            
        for col in ["Dirección/Comuna", "Teléfono", "Estado Visita", "Opinión Final", "Link", "Notas"]:
            if col in df.columns:
                df[col] = df[col].fillna("").astype(str)
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
st.info("💡 **Tip:** Rellena los datos, escribe la dirección y haz clic en **Guardar Cambios** para sincronizar automáticamente con la nube.")

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
        "Teléfono", "WhatsApp", "Link", "Estado Visita", "Fecha Visita", 
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
        "Estado Visita": st.column_config.SelectboxColumn("🚦 Estado", options=["Por contactar", "Espera de respuesta", "Visita agendada", "Visitado"], required=True, default="Por contactar"),
        "Fecha Visita": st.column_config.DatetimeColumn("📅 Fecha y Hora Visita", format="DD/MM/YYYY HH:mm"),
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
            
    guardar_en_github(save_df)
    st.success("¡Datos guardados y sincronizados en la nube con éxito!")
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
    st.dataframe(
        df_filtrado[["Dirección/Comuna", "Mapa", "Precio", "GGCC", "Link"]], 
        use_container_width=True, 
        hide_index=True,
        column_config={
            "Mapa": st.column_config.LinkColumn("🗺️ Mapa", display_text="Ver"),
            "Link": st.column_config.LinkColumn("🔗 Aviso", display_text="Ver Link")
        }
    )

st.markdown("---")
st.markdown("### 🗓️ Próximas Visitas")
if not df.empty:
    agendadas = df[df["Estado Visita"] == "Visita agendada"].copy()
    if not agendadas.empty:
        agendadas = agendadas.sort_values(by="Fecha Visita", na_position="last")
        st.dataframe(
            agendadas[["Fecha Visita", "Dirección/Comuna", "Mapa", "Teléfono", "Precio", "GGCC", "Link"]], 
            use_container_width=True, 
            hide_index=True,
            column_config={
                "Fecha Visita": st.column_config.DatetimeColumn("📅 Fecha y Hora", format="DD/MM/YYYY HH:mm"),
                "Mapa": st.column_config.LinkColumn("🗺️ Mapa", display_text="Ver Mapa"),
                "Link": st.column_config.LinkColumn("🔗 Aviso", display_text="Ver Link")
            }
        )
    else:
        st.write("No hay visitas agendadas por el momento.")
