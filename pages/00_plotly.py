import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta

# ----------------------------
# 기본 설정
# ----------------------------
st.set_page_config(
    page_title="에너지/딥테크 주식 대시보드",
    page_icon="📈",
    layout="wide",
)

# 종목 리스트 (한글명: 티커)
STOCKS = {
    "블룸에너지 (BE)": "BE",
    "플러그파워 (PLUG)": "PLUG",
    "타이고에너지 (TYGO)": "TYGO",
    "아킷퀀텀 (ARQQ)": "ARQQ",
    "프레네틱스글로벌 (PRE)": "PRE",
    "스탠더드리튬 (SLI)": "SLI",
    "솔루나홀딩스 (SLNH)": "SLNH",
}

st.title("📈 에너지/딥테크 종목 주가 대시보드")
st.caption("최근 1년간 주가 변화를 Plotly로 시각화합니다. (데이터 출처: Yahoo Finance)")

# ----------------------------
# 사이드바: 옵션
# ----------------------------
st.sidebar.header("⚙️ 옵션")

selected_names = st.sidebar.multiselect(
    "표시할 종목 선택",
    options=list(STOCKS.keys()),
    default=list(STOCKS.keys()),
)
selected_tickers = [STOCKS[name] for name in selected_names]

period_option = st.sidebar.selectbox(
    "조회 기간",
    options=["1년", "6개월", "3개월", "1개월"],
    index=0,
)
period_map = {"1년": "1y", "6개월": "6mo", "3개월": "3mo", "1개월": "1mo"}
period = period_map[period_option]

view_mode = st.sidebar.radio(
    "보기 방식",
    options=["수익률 비교 (%, 기준일=0%)", "실제 주가 (개별 차트)", "거래량 포함 (개별 차트)"],
)

st.sidebar.markdown("---")
st.sidebar.caption("데이터는 yfinance를 통해 실시간으로 불러옵니다. "
                    "장 운영 시간 외에는 최신 종가 기준일 수 있습니다.")


# ----------------------------
# 데이터 로딩 (캐시 처리)
# ----------------------------
@st.cache_data(ttl=3600, show_spinner=False)
def load_data(tickers, period):
    data = {}
    for t in tickers:
        try:
            df = yf.Ticker(t).history(period=period)
            if not df.empty:
                df.index = df.index.tz_localize(None)
                data[t] = df
        except Exception as e:
            st.warning(f"{t} 데이터를 불러오는 중 오류 발생: {e}")
    return data


if not selected_tickers:
    st.info("왼쪽 사이드바에서 하나 이상의 종목을 선택해주세요.")
    st.stop()

with st.spinner("주가 데이터를 불러오는 중입니다..."):
    stock_data = load_data(tuple(selected_tickers), period)

if not stock_data:
    st.error("선택한 종목의 데이터를 불러오지 못했습니다. 잠시 후 다시 시도해주세요.")
    st.stop()

# 이름 <-> 티커 역매핑
ticker_to_name = {v: k for k, v in STOCKS.items()}

# 색상 팔레트
COLORS = [
    "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728",
    "#9467bd", "#8c564b", "#e377c2", "#17becf",
]

# ----------------------------
# 요약 지표 (메트릭 카드)
# ----------------------------
st.subheader("📊 기간 내 등락률 요약")
cols = st.columns(len(stock_data))
for i, (ticker, df) in enumerate(stock_data.items()):
    start_price = df["Close"].iloc[0]
    end_price = df["Close"].iloc[-1]
    pct_change = (end_price - start_price) / start_price * 100
    with cols[i]:
        st.metric(
            label=ticker_to_name.get(ticker, ticker),
            value=f"${end_price:,.2f}",
            delta=f"{pct_change:+.2f}%",
        )

st.markdown("---")

