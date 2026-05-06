import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

st.set_page_config(
    page_title="Agricultex — Dashboard Recría",
    page_icon="🐷",
    layout="wide"
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;700&display=swap');
    html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
    .stApp { background-color: #1A1A1A; color: white; }
    section[data-testid="stSidebar"] { background-color: #111111; }
    .metric-card {
        background: #2A2A2A; border-radius: 12px; padding: 16px 20px;
        box-shadow: 0 1px 4px rgba(0,0,0,0.4); border-left: 4px solid #2E7D32;
        margin-bottom: 8px;
    }
    .metric-title { font-size: 12px; color: #AAAAAA; text-transform: uppercase; letter-spacing: 0.05em; }
    .metric-value { font-size: 26px; font-weight: 700; color: #FFFFFF; }
    .metric-sub { font-size: 12px; color: #888888; margin-top: 2px; }
    h1, h2, h3 { color: #FFFFFF !important; }
    p, li, label { color: #CCCCCC !important; }
    .stDataFrame { background-color: #2A2A2A; }
    div[data-testid="stSelectbox"] label { color: #CCCCCC !important; }
</style>
""", unsafe_allow_html=True)

SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSgxJiumgT9__PpntQZvNU-mEa7soEDOy0oQ_4vJZOjfKcBESdGlevazx5XtutLLEhVaJj74BLoRILT/pub?gid=0&single=true&output=csv"

STANDARD = {3:6.3, 4:8.3, 5:10.6, 6:13.3, 7:16.6, 8:20.6, 9:25.1, 10:30.0, 11:35.4}

@st.cache_data(ttl=300)
def cargar_datos():
    try:
        df_raw = pd.read_csv(SHEET_URL, header=None)
        header_row = None
        for i, row in df_raw.iterrows():
            if str(row[0]).strip() == 'Banda':
                header_row = i
                break
        if header_row is None:
            return None, "No se encontró la tabla"
        df = df_raw.iloc[header_row+1:].copy()
        df.columns = df_raw.iloc[header_row].values
        df = df.reset_index(drop=True)
        df = df[df['Banda'].notna() & (df['Banda'] != '')]
        for col in ['Banda', 'Semana', 'N (lechones)', 'Media (kg)', 'Desvío S',
                    'Error Est. (SE)', 'IC 95% inf', 'IC 95% sup']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        df = df.dropna(subset=['Banda', 'Semana', 'Media (kg)'])
        return df, None
    except Exception as e:
        return None, str(e)

st.markdown("# 🐷 Agricultex — Dashboard Recría")
st.markdown("Evolución de peso por banda con intervalo de confianza al 95%")
st.markdown("---")

df, error = cargar_datos()

if error:
    st.error(f"Error cargando datos: {error}")
    st.stop()

if df is None or df.empty:
    st.warning("No hay datos disponibles.")
    st.stop()

st.caption(f"✅ {len(df)} registros cargados · Se actualiza cada 5 minutos")

bandas = sorted(df['Banda'].dropna().unique().astype(int))
banda_sel = st.selectbox("🏷️ Seleccioná la Banda", bandas)

df_banda = df[df['Banda'] == banda_sel].copy().sort_values('Semana')

if df_banda.empty:
    st.warning(f"No hay datos para la Banda {banda_sel}")
    st.stop()

ultima = df_banda.iloc[-1]
std_ult = STANDARD.get(int(ultima['Semana']), None)
indice = ultima['Media (kg)'] / std_ult if std_ult else None

c1, c2, c3, c4 = st.columns(4)
with c1:
    st.markdown(f"""<div class="metric-card">
        <div class="metric-title">Banda</div>
        <div class="metric-value">{int(banda_sel)}</div>
        <div class="metric-sub">{int(df_banda['N (lechones)'].iloc[-1])} lechones</div>
    </div>""", unsafe_allow_html=True)
with c2:
    st.markdown(f"""<div class="metric-card">
        <div class="metric-title">Media última semana (Sem {int(ultima['Semana'])})</div>
        <div class="metric-value">{ultima['Media (kg)']:.2f} kg</div>
        <div class="metric-sub">Estándar: {std_ult if std_ult else 'N/D'} kg</div>
    </div>""", unsafe_allow_html=True)
with c3:
    if indice:
        color = "#2E7D32" if 0.95 <= indice <= 1.05 else "#F57F17" if 0.85 <= indice < 0.95 else "#C62828"
        st.markdown(f"""<div class="metric-card" style="border-left-color:{color}">
            <div class="metric-title">Índice Media/Estándar</div>
            <div class="metric-value" style="color:{color}">{indice:.2f}</div>
            <div class="metric-sub">1.00 = exactamente en estándar</div>
        </div>""", unsafe_allow_html=True)
with c4:
    estado_ult = str(ultima.get('Estado vs Estándar', ''))
    color_e = "#2E7D32" if "Dentro" in estado_ult else "#F57F17" if "debajo" in estado_ult.lower() else "#1565C0"
    st.markdown(f"""<div class="metric-card" style="border-left-color:{color_e}">
        <div class="metric-title">Estado última semana</div>
        <div class="metric-value" style="font-size:18px;color:{color_e}">{estado_ult}</div>
    </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

semanas_banda = df_banda['Semana'].tolist()
medias = df_banda['Media (kg)'].tolist()
ic_infs = df_banda['IC 95% inf'].tolist()
ic_sups = df_banda['IC 95% sup'].tolist()

fig = go.Figure()

fig.add_trace(go.Scatter(
    x=semanas_banda + semanas_banda[::-1],
    y=ic_sups + ic_infs[::-1],
    fill='toself',
    fillcolor='rgba(33,150,243,0.15)',
    line=dict(color='rgba(255,255,255,0)'),
    name='IC 95%',
    hoverinfo='skip',
))

semanas_std = [s for s in range(3, 12) if s in STANDARD]
fig.add_trace(go.Scatter(
    x=semanas_std, y=[STANDARD[s] for s in semanas_std],
    mode='lines+markers', name='Estándar',
    line=dict(color='#EF5350', width=2, dash='dash'),
    marker=dict(size=7),
))

fig.add_trace(go.Scatter(
    x=semanas_banda, y=medias,
    mode='lines+markers', name='Media real',
    line=dict(color='#42A5F5', width=3),
    marker=dict(size=9),
    text=[f"Sem {int(s)}<br>Media: {m:.2f} kg<br>IC: [{il:.2f}, {su:.2f}]"
          for s, m, il, su in zip(semanas_banda, medias, ic_infs, ic_sups)],
    hovertemplate='%{text}<extra></extra>',
))

fig.update_layout(
    title=dict(text=f'Evolución de peso — Banda {int(banda_sel)}', font=dict(size=18, color='white')),
    xaxis=dict(title='Semana de vida', tickmode='linear', dtick=1,
               gridcolor='#333333', color='white', titlefont=dict(color='white')),
    yaxis=dict(title='Peso (kg)', gridcolor='#333333', color='white', titlefont=dict(color='white')),
    plot_bgcolor='#1A1A1A', paper_bgcolor='#1A1A1A',
    legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1,
                font=dict(color='white')),
    height=450, margin=dict(l=40, r=20, t=60, b=40),
)
st.plotly_chart(fig, use_container_width=True)

st.markdown("### 📋 Tabla estadística por semana")
cols_mostrar = ['Semana', 'N (lechones)', 'Media (kg)', 'Desvío S',
                'Error Est. (SE)', 'IC 95% inf', 'IC 95% sup', 'Estado vs Estándar']
cols_disp = [c for c in cols_mostrar if c in df_banda.columns]
st.dataframe(df_banda[cols_disp].reset_index(drop=True), use_container_width=True, hide_index=True)

if 'Estado vs Estándar' in df_banda.columns:
    estados = df_banda['Estado vs Estándar'].tolist()
    dentro = sum(1 for e in estados if 'Dentro' in str(e))
    encima = sum(1 for e in estados if 'encima' in str(e).lower())
    debajo = sum(1 for e in estados if 'debajo' in str(e).lower())
    total = len(estados)
    c1, c2, c3 = st.columns(3)
    c1.metric("✅ Dentro de banda", f"{dentro}/{total}")
    c2.metric("⬆️ Por encima", f"{encima}/{total}")
    c3.metric("⚠️ Por debajo", f"{debajo}/{total}")

st.markdown("---")
st.caption("🐷 Agricultex — IC con t de Student (gl=n-1, α=0.05) · Datos sincronizados automáticamente")
