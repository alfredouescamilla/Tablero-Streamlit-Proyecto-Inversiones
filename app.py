import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Análisis Fundamental - Acciones EUA", layout="wide")

st.title("📊 Dashboard de Análisis Fundamental — Mercado EUA")
st.caption("Datos públicos obtenidos vía Yahoo Finance (yfinance)")

# ---------- Sidebar: selección de tickers ----------
DEFAULT_TICKERS = ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA"]

st.sidebar.header("Configuración")
tickers_input = st.sidebar.text_input(
    "Tickers (separados por coma)",
    value=", ".join(DEFAULT_TICKERS)
)
tickers = [t.strip().upper() for t in tickers_input.split(",") if t.strip()]

if not tickers:
    st.warning("Ingresa al menos un ticker.")
    st.stop()

# ---------- Función de extracción de datos ----------
@st.cache_data(ttl=3600)
def get_fundamentals(ticker):
    try:
        t = yf.Ticker(ticker)
        info = t.info
        return {
            "Ticker": ticker,
            "Nombre": info.get("shortName"),
            "Sector": info.get("sector"),
            "Industria": info.get("industry"),
            "Precio": info.get("currentPrice"),
            "Market Cap (B)": round(info.get("marketCap", 0) / 1e9, 2) if info.get("marketCap") else None,
            "PER (trailing)": info.get("trailingPE"),
            "PER (forward)": info.get("forwardPE"),
            "PEG": info.get("pegRatio"),
            "P/B": info.get("priceToBook"),
            "P/S": info.get("priceToSalesTrailing12Months"),
            "EPS (trailing)": info.get("trailingEps"),
            "EPS (forward)": info.get("forwardEps"),
            "Margen Bruto": info.get("grossMargins"),
            "Margen Operativo": info.get("operatingMargins"),
            "Margen Neto": info.get("profitMargins"),
            "ROE": info.get("returnOnEquity"),
            "ROA": info.get("returnOnAssets"),
            "Deuda/Capital": info.get("debtToEquity"),
            "Current Ratio": info.get("currentRatio"),
            "Crecimiento Ingresos": info.get("revenueGrowth"),
            "Crecimiento Ganancias": info.get("earningsGrowth"),
            "Dividend Yield": info.get("dividendYield"),
            "Payout Ratio": info.get("payoutRatio"),
            "Beta": info.get("beta"),
            "52w High": info.get("fiftyTwoWeekHigh"),
            "52w Low": info.get("fiftyTwoWeekLow"),
        }
    except Exception as e:
        st.error(f"Error obteniendo datos de {ticker}: {e}")
        return None

with st.spinner("Descargando datos fundamentales..."):
    data = [get_fundamentals(t) for t in tickers]
    data = [d for d in data if d is not None]

if not data:
    st.error("No se pudo obtener información para los tickers ingresados.")
    st.stop()

df_full = pd.DataFrame(data).set_index("Ticker")

# ---------- Filtros adicionales ----------
st.sidebar.header("Filtros")

sectores_disponibles = sorted([s for s in df_full["Sector"].dropna().unique()])
sectores_sel = st.sidebar.multiselect(
    "Sector",
    options=sectores_disponibles,
    default=sectores_disponibles
)

precio_min = float(df_full["Precio"].dropna().min()) if df_full["Precio"].notna().any() else 0.0
precio_max = float(df_full["Precio"].dropna().max()) if df_full["Precio"].notna().any() else 1.0
if precio_max <= precio_min:
    precio_max = precio_min + 1
rango_precio = st.sidebar.slider(
    "Rango de precio (USD)",
    min_value=round(precio_min, 2),
    max_value=round(precio_max, 2),
    value=(round(precio_min, 2), round(precio_max, 2))
)

cap_min = float(df_full["Market Cap (B)"].dropna().min()) if df_full["Market Cap (B)"].notna().any() else 0.0
cap_max = float(df_full["Market Cap (B)"].dropna().max()) if df_full["Market Cap (B)"].notna().any() else 1.0
if cap_max <= cap_min:
    cap_max = cap_min + 1
rango_cap = st.sidebar.slider(
    "Rango de Market Cap (Billions USD)",
    min_value=round(cap_min, 2),
    max_value=round(cap_max, 2),
    value=(round(cap_min, 2), round(cap_max, 2))
)

df = df_full[
    (df_full["Sector"].isin(sectores_sel) | df_full["Sector"].isna()) &
    (df_full["Precio"].between(rango_precio[0], rango_precio[1]) | df_full["Precio"].isna()) &
    (df_full["Market Cap (B)"].between(rango_cap[0], rango_cap[1]) | df_full["Market Cap (B)"].isna())
]

if df.empty:
    st.warning("Ningún ticker cumple con los filtros seleccionados. Ajusta los filtros en la barra lateral.")
    st.stop()

tickers_filtrados = list(df.index)

# ---------- Resumen general (KPIs) ----------
st.subheader("Resumen de la selección")
k1, k2, k3, k4 = st.columns(4)
k1.metric("Acciones mostradas", len(df))
k2.metric("Market Cap total", f"${df['Market Cap (B)'].sum():,.2f}B")
per_prom = df["PER (trailing)"].dropna()
k3.metric("PER (trailing) promedio", f"{per_prom.mean():.2f}" if not per_prom.empty else "N/A")
div_prom = df["Dividend Yield"].dropna()
k4.metric("Dividend Yield promedio", f"{div_prom.mean():.4f}" if not div_prom.empty else "N/A")