# ----------------------------
# 메인 시각화
# ----------------------------
if view_mode == "수익률 비교 (%, 기준일=0%)":
    st.subheader("📈 종목별 누적 수익률 비교 (기준일 = 0%)")

    fig = go.Figure()
    for i, (ticker, df) in enumerate(stock_data.items()):
        normalized = (df["Close"] / df["Close"].iloc[0] - 1) * 100
        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=normalized,
                mode="lines",
                name=ticker_to_name.get(ticker, ticker),
                line=dict(width=2, color=COLORS[i % len(COLORS)]),
                hovertemplate="%{x|%Y-%m-%d}<br>수익률: %{y:.2f}%<extra>"
                + ticker_to_name.get(ticker, ticker) + "</extra>",
            )
        )

    fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.6)
    fig.update_layout(
        height=600,
        xaxis_title="날짜",
        yaxis_title="누적 수익률 (%)",
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        template="plotly_white",
        margin=dict(t=40, b=40),
    )
    st.plotly_chart(fig, use_container_width=True)

elif view_mode == "실제 주가 (개별 차트)":
    st.subheader("💵 종목별 실제 주가 (개별 차트)")

    n = len(stock_data)
    ncols = 2
    nrows = (n + 1) // ncols

    fig = make_subplots(
        rows=nrows, cols=ncols,
        subplot_titles=[ticker_to_name.get(t, t) for t in stock_data.keys()],
        vertical_spacing=0.12,
        horizontal_spacing=0.08,
    )

    for i, (ticker, df) in enumerate(stock_data.items()):
        row = i // ncols + 1
        col = i % ncols + 1
        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df["Close"],
                mode="lines",
                name=ticker_to_name.get(ticker, ticker),
                line=dict(width=2, color=COLORS[i % len(COLORS)]),
                showlegend=False,
                hovertemplate="%{x|%Y-%m-%d}<br>종가: $%{y:.2f}<extra></extra>",
            ),
            row=row, col=col,
        )

    fig.update_layout(
        height=350 * nrows,
        template="plotly_white",
        margin=dict(t=60, b=40),
    )
    st.plotly_chart(fig, use_container_width=True)

else:  # 거래량 포함
    st.subheader("📉 종목별 주가 + 거래량")

    selected_for_volume = st.selectbox(
        "거래량을 함께 볼 종목 선택",
        options=list(stock_data.keys()),
        format_func=lambda t: ticker_to_name.get(t, t),
    )
    df = stock_data[selected_for_volume]

    fig = make_subplots(
        rows=2, cols=1, shared_xaxes=True,
        row_heights=[0.7, 0.3],
        vertical_spacing=0.05,
        subplot_titles=(f"{ticker_to_name.get(selected_for_volume)} 주가", "거래량"),
    )

    fig.add_trace(
        go.Candlestick(
            x=df.index,
            open=df["Open"], high=df["High"],
            low=df["Low"], close=df["Close"],
            name="주가",
        ),
        row=1, col=1,
    )

    vol_colors = ["red" if df["Close"].iloc[i] < df["Open"].iloc[i] else "green"
                  for i in range(len(df))]
    fig.add_trace(
        go.Bar(x=df.index, y=df["Volume"], marker_color=vol_colors, name="거래량"),
        row=2, col=1,
    )

    fig.update_layout(
        height=650,
        template="plotly_white",
        xaxis_rangeslider_visible=False,
        showlegend=False,
        margin=dict(t=60, b=40),
    )
    st.plotly_chart(fig, use_container_width=True)

# ----------------------------
# 원본 데이터 표시 (선택)
# ----------------------------
with st.expander("🔍 원본 데이터 보기"):
    selected_for_table = st.selectbox(
        "데이터를 확인할 종목 선택",
        options=list(stock_data.keys()),
        format_func=lambda t: ticker_to_name.get(t, t),
        key="table_select",
    )
    st.dataframe(
        stock_data[selected_for_table][["Open", "High", "Low", "Close", "Volume"]]
        .sort_index(ascending=False),
        use_container_width=True,
    )

st.markdown("---")
st.caption(f"마지막 업데이트: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | "
           "본 대시보드는 정보 제공 목적이며 투자 권유가 아닙니다.")
