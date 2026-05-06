import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from scipy import stats
import gspread
from google.oauth2.service_account import Credentials

# ── Configuración de página ──────────────────────────────────────────────────
st.set_page_config(
    page_title="Agricultex — Dashboard Recría",
    page_icon="🐷",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── CSS personalizado ─────────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;700&family=DM+Mono&display=swap');

    html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }

    .main { background-color: #F5F7F2; }

    .metric-card {
        background: white;
        border-radius: 12px;
        padding: 16px 20px;
        box-shadow: 0 1px 4px rgba(0,0,0,0.08);
        border-left: 4px solid #2E7D32;
    }
    .metric-title { font-size: 12px; color: #666; text-transform: uppercase; letter-spacing: 0.05em; }
    .metric-value { font-size: 28px; font-weight: 700; color: #1A1A1A; }
    .metric-sub { font-size: 12px; color: #888; margin-top: 2px; }

    .dentro  { background: #E8F5E9; color: #2E7D32; padding: 3px 10px; border-radius: 20px; font-size: 12px; font-weight: 600; }
    .fuera   { background: #FFEBEE; color: #C62828; padding: 3px 10px; border-radius: 20px; font-size: 12px; font-weight: 600; }
    .alerta  { background: #FFF8E1; color: #F57F17; padding: 3px 10px; border-radius: 20px; font-size: 12px; font-weight: 600; }

    h1 { color: #1A1A1A !important; }
    .stSelectbox label { font-weight: 600; }
</style>
""", unsafe_allow_html=True)

# ── Valores estándar por semana ───────────────────────────────────────────────
STANDARD = {
    3:  6.3,
    4:  8.3,
    5:  10.6,
    6:  13.3,
    7:  16.6,
    8:  20.6,
    9:  25.1,
    10: 30.0,
    11: 35.4,
    12: 40.8,
    13: 46.5,
    14: 52.0,
    15: 57.8,
    16: 63.5,
}

# ── Carga de datos ────────────────────────────────────────────────────────────
@st.cache_data(ttl=300)
def cargar_datos_local(archivo):
    df = pd.read_excel(archivo, sheet_name='Recria')
    return df

@st.cache_data(ttl=300)
def cargar_desde_gsheets(url_o_id, json_creds):
    """Carga datos desde Google Sheets usando service account."""
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds = Credentials.from_service_account_info(json_creds, scopes=scope)
    gc = gspread.authorize(creds)
    sh = gc.open_by_url(url_o_id) if url_o_id.startswith('http') else gc.open_by_key(url_o_id)
    ws = sh.worksheet('Recria')
    data = ws.get_all_records()
    return pd.DataFrame(data)

def calcular_ic(datos, confianza=0.95):
    """Intervalo de confianza con t de Student (muestras pequeñas)."""
    n = len(datos)
    if n < 2:
        return None, None
    media = np.mean(datos)
    se = stats.sem(datos)
    t_val = stats.t.ppf((1 + confianza) / 2, df=n - 1)
    margen = t_val * se
    return media - margen, media + margen

def estado_lechon(peso, semana, ic_inf, ic_sup, std_val):
    """Determina si el lechón está dentro/fuera de la banda de confianza."""
    if ic_inf is None:
        return "Sin datos"
    if ic_inf <= peso <= ic_sup:
        return "✅ Dentro"
    elif peso < std_val * 0.85:
        return "🔴 Muy por debajo"
    elif peso < ic_inf:
        return "⚠️ Por debajo"
    else:
        return "⬆️ Por encima"

# ── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.image("https://i.imgur.com/placeholder.png", width=160) if False else None
    st.markdown("## 🐷 Agricultex")
    st.markdown("---")

    fuente = st.radio("Fuente de datos", ["📁 Archivo local", "☁️ Google Sheets"])

    df = None

    if fuente == "📁 Archivo local":
        archivo = st.file_uploader("Subí el Excel del sistema", type=["xlsx"])
        if archivo:
            df = cargar_datos_local(archivo)
            st.success(f"✅ {len(df)} registros cargados")
    else:
        st.info("Para conectar Google Sheets necesitás configurar las credenciales de servicio.")
        sheet_id = st.text_input("ID de Google Sheet")
        creds_json = st.text_area("Service Account JSON (pegá el contenido)", height=120)
        if sheet_id and creds_json:
            try:
                import json
                df = cargar_desde_gsheets(sheet_id, json.loads(creds_json))
                st.success(f"✅ {len(df)} registros cargados")
            except Exception as e:
                st.error(f"Error: {e}")

    st.markdown("---")
    confianza = st.slider("Nivel de confianza", 0.80, 0.99, 0.95, 0.01,
                          format="%.0f%%", help="Nivel de confianza para la banda (t de Student)")

# ── CONTENIDO PRINCIPAL ───────────────────────────────────────────────────────
st.markdown("# Dashboard Recría")
st.markdown("Evolución de peso por banda con intervalo de confianza")

if df is None:
    st.info("👈 Cargá los datos desde el panel lateral para comenzar.")

    # Mostrar demo con datos de ejemplo
    st.markdown("### Vista previa con datos de ejemplo")
    demo_data = []
    for semana in [3, 4, 5, 6, 7]:
        std = STANDARD[semana]
        for i in range(5):
            demo_data.append({
                'Banda': 4, 'Semana de peso': semana,
                'N° Lechon': i + 1,
                'Peso': round(std * np.random.uniform(0.85, 1.15), 2)
            })
    df = pd.DataFrame(demo_data)
    st.caption("⚠️ Mostrando datos de ejemplo — cargá tu archivo para ver datos reales")

# Asegurar tipos correctos
df['Banda'] = pd.to_numeric(df['Banda'], errors='coerce')
df['Semana de peso'] = pd.to_numeric(df['Semana de peso'], errors='coerce')
df['Peso'] = pd.to_numeric(df['Peso'], errors='coerce')
df = df.dropna(subset=['Banda', 'Semana de peso', 'Peso'])

# ── FILTROS ───────────────────────────────────────────────────────────────────
col1, col2 = st.columns([1, 3])
with col1:
    bandas_disponibles = sorted(df['Banda'].unique())
    banda_sel = st.selectbox("🏷️ Seleccioná la Banda", bandas_disponibles)

df_banda = df[df['Banda'] == banda_sel].copy()

# ── MÉTRICAS RESUMEN ──────────────────────────────────────────────────────────
semanas_banda = sorted(df_banda['Semana de peso'].unique())
ultima_semana = semanas_banda[-1] if semanas_banda else None

if ultima_semana:
    df_ult = df_banda[df_banda['Semana de peso'] == ultima_semana]
    media_actual = df_ult['Peso'].mean()
    std_actual = STANDARD.get(ultima_semana, 0)
    n_lechones = df_ult['N° Lechon'].nunique()
    indice = media_actual / std_actual if std_actual > 0 else 0

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"""<div class="metric-card">
            <div class="metric-title">Banda</div>
            <div class="metric-value">{int(banda_sel)}</div>
            <div class="metric-sub">{n_lechones} lechones</div>
        </div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""<div class="metric-card">
            <div class="metric-title">Media actual (sem {int(ultima_semana)})</div>
            <div class="metric-value">{media_actual:.2f} kg</div>
            <div class="metric-sub">Estándar: {std_actual} kg</div>
        </div>""", unsafe_allow_html=True)
    with c3:
        color = "#2E7D32" if 0.95 <= indice <= 1.05 else "#F57F17" if 0.85 <= indice < 0.95 else "#C62828"
        st.markdown(f"""<div class="metric-card" style="border-left-color:{color}">
            <div class="metric-title">Índice de rendimiento</div>
            <div class="metric-value" style="color:{color}">{indice:.2f}</div>
            <div class="metric-sub">Media / Estándar</div>
        </div>""", unsafe_allow_html=True)
    with c4:
        desv = ((media_actual - std_actual) / std_actual * 100) if std_actual > 0 else 0
        color2 = "#2E7D32" if abs(desv) <= 5 else "#F57F17" if abs(desv) <= 15 else "#C62828"
        st.markdown(f"""<div class="metric-card" style="border-left-color:{color2}">
            <div class="metric-title">Desvío del estándar</div>
            <div class="metric-value" style="color:{color2}">{desv:+.1f}%</div>
            <div class="metric-sub">Última semana registrada</div>
        </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── GRÁFICO PRINCIPAL ─────────────────────────────────────────────────────────
fig = go.Figure()

# Línea estándar
semanas_std = [s for s in range(3, 17) if s in STANDARD]
std_vals = [STANDARD[s] for s in semanas_std]
fig.add_trace(go.Scatter(
    x=semanas_std, y=std_vals,
    mode='lines+markers',
    name='Estándar',
    line=dict(color='#E53935', width=2, dash='dash'),
    marker=dict(size=6),
))

# Por cada lechón — línea individual + banda de confianza
lechones = sorted(df_banda['N° Lechon'].unique())
colores_lechones = ['#1565C0', '#2E7D32', '#6A1B9A', '#E65100', '#00695C']

for i, lechon in enumerate(lechones):
    df_l = df_banda[df_banda['N° Lechon'] == lechon].sort_values('Semana de peso')
    color = colores_lechones[i % len(colores_lechones)]
    fig.add_trace(go.Scatter(
        x=df_l['Semana de peso'], y=df_l['Peso'],
        mode='lines+markers',
        name=f'Lechón {int(lechon)}',
        line=dict(color=color, width=1.5),
        marker=dict(size=5),
        opacity=0.7,
    ))

# Banda de confianza (media ± IC) por semana
medias, ic_infs, ic_sups, semanas_plot = [], [], [], []
for semana in semanas_banda:
    datos_sem = df_banda[df_banda['Semana de peso'] == semana]['Peso'].dropna().values
    if len(datos_sem) >= 2:
        ic_inf, ic_sup = calcular_ic(datos_sem, confianza)
        medias.append(np.mean(datos_sem))
        ic_infs.append(ic_inf)
        ic_sups.append(ic_sup)
        semanas_plot.append(semana)

if semanas_plot:
    # Banda de confianza rellena
    fig.add_trace(go.Scatter(
        x=semanas_plot + semanas_plot[::-1],
        y=ic_sups + ic_infs[::-1],
        fill='toself',
        fillcolor='rgba(46,125,50,0.12)',
        line=dict(color='rgba(255,255,255,0)'),
        name=f'IC {int(confianza*100)}%',
        showlegend=True,
    ))
    # Media real
    fig.add_trace(go.Scatter(
        x=semanas_plot, y=medias,
        mode='lines+markers',
        name='Media real',
        line=dict(color='#2E7D32', width=3),
        marker=dict(size=8, symbol='diamond'),
    ))

fig.update_layout(
    title=dict(text=f'Evolución de peso — Banda {int(banda_sel)}', font=dict(size=18)),
    xaxis=dict(title='Semana de vida', tickmode='linear', dtick=1, gridcolor='#F0F0F0'),
    yaxis=dict(title='Peso (kg)', gridcolor='#F0F0F0'),
    plot_bgcolor='white',
    paper_bgcolor='white',
    legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
    height=450,
    margin=dict(l=40, r=20, t=60, b=40),
)
st.plotly_chart(fig, use_container_width=True)

# ── TABLA DETALLE ─────────────────────────────────────────────────────────────
st.markdown("### 📋 Estado por lechón — última semana registrada")

if ultima_semana and len(semanas_plot) > 0:
    ic_ult_idx = semanas_plot.index(ultima_semana) if ultima_semana in semanas_plot else -1
    ic_inf_ult = ic_infs[ic_ult_idx] if ic_ult_idx >= 0 else None
    ic_sup_ult = ic_sups[ic_ult_idx] if ic_ult_idx >= 0 else None
    std_ult = STANDARD.get(ultima_semana, 0)

    filas = []
    for lechon in lechones:
        df_l_ult = df_banda[(df_banda['N° Lechon'] == lechon) & (df_banda['Semana de peso'] == ultima_semana)]
        if not df_l_ult.empty:
            peso = df_l_ult['Peso'].values[0]
            estado = estado_lechon(peso, ultima_semana, ic_inf_ult, ic_sup_ult, std_ult)
            dif = peso - std_ult
            filas.append({
                'Lechón': int(lechon),
                'Peso (kg)': peso,
                'Estándar (kg)': std_ult,
                'Diferencia': f'{dif:+.2f} kg',
                f'IC {int(confianza*100)}% inferior': f'{ic_inf_ult:.2f}' if ic_inf_ult else '-',
                f'IC {int(confianza*100)}% superior': f'{ic_sup_ult:.2f}' if ic_sup_ult else '-',
                'Estado': estado,
            })

    if filas:
        df_tabla = pd.DataFrame(filas)
        st.dataframe(
            df_tabla,
            use_container_width=True,
            hide_index=True,
            column_config={
                'Estado': st.column_config.TextColumn('Estado', width='medium'),
                'Peso (kg)': st.column_config.NumberColumn('Peso (kg)', format='%.2f'),
            }
        )

        # Resumen
        total = len(filas)
        dentro = sum(1 for f in filas if '✅' in f['Estado'])
        fuera_abajo = sum(1 for f in filas if 'Por debajo' in f['Estado'] or 'Muy' in f['Estado'])

        c1, c2, c3 = st.columns(3)
        c1.metric("✅ Dentro de banda", f"{dentro}/{total}", f"{dentro/total*100:.0f}%")
        c2.metric("⚠️ Fuera de banda", f"{total-dentro}/{total}")
        c3.metric("🔴 Por debajo del estándar", f"{fuera_abajo}/{total}")

# ── EVOLUCIÓN COMPLETA POR LECHÓN ─────────────────────────────────────────────
with st.expander("📊 Ver evolución completa por lechón"):
    semana_sel = st.select_slider("Semana", options=semanas_banda, value=semanas_banda[-1] if semanas_banda else 3)
    df_sem = df_banda[df_banda['Semana de peso'] == semana_sel].copy()

    if not df_sem.empty:
        datos_sem = df_sem['Peso'].dropna().values
        ic_inf_s, ic_sup_s = calcular_ic(datos_sem, confianza)
        std_s = STANDARD.get(semana_sel, 0)

        df_sem['Estado'] = df_sem['Peso'].apply(
            lambda p: estado_lechon(p, semana_sel, ic_inf_s, ic_sup_s, std_s)
        )
        df_sem['vs Estándar'] = (df_sem['Peso'] - std_s).round(2)
        st.dataframe(
            df_sem[['N° Lechon', 'Peso', 'vs Estándar', 'Estado']].sort_values('N° Lechon'),
            use_container_width=True, hide_index=True
        )

# ── FOOTER ────────────────────────────────────────────────────────────────────
st.markdown("---")
st.caption("🐷 Agricultex — Sistema de Gestión de Granjas | Intervalo de confianza calculado con t de Student")