st.divider()

# ---------- Tabla comparativa ----------
st.subheader("Tabla comparativa de métricas fundamentales")
st.caption("Market Cap expresado en miles de millones de USD (Billions)")
st.dataframe(df, use_container_width=True)

st.divider()

# ---------- Comparación gráfica ----------
st.subheader("Comparación gráfica")

col1, col2 = st.columns(2)

with col1:
    metric1 = st.selectbox(
        "Métrica para gráfico 1",
        ["PER (trailing)", "Market Cap (B)", "ROE", "Margen Neto", "Deuda/Capital"],
        index=0
    )
    fig1 = px.bar(df.reset_index(), x="Ticker", y=metric1, color="Ticker",
                  title=f"{metric1} por acción")
    st.plotly_chart(fig1, use_container_width=True)

with col2:
    metric2 = st.selectbox(
        "Métrica para gráfico 2",
        ["Crecimiento Ingresos", "Dividend Yield", "P/B", "P/S", "Beta"],
        index=0
    )
    fig2 = px.bar(df.reset_index(), x="Ticker", y=metric2, color="Ticker",
                  title=f"{metric2} por acción")
    st.plotly_chart(fig2, use_container_width=True)

st.divider()

# ---------- Gráficas interactivas avanzadas ----------
st.subheader("Análisis relacional entre métricas")

col3, col4 = st.columns(2)

with col3:
    ejes_disponibles = ["PER (trailing)", "ROE", "Margen Neto", "P/B", "P/S", "Crecimiento Ingresos", "Dividend Yield"]
    eje_x = st.selectbox("Eje X", ejes_disponibles, index=0)
    eje_y = st.selectbox("Eje Y", ejes_disponibles, index=1)
    df_scatter = df.reset_index().dropna(subset=[eje_x, eje_y, "Market Cap (B)"])
    if not df_scatter.empty:
        fig_scatter = px.scatter(
            df_scatter,
            x=eje_x,
            y=eje_y,
            size="Market Cap (B)",
            color="Sector",
            hover_name="Ticker",
            size_max=60,
            title=f"{eje_y} vs {eje_x} (tamaño = Market Cap en Billions)"
        )
        st.plotly_chart(fig_scatter, use_container_width=True)
    else:
        st.info("No hay suficientes datos para mostrar esta gráfica con los filtros actuales.")

with col4:
    df_tree = df.reset_index().dropna(subset=["Market Cap (B)", "Sector"])
    if not df_tree.empty:
        fig_tree = px.treemap(
            df_tree,
            path=["Sector", "Ticker"],
            values="Market Cap (B)",
            color="PER (trailing)",
            color_continuous_scale="RdBu",
            title="Distribución de Market Cap por sector (Billions USD)"
        )
        st.plotly_chart(fig_tree, use_container_width=True)
    else:
        st.info("No hay suficientes datos para mostrar el treemap con los filtros actuales.")

st.divider()

# ---------- Detalle individual ----------
st.subheader("Detalle por acción")
selected = st.selectbox("Selecciona una acción para ver más detalle", tickers_filtrados)

t = yf.Ticker(selected)

@st.cache_data(ttl=3600)
def get_history(ticker, period):
    return yf.Ticker(ticker).history(period=period)

tab1, tab2, tab3, tab4 = st.tabs(["Resumen", "Precio histórico", "Estado de Resultados", "Balance General"])

with tab1:
    info = t.info
    c1, c2, c3 = st.columns(3)
    c1.metric("Precio actual", f"${info.get('currentPrice', 'N/A')}")
    c2.metric("PER (trailing)", info.get("trailingPE", "N/A"))
    c3.metric("Market Cap", f"${round(info.get('marketCap',0)/1e9,2)}B" if info.get("marketCap") else "N/A")
    st.write(info.get("longBusinessSummary", "Sin descripción disponible."))

with tab2:
    periodo = st.selectbox("Periodo", ["1mo", "3mo", "6mo", "1y", "2y", "5y"], index=3)
    try:
        hist = get_history(selected, periodo)
        if not hist.empty:
            fig_hist = px.line(hist.reset_index(), x="Date", y="Close",
                                title=f"Precio de cierre — {selected} ({periodo})")
            st.plotly_chart(fig_hist, use_container_width=True)
        else:
            st.info("No hay datos históricos disponibles para este periodo.")
    except Exception:
        st.info("No fue posible descargar el historial de precios.")

with tab3:
    try:
        income = t.financials
        if not income.empty:
            st.caption("Cifras en miles de millones de USD (Billions)")
            st.dataframe((income / 1e9).round(3), use_container_width=True)
        else:
            st.info("No hay datos de estado de resultados disponibles.")
    except Exception:
        st.info("No hay datos de estado de resultados disponibles.")

with tab4:
    try:
        balance = t.balance_sheet
        if not balance.empty:
            st.caption("Cifras en miles de millones de USD (Billions)")
            st.dataframe((balance / 1e9).round(3), use_container_width=True)
        else:
            st.info("No hay datos de balance general disponibles.")
    except Exception:
        st.info("No hay datos de balance general disponibles.")

st.caption("⚠️ Esta información es solo con fines educativos/informativos y no constituye asesoría financiera.")
