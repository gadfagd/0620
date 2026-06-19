"""
temper.py
서울(108) 관측소 일별 기온 CSV -> Streamlit 인터랙티브 대시보드

실행:
    streamlit run temper.py

필요 패키지 (requirements.txt):
    streamlit
    pandas
    numpy
    plotly

같은 폴더(또는 저장소)에 CSV 파일(ta_20260619190504.csv)이 있어야 합니다.
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# ------------------------------------------------------------------
# 0. 기본 설정
# ------------------------------------------------------------------
CSV_PATH = "ta_20260619190504.csv"
HEATWAVE_THRESHOLD = 33       # 최고기온 33도 이상 -> 폭염일
COLDWAVE_THRESHOLD = -12      # 최저기온 -12도 이하 -> 한파일
COMPLETE_YEAR_MIN_DAYS = 350  # 이 일수 이상이어야 "완전한 연도"

st.set_page_config(page_title="서울 기온 기록부, 119년", page_icon="🌡️", layout="wide")

PAPER = "#FBF8F1"
INK = "#2B2620"
INK_SOFT = "#756B58"
HEAT = "#B5402B"
COLD = "#2E5C7E"
GOLD = "#A97C26"
LINE = "#DBD2BC"


# ------------------------------------------------------------------
# 1. 데이터 로드 & 정제
# ------------------------------------------------------------------
@st.cache_data
def load_data(path):
    df = pd.read_csv(path, encoding="utf-8-sig")
    df.columns = [c.strip() for c in df.columns]
    df["날짜"] = df["날짜"].astype(str).str.strip()
    df = df[df["날짜"] != ""]
    df["날짜"] = pd.to_datetime(df["날짜"])
    df = df.rename(columns={
        "평균기온(℃)": "avg",
        "최저기온(℃)": "min",
        "최고기온(℃)": "max",
    })
    df["year"] = df["날짜"].dt.year
    df["md"] = df["날짜"].dt.strftime("%m-%d")
    return df


@st.cache_data
def build_yearly(df):
    yearly = (
        df.dropna(subset=["avg"])
        .groupby("year")
        .agg(
            avg=("avg", "mean"),
            days=("avg", "count"),
            heatwave=("max", lambda x: (x >= HEATWAVE_THRESHOLD).sum()),
            coldwave=("min", lambda x: (x <= COLDWAVE_THRESHOLD).sum()),
        )
        .reset_index()
    )
    yearly["complete"] = yearly["days"] >= COMPLETE_YEAR_MIN_DAYS
    yearly["ma10"] = yearly["avg"].rolling(10, min_periods=6).mean()
    return yearly


def linreg(x, y):
    if len(x) < 2:
        return 0.0, float(y[0]) if len(y) else 0.0
    slope, intercept = np.polyfit(x, y, 1)
    return slope, intercept


df = load_data(CSV_PATH)
yearly = build_yearly(df)
complete = yearly[yearly["complete"]]

# ------------------------------------------------------------------
# 2. 헤더 / 헤로 지표
# ------------------------------------------------------------------
st.markdown(
    f"<div style='font-family:monospace;color:{INK_SOFT};font-size:13px;"
    "letter-spacing:0.1em;'>OBSERVATION LEDGER · KMA STATION 108</div>",
    unsafe_allow_html=True,
)
st.title("서울 기온 기록부, 119년")
st.caption(
    f"기상청 서울(108) 관측소 — {df['날짜'].min().date()} ~ {df['날짜'].max().date()} "
    "일별 기온 기록입니다."
)

slope_all, intercept_all = linreg(complete["year"].values, complete["avg"].values)
y0, y1 = int(complete["year"].min()), int(complete["year"].max())
total_rise = slope_all * (y1 - y0)

first5 = complete["avg"].iloc[:5].mean()
last5 = complete["avg"].iloc[-5:].mean()
hottest = complete.loc[complete["avg"].idxmax()]
coldest = complete.loc[complete["avg"].idxmin()]

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric(f"전 기간 회귀 추세 ({y0}~{y1})", f"{total_rise:+.1f}℃")
c2.metric("최근 5년 평균", f"{last5:.1f}℃")
c3.metric(f"{y0}~{y0+4}년 평균", f"{first5:.1f}℃")
c4.metric("가장 더웠던 해", f"{int(hottest['year'])}년", f"{hottest['avg']:.1f}℃")
c5.metric("가장 추웠던 해", f"{int(coldest['year'])}년", f"{coldest['avg']:.1f}℃")

st.divider()

# ------------------------------------------------------------------
# 3. 기록 A — 연도별 추이 + 구간 회귀선
# ------------------------------------------------------------------
st.subheader("기록 A · 연평균 기온의 119년 추이")
st.caption("구간을 선택하면 그 구간만의 회귀선(추세선)을 다시 계산합니다.")

y_start, y_end = st.slider(
    "구간 선택",
    min_value=y0, max_value=y1, value=(y0, y1),
)

fig_a = go.Figure()
fig_a.add_trace(go.Scatter(
    x=complete["year"], y=complete["avg"],
    mode="lines", name="연평균 기온",
    line=dict(color=INK_SOFT, width=1.3), opacity=0.6,
))
fig_a.add_trace(go.Scatter(
    x=yearly["year"], y=yearly["ma10"],
    mode="lines", name="10년 이동평균",
    line=dict(color=GOLD, width=3),
))

sel = complete[(complete["year"] >= y_start) & (complete["year"] <= y_end)]
if len(sel) >= 2:
    s, b = linreg(sel["year"].values, sel["avg"].values)
    x_line = [sel["year"].min(), sel["year"].max()]
    y_line = [s * x + b for x in x_line]
    fig_a.add_trace(go.Scatter(
        x=x_line, y=y_line, mode="lines", name="선택 구간 회귀선",
        line=dict(color=HEAT, width=4),
    ))
    rise = s * (x_line[1] - x_line[0])
    st.markdown(
        f"**{x_line[0]}~{x_line[1]}년** ({x_line[1]-x_line[0]}년간) 회귀 추세: "
        f"연평균 **{s*10:+.2f}℃/10년** · 구간 전체 **{rise:+.1f}℃** 변화"
    )

fig_a.update_layout(
    plot_bgcolor=PAPER, paper_bgcolor=PAPER,
    font=dict(color=INK),
    xaxis=dict(gridcolor=LINE, title="연도"),
    yaxis=dict(gridcolor=LINE, title="평균기온(℃)"),
    legend=dict(orientation="h", y=1.1),
    height=420, margin=dict(t=30, b=30),
)
st.plotly_chart(fig_a, use_container_width=True)

st.divider()

# ------------------------------------------------------------------
# 4. 기록 B — 폭염일 / 한파일
# ------------------------------------------------------------------
st.subheader("기록 B · 폭염일과 한파일, 연도별 변화")
st.caption(f"최고기온 {HEATWAVE_THRESHOLD}℃ 이상 = 폭염일, 최저기온 {COLDWAVE_THRESHOLD}℃ 이하 = 한파일")

mode = st.radio("기준 선택", ["폭염일", "한파일"], horizontal=True)
key = "heatwave" if mode == "폭염일" else "coldwave"
color = HEAT if mode == "폭염일" else COLD

fig_b = go.Figure(go.Bar(
    x=complete["year"], y=complete[key],
    marker_color=color, opacity=0.8,
))
fig_b.update_layout(
    plot_bgcolor=PAPER, paper_bgcolor=PAPER,
    font=dict(color=INK),
    xaxis=dict(gridcolor=LINE, title="연도"),
    yaxis=dict(gridcolor=LINE, title="일수"),
    height=360, margin=dict(t=20, b=30),
)
st.plotly_chart(fig_b, use_container_width=True)

recent10 = complete[key].iloc[-10:].mean()
first10 = complete[key].iloc[:10].mean()
st.markdown(f"관측 초기 10년 평균 **{first10:.1f}일** → 최근 10년 평균 **{recent10:.1f}일** ({mode}/년)")

st.divider()

# ------------------------------------------------------------------
# 5. 기록 C — 그 날의 기록 (생일 조회)
# ------------------------------------------------------------------
st.subheader("기록 C · 그 날의 기록 — 날짜로 찾아보기")
st.caption("월과 일을 고르면, 그 날짜에 서울의 기온이 매년 몇 도였는지 모두 보여드립니다.")

col_m, col_d = st.columns(2)
month = col_m.selectbox("월", list(range(1, 13)), index=5)
days_in_month = [31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month - 1]
day = col_d.selectbox("일", list(range(1, days_in_month + 1)), index=18)

rows = df[(df["날짜"].dt.month == month) & (df["날짜"].dt.day == day)].dropna(subset=["avg"]).sort_values("year")

if len(rows) > 0:
    st.caption(f"{len(rows)}개 연도 기록")
    fig_c = go.Figure()
    fig_c.add_trace(go.Bar(
        x=rows["year"], y=rows["max"] - rows["min"], base=rows["min"],
        marker_color=COLD, opacity=0.35, name="최저~최고",
    ))
    fig_c.add_trace(go.Scatter(
        x=rows["year"], y=rows["avg"], mode="markers", name="평균기온",
        marker=dict(color=HEAT, size=5),
    ))
    fig_c.update_layout(
        plot_bgcolor=PAPER, paper_bgcolor=PAPER,
        font=dict(color=INK),
        xaxis=dict(gridcolor=LINE, title="연도"),
        yaxis=dict(gridcolor=LINE, title="기온(℃)"),
        height=340, margin=dict(t=20, b=30),
        showlegend=False,
    )
    st.plotly_chart(fig_c, use_container_width=True)

    hot_row = rows.loc[rows["avg"].idxmax()]
    cold_row = rows.loc[rows["avg"].idxmin()]
    avg_all = rows["avg"].mean()

    m1, m2, m3 = st.columns(3)
    m1.metric("역대 가장 더운 해", f"{hot_row['avg']:.1f}℃", f"{int(hot_row['year'])}년")
    m2.metric(f"{len(rows)}개년 평균", f"{avg_all:.1f}℃", f"{month}월 {day}일")
    m3.metric("역대 가장 추운 해", f"{cold_row['avg']:.1f}℃", f"{int(cold_row['year'])}년")
else:
    st.info("해당 날짜의 기록이 없습니다.")

st.divider()
st.caption(
    f"자료: 기상청 서울(108) 관측소 일별 기온 — "
    f"{df['날짜'].min().date()} ~ {df['날짜'].max().date()} · "
    "1907년·2026년은 일부 기간만 포함된 연도입니다"
)
