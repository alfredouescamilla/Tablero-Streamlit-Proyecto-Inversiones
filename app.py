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

df = pd.DataFrame(data).set_index("Ticker")

# ---------- Tabla comparativa ----------
st.subheader("Tabla comparativa de métricas fundamentales")
st.dataframe(df, use_container_width=True)

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

# ---------- Detalle individual ----------
st.subheader("Detalle por acción")
selected = st.selectbox("Selecciona una acción para ver más detalle", tickers)

t = yf.Ticker(selected)

tab1, tab2, tab3 = st.tabs(["Resumen", "Estado de Resultados", "Balance General"])

with tab1:
    info = t.info
    c1, c2, c3 = st.columns(3)
    c1.metric("Precio actual", f"${info.get('currentPrice', 'N/A')}")
    c2.metric("PER (trailing)", info.get("trailingPE", "N/A"))
    c3.metric("Market Cap", f"${round(info.get('marketCap',0)/1e9,2)}B" if info.get("marketCap") else "N/A")
    st.write(info.get("longBusinessSummary", "Sin descripción disponible."))

with tab2:
    try:
        income = t.financials
        st.dataframe(income, use_container_width=True)
    except Exception:
        st.info("No hay datos de estado de resultados disponibles.")

with tab3:
    try:
        balance = t.balance_sheet
        st.dataframe(balance, use_container_width=True)
    except Exception:
        st.info("No hay datos de balance general disponibles.")

st.caption("⚠️ Esta información es solo con fines educativos/informativos y no constituye asesoría financiera.")
