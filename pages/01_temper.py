"""
temper.py
서울(108) 관측소 일별 기온 CSV -> 인터랙티브 기온 기록부 웹앱(HTML) 생성 스크립트

사용법:
    python temper.py [입력_csv_경로] [출력_html_경로]

기본값:
    입력: ta_20260619190504.csv  (같은 폴더에 두면 됨)
    출력: seoul_temperature_ledger.html

필요 패키지:
    pip install pandas numpy
"""

import sys
import json
import numpy as np
import pandas as pd

# ------------------------------------------------------------------
# 1. 경로 설정
# ------------------------------------------------------------------
INPUT_CSV = sys.argv[1] if len(sys.argv) > 1 else "ta_20260619190504.csv"
OUTPUT_HTML = sys.argv[2] if len(sys.argv) > 2 else "seoul_temperature_ledger.html"

# 폭염 / 한파 판정 기준 (필요하면 숫자만 바꾸면 됩니다)
HEATWAVE_THRESHOLD = 33     # 최고기온 33도 이상 -> 폭염일
COLDWAVE_THRESHOLD = -12    # 최저기온 -12도 이하 -> 한파일
COMPLETE_YEAR_MIN_DAYS = 350  # 이 일수 이상 기록이 있어야 "완전한 연도"로 취급 (회귀분석에 사용)

# ------------------------------------------------------------------
# 2. 데이터 읽기 & 정제
# ------------------------------------------------------------------
def load_and_clean(path):
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
    return yearly.round(2).to_dict(orient="records")


def build_daily_lookup(df):
    daily = df.dropna(subset=["avg"]).copy()
    daily["avg"] = daily["avg"].round(1)
    daily["min"] = daily["min"].round(1)
    daily["max"] = daily["max"].round(1)
    lookup = {}
    for md, grp in daily.groupby("md"):
        lookup[md] = grp[["year", "avg", "min", "max"]].values.tolist()
    return lookup


# ------------------------------------------------------------------
# 3. HTML 템플릿 (CSS + JS 포함, 데이터만 주입)
# ------------------------------------------------------------------
HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>서울 기상관측 119년 — 기온 기록부</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Noto+Serif+KR:wght@500;700;900&family=Noto+Sans+KR:wght@400;500;700&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
<style>
  :root{
    --bg: #F6F1E4;
    --paper: #FBF8F1;
    --ink: #2B2620;
    --ink-soft: #756B58;
    --ink-faint: #A89C84;
    --heat: #B5402B;
    --heat-soft: #D9C2B4;
    --cold: #2E5C7E;
    --cold-soft: #C3D2DC;
    --gold: #A97C26;
    --line: #DBD2BC;
    --line-strong: #C8BC9F;
    --shadow: 0 1px 0 rgba(43,38,32,0.06);
  }
  *{box-sizing:border-box;}
  html,body{margin:0;padding:0;}
  body{
    background: var(--bg);
    background-image:
      radial-gradient(ellipse at top left, rgba(185,138,46,0.06), transparent 50%),
      radial-gradient(ellipse at bottom right, rgba(46,92,126,0.05), transparent 50%);
    color: var(--ink);
    font-family: 'Noto Sans KR', sans-serif;
    line-height:1.55;
    -webkit-font-smoothing:antialiased;
  }
  .wrap{ max-width: 980px; margin: 0 auto; padding: 56px 28px 90px; }

  /* ===== Header / Hero ===== */
  .ledger-head{
    display:flex; justify-content:space-between; align-items:flex-end;
    border-bottom: 2px solid var(--ink);
    padding-bottom: 14px; margin-bottom: 6px;
  }
  .eyebrow{
    font-family:'JetBrains Mono', monospace;
    font-size: 12px; letter-spacing: 0.14em; color: var(--ink-soft);
    text-transform: uppercase;
  }
  .station-id{ font-family:'JetBrains Mono', monospace; font-size:12px; color: var(--ink-faint); text-align:right;}
  h1{
    font-family:'Noto Serif KR', serif;
    font-weight: 900;
    font-size: clamp(32px, 5vw, 52px);
    margin: 10px 0 4px;
    letter-spacing: -0.01em;
  }
  .sub{ color: var(--ink-soft); font-size: 15px; margin-bottom: 36px;}

  .hero{
    position:relative;
    display:grid; grid-template-columns: 1.1fr 1fr;
    gap: 36px;
    padding: 30px 0 38px;
    border-bottom: 1px solid var(--line);
    margin-bottom: 40px;
    align-items:center;
  }
  .hero-number{ position:relative; }
  .hero-number .num{
    font-family:'Noto Serif KR', serif;
    font-weight:900;
    font-size: clamp(64px, 10vw, 108px);
    color: var(--heat);
    line-height: 0.9;
    display:inline-block;
  }
  .hero-number .deg{ font-size:0.5em; vertical-align: 0.42em; }
  .stamp{
    position:absolute; top: -8px; right: 6px;
    border: 2px solid var(--heat);
    color: var(--heat);
    border-radius: 50%;
    width: 92px; height:92px;
    display:flex; align-items:center; justify-content:center;
    font-family:'JetBrains Mono',monospace;
    font-size: 10.5px; line-height:1.25; text-align:center;
    transform: rotate(11deg);
    opacity:0.85;
    font-weight:600;
  }
  .hero-number .cap{ font-family:'Noto Sans KR',sans-serif; font-size:14px; color: var(--ink-soft); margin-top:6px; max-width: 360px;}
  .hero-side{ font-size: 14px; color: var(--ink-soft); border-left: 1px solid var(--line); padding-left: 28px;}
  .hero-side b{ color: var(--ink); }
  .hero-side .row{ display:flex; justify-content:space-between; padding: 7px 0; border-bottom: 1px dashed var(--line); font-family:'JetBrains Mono',monospace; font-size:13px;}
  .hero-side .row:last-child{ border-bottom:none; }

  /* ===== Section shell ===== */
  section{ margin-bottom: 54px; }
  .sec-head{ display:flex; align-items:baseline; gap:12px; margin-bottom: 4px;}
  .sec-tag{
    font-family:'JetBrains Mono',monospace; font-size:12px; color: var(--gold);
    border:1px solid var(--gold); border-radius:3px; padding:1px 7px; letter-spacing:0.06em;
  }
  .sec-title{ font-family:'Noto Serif KR',serif; font-weight:700; font-size:22px;}
  .sec-desc{ color:var(--ink-soft); font-size:13.5px; margin: 4px 0 20px;}

  .panel{
    background: var(--paper);
    border:1px solid var(--line-strong);
    border-radius: 6px;
    padding: 22px 22px 16px;
    box-shadow: var(--shadow);
  }

  /* controls */
  .controls{ display:flex; flex-wrap:wrap; gap:18px; align-items:center; margin-bottom:14px; font-size:13px; color:var(--ink-soft); }
  .controls label{ display:flex; flex-direction:column; gap:5px; font-family:'JetBrains Mono',monospace; font-size:11.5px; letter-spacing:0.04em; color:var(--ink-faint); text-transform:uppercase;}
  input[type=range]{ width: 220px; accent-color: var(--heat); }
  .range-val{ font-family:'JetBrains Mono',monospace; color:var(--ink); font-size:13px; font-weight:600;}
  .seg{ display:inline-flex; border:1px solid var(--line-strong); border-radius:5px; overflow:hidden; }
  .seg button{
    border:none; background:var(--paper); color:var(--ink-soft); padding:6px 13px; font-family:'JetBrains Mono',monospace; font-size:12px; cursor:pointer;
  }
  .seg button.active{ background: var(--ink); color: var(--paper); }
  .stat-line{ font-family:'JetBrains Mono',monospace; font-size:13px; color:var(--ink); margin: 10px 2px 6px;}
  .stat-line .val{ color: var(--heat); font-weight:700; }
  .stat-line .val.down{ color: var(--cold); }
  svg{ display:block; width:100%; height:auto; overflow:visible;}
  .axis-label{ font-family:'JetBrains Mono',monospace; font-size:10px; fill: var(--ink-faint); }
  .legend{ display:flex; gap:18px; font-size:12px; color:var(--ink-soft); margin-top:8px; flex-wrap:wrap;}
  .legend span{ display:inline-flex; align-items:center; gap:6px;}
  .swatch{ width:14px; height:3px; display:inline-block; border-radius:2px;}

  /* birthday section */
  .date-input-row{ display:flex; align-items:center; gap:14px; flex-wrap:wrap; margin-bottom:16px;}
  .date-input-row select{
    font-family:'JetBrains Mono',monospace; font-size:14px; padding:8px 10px; border:1px solid var(--line-strong);
    border-radius:5px; background:var(--paper); color:var(--ink);
  }
  .record-cards{ display:grid; grid-template-columns: repeat(3,1fr); gap:12px; margin-top:18px; }
  .rcard{ border:1px solid var(--line); border-radius:6px; padding:14px 14px; text-align:center; }
  .rcard .lbl{ font-family:'JetBrains Mono',monospace; font-size:10.5px; color:var(--ink-faint); text-transform:uppercase; letter-spacing:0.06em;}
  .rcard .v{ font-family:'Noto Serif KR',serif; font-weight:900; font-size:26px; margin:4px 0 2px;}
  .rcard .y{ font-size:12px; color:var(--ink-soft);}
  .rcard.hot .v{ color:var(--heat); }
  .rcard.cold .v{ color:var(--cold); }

  footer{ border-top:2px solid var(--ink); padding-top:16px; font-family:'JetBrains Mono',monospace; font-size:11.5px; color:var(--ink-faint); display:flex; justify-content:space-between; flex-wrap:wrap; gap:8px;}

  @media (max-width: 720px){
    .hero{ grid-template-columns: 1fr; }
    .hero-side{ border-left:none; border-top:1px solid var(--line); padding-left:0; padding-top:18px;}
    .record-cards{ grid-template-columns: 1fr 1fr; }
    .stamp{ display:none; }
  }
  .tooltip{
    position:absolute; pointer-events:none; background:var(--ink); color:var(--paper);
    font-family:'JetBrains Mono',monospace; font-size:11.5px; padding:6px 9px; border-radius:4px;
    transform: translate(-50%,-115%); white-space:nowrap; opacity:0; transition:opacity .1s; z-index:10;
  }
  .chart-wrap{ position:relative; }
</style>
</head>
<body>
<div class="wrap">

  <div class="ledger-head">
    <div>
      <div class="eyebrow">OBSERVATION LEDGER · KMA STATION 108</div>
    </div>
    <div class="station-id">서울 · 위도 37.57N · 기록 1907.10–현재</div>
  </div>
  <h1>서울 기온 기록부, 119년</h1>
  <p class="sub">기상청 서울(108) 관측소의 1907년 10월부터 오늘까지의 일별 기온 기록입니다. 100년 넘게 쌓인 숫자 속에서 변화의 흐름을 직접 확인해보세요.</p>

  <div class="hero">
    <div class="hero-number">
      <div class="stamp" id="heroStamp">전 기간<br>회귀 추세<br>★ 1908–2025</div>
      <div><span class="num" id="heroNum">+0.0</span><span class="num deg">℃</span></div>
      <div class="cap">완전 관측연도(1908–2025) 기준, 선형회귀로 추정한 서울의 연평균 기온 상승폭입니다.</div>
    </div>
    <div class="hero-side" id="heroSide"></div>
  </div>

  <!-- SECTION A: trend -->
  <section>
    <div class="sec-head"><span class="sec-tag">기록 A</span><span class="sec-title">연평균 기온의 119년 추이</span></div>
    <p class="sec-desc">구간을 선택하면 그 구간만의 회귀선(추세선)을 다시 계산합니다. 회귀분석이 실제 기후 데이터에서 어떻게 쓰이는지 확인해보세요.</p>
    <div class="panel">
      <div class="controls">
        <label>시작 연도
          <input type="range" id="yearStart" min="1908" max="2025" value="1908">
        </label>
        <label>종료 연도
          <input type="range" id="yearEnd" min="1908" max="2025" value="2025">
        </label>
        <span class="range-val" id="rangeLabel">1908 – 2025</span>
      </div>
      <div class="chart-wrap">
        <svg id="trendChart" viewBox="0 0 900 340"></svg>
        <div class="tooltip" id="trendTip"></div>
      </div>
      <div class="legend">
        <span><span class="swatch" style="background:var(--ink-faint)"></span>연평균 기온</span>
        <span><span class="swatch" style="background:var(--gold)"></span>10년 이동평균</span>
        <span><span class="swatch" style="background:var(--heat)"></span>선택 구간 회귀선</span>
      </div>
      <div class="stat-line" id="trendStat"></div>
    </div>
  </section>

  <!-- SECTION B: extremes -->
  <section>
    <div class="sec-head"><span class="sec-tag">기록 B</span><span class="sec-title">폭염일과 한파일, 연도별 변화</span></div>
    <p class="sec-desc">최고기온 33℃ 이상이면 폭염일, 최저기온 -12℃ 이하면 한파일로 집계했습니다.</p>
    <div class="panel">
      <div class="controls">
        <div class="seg" id="extSeg">
          <button data-mode="heat" class="active">폭염일 (≥33℃)</button>
          <button data-mode="cold">한파일 (≤-12℃)</button>
        </div>
      </div>
      <div class="chart-wrap">
        <svg id="extChart" viewBox="0 0 900 280"></svg>
        <div class="tooltip" id="extTip"></div>
      </div>
      <div class="stat-line" id="extStat"></div>
    </div>
  </section>

  <!-- SECTION C: birthday lookup -->
  <section>
    <div class="sec-head"><span class="sec-tag">기록 C</span><span class="sec-title">그 날의 기록 — 날짜로 찾아보기</span></div>
    <p class="sec-desc">월과 일을 고르면, 1907년부터 그 날짜에 서울의 기온이 몇 도였는지 모두 보여드립니다.</p>
    <div class="panel">
      <div class="date-input-row">
        <select id="monthSel"></select>
        <select id="daySel"></select>
        <span class="range-val" id="mdCount"></span>
      </div>
      <div class="chart-wrap">
        <svg id="mdChart" viewBox="0 0 900 260"></svg>
        <div class="tooltip" id="mdTip"></div>
      </div>
      <div class="record-cards" id="recordCards"></div>
    </div>
  </section>

  <footer>
    <span>자료: 기상청 서울(108) 관측소 일별 기온 — 1907.10.01 ~ 2026.06.18</span>
    <span>1907년·2026년은 일부 기간만 포함된 연도입니다</span>
  </footer>
</div>

<script>
const YEARLY = __YEARLY_JSON__;
const DAILY_MD = __DAILY_JSON__;

const fmt1 = n => (Math.round(n*10)/10).toFixed(1);

// ---------- regression helper ----------
function linreg(xs, ys){
  const n = xs.length;
  if(n < 2) return {slope:0, intercept: ys[0]||0};
  const mx = xs.reduce((a,b)=>a+b,0)/n;
  const my = ys.reduce((a,b)=>a+b,0)/n;
  let num=0, den=0;
  for(let i=0;i<n;i++){ num += (xs[i]-mx)*(ys[i]-my); den += (xs[i]-mx)**2; }
  const slope = den===0 ? 0 : num/den;
  const intercept = my - slope*mx;
  return {slope, intercept};
}

// ---------- hero ----------
(function initHero(){
  const complete = YEARLY.filter(d=>d.complete);
  const xs = complete.map(d=>d.year), ys = complete.map(d=>d.avg);
  const {slope, intercept} = linreg(xs, ys);
  const y0 = xs[0], y1 = xs[xs.length-1];
  const rise = slope*(y1-y0);
  document.getElementById('heroNum').textContent = (rise>=0?'+':'') + fmt1(rise);
  document.getElementById('heroStamp').innerHTML = `전 기간<br>회귀 추세<br>★ ${y0}–${y1}`;

  const first5 = ys.slice(0,5).reduce((a,b)=>a+b,0)/5;
  const last5 = ys.slice(-5).reduce((a,b)=>a+b,0)/5;
  const hottestYear = complete.reduce((a,b)=> b.avg>a.avg? b:a);
  const coldestYear = complete.reduce((a,b)=> b.avg<a.avg? b:a);

  document.getElementById('heroSide').innerHTML = `
    <div class="row"><span>관측 시작</span><b>${y0}년</b></div>
    <div class="row"><span>최근 5년 평균</span><b>${fmt1(last5)}℃</b></div>
    <div class="row"><span>1908~1912년 평균</span><b>${fmt1(first5)}℃</b></div>
    <div class="row"><span>가장 더웠던 해</span><b>${hottestYear.year}년 (${fmt1(hottestYear.avg)}℃)</b></div>
    <div class="row"><span>가장 추웠던 해</span><b>${coldestYear.year}년 (${fmt1(coldestYear.avg)}℃)</b></div>
  `;
})();

// ---------- SECTION A: trend chart ----------
const trendSvg = document.getElementById('trendChart');
const trendTip = document.getElementById('trendTip');
const W=900,H=340, PAD={l:46,r:18,t:18,b:34};
const yStartEl = document.getElementById('yearStart');
const yEndEl = document.getElementById('yearEnd');
const rangeLabel = document.getElementById('rangeLabel');

function movingAvg(arr, key, window){
  return arr.map((d,i)=>{
    const lo = Math.max(0,i-window+1);
    const slice = arr.slice(lo,i+1).filter(x=>x.complete);
    if(slice.length < Math.min(window, i+1)*0.6) return null;
    return slice.reduce((a,b)=>a+b[key],0)/slice.length;
  });
}

function drawTrend(){
  let ys0 = parseInt(yStartEl.value), ys1 = parseInt(yEndEl.value);
  if(ys0 > ys1) [ys0,ys1] = [ys1,ys0];
  rangeLabel.textContent = `${ys0} – ${ys1}`;

  const allYears = YEARLY.map(d=>d.year);
  const xMin = Math.min(...allYears), xMax = Math.max(...allYears);
  const avgs = YEARLY.map(d=>d.avg);
  const yMin = Math.floor(Math.min(...avgs)-0.6), yMax = Math.ceil(Math.max(...avgs)+0.6);

  const xScale = y => PAD.l + (y-xMin)/(xMax-xMin) * (W-PAD.l-PAD.r);
  const yScale = v => H-PAD.b - (v-yMin)/(yMax-yMin) * (H-PAD.t-PAD.b);

  const ma = movingAvg(YEARLY, 'avg', 10);

  let svg = `<g class="grid">`;
  for(let g=Math.ceil(yMin); g<=yMax; g+=2){
    svg += `<line x1="${PAD.l}" x2="${W-PAD.r}" y1="${yScale(g)}" y2="${yScale(g)}" stroke="var(--line)" stroke-width="1"/>`;
    svg += `<text class="axis-label" x="${PAD.l-8}" y="${yScale(g)+3}" text-anchor="end">${g}℃</text>`;
  }
  for(let yr=Math.ceil(xMin/20)*20; yr<=xMax; yr+=20){
    svg += `<text class="axis-label" x="${xScale(yr)}" y="${H-PAD.b+16}" text-anchor="middle">${yr}</text>`;
  }
  svg += `</g>`;

  // raw line (faint)
  let path = '';
  YEARLY.forEach((d,i)=>{
    if(!d.complete) return;
    const cmd = path==='' ? 'M' : 'L';
    path += `${cmd}${xScale(d.year).toFixed(1)},${yScale(d.avg).toFixed(1)} `;
  });
  svg += `<path d="${path}" fill="none" stroke="var(--ink-faint)" stroke-width="1.3" opacity="0.65"/>`;

  // moving avg gold line
  let maPath = '';
  YEARLY.forEach((d,i)=>{
    if(ma[i]===null) return;
    const cmd = maPath==='' ? 'M' : 'L';
    maPath += `${cmd}${xScale(d.year).toFixed(1)},${yScale(ma[i]).toFixed(1)} `;
  });
  svg += `<path d="${maPath}" fill="none" stroke="var(--gold)" stroke-width="2.4"/>`;

  // selected range highlight + regression
  const sel = YEARLY.filter(d=>d.complete && d.year>=ys0 && d.year<=ys1);
  svg += `<rect x="${xScale(ys0)}" y="${PAD.t}" width="${xScale(ys1)-xScale(ys0)}" height="${H-PAD.t-PAD.b}" fill="var(--heat)" opacity="0.05"/>`;

  let statText = '데이터가 부족합니다.';
  if(sel.length>=2){
    const {slope, intercept} = linreg(sel.map(d=>d.year), sel.map(d=>d.avg));
    const x0=sel[0].year, x1=sel[sel.length-1].year;
    const v0 = slope*x0+intercept, v1 = slope*x1+intercept;
    svg += `<line x1="${xScale(x0)}" y1="${yScale(v0)}" x2="${xScale(x1)}" y2="${yScale(v1)}" stroke="var(--heat)" stroke-width="3"/>`;
    const totalRise = slope*(x1-x0);
    const cls = totalRise>=0 ? 'val' : 'val down';
    statText = `${x0}~${x1}년(${x1-x0}년간) 회귀 추세: 연평균 <span class="${cls}">${(slope>=0?'+':'')}${fmt1(slope*10)}℃/10년</span> · 구간 전체 <span class="${cls}">${(totalRise>=0?'+':'')}${fmt1(totalRise)}℃</span> 변화`;
  }
  document.getElementById('trendStat').innerHTML = statText;

  // dots for hover
  YEARLY.forEach(d=>{
    if(!d.complete) return;
    svg += `<circle data-year="${d.year}" data-avg="${d.avg}" cx="${xScale(d.year).toFixed(1)}" cy="${yScale(d.avg).toFixed(1)}" r="7" fill="transparent" class="hoverdot"/>`;
  });

  trendSvg.innerHTML = svg;

  trendSvg.querySelectorAll('.hoverdot').forEach(c=>{
    c.addEventListener('mousemove', e=>{
      const rect = trendSvg.getBoundingClientRect();
      const scale = rect.width / W;
      trendTip.style.opacity=1;
      trendTip.style.left = (parseFloat(c.getAttribute('cx'))*scale) + 'px';
      trendTip.style.top = (parseFloat(c.getAttribute('cy'))*scale) + 'px';
      trendTip.textContent = `${c.dataset.year}년 · ${fmt1(c.dataset.avg)}℃`;
    });
    c.addEventListener('mouseleave', ()=> trendTip.style.opacity=0);
  });
}
yStartEl.addEventListener('input', drawTrend);
yEndEl.addEventListener('input', drawTrend);
drawTrend();

// ---------- SECTION B: extremes ----------
const extSvg = document.getElementById('extChart');
const extTip = document.getElementById('extTip');
let extMode = 'heat';
document.getElementById('extSeg').addEventListener('click', e=>{
  if(e.target.tagName!=='BUTTON') return;
  document.querySelectorAll('#extSeg button').forEach(b=>b.classList.remove('active'));
  e.target.classList.add('active');
  extMode = e.target.dataset.mode;
  drawExt();
});

function drawExt(){
  const W2=900,H2=280, P={l:42,r:18,t:16,b:34};
  const data = YEARLY.filter(d=>d.complete);
  const key = extMode==='heat' ? 'heatwave' : 'coldwave';
  const color = extMode==='heat' ? 'var(--heat)' : 'var(--cold)';
  const maxV = Math.max(...data.map(d=>d[key]), 5);
  const xMin = data[0].year, xMax = data[data.length-1].year;
  const xScale = y => P.l + (y-xMin)/(xMax-xMin) * (W2-P.l-P.r);
  const yScale = v => H2-P.b - (v/maxV) * (H2-P.t-P.b);
  const barW = Math.max(1.4, (W2-P.l-P.r)/data.length - 0.6);

  let svg = '';
  for(let g=0; g<=maxV; g+=Math.ceil(maxV/4)){
    svg += `<line x1="${P.l}" x2="${W2-P.r}" y1="${yScale(g)}" y2="${yScale(g)}" stroke="var(--line)" stroke-width="1"/>`;
    svg += `<text class="axis-label" x="${P.l-8}" y="${yScale(g)+3}" text-anchor="end">${g}일</text>`;
  }
  for(let yr=Math.ceil(xMin/20)*20; yr<=xMax; yr+=20){
    svg += `<text class="axis-label" x="${xScale(yr)}" y="${H2-P.b+16}" text-anchor="middle">${yr}</text>`;
  }
  data.forEach(d=>{
    const x = xScale(d.year)-barW/2, y = yScale(d[key]), h = (H2-P.b)-y;
    svg += `<rect class="bar" data-year="${d.year}" data-v="${d[key]}" x="${x.toFixed(1)}" y="${y.toFixed(1)}" width="${barW.toFixed(1)}" height="${Math.max(0,h).toFixed(1)}" fill="${color}" opacity="0.78"/>`;
  });
  extSvg.innerHTML = svg;

  const recent10 = data.slice(-10).reduce((a,b)=>a+b[key],0)/10;
  const first10 = data.slice(0,10).reduce((a,b)=>a+b[key],0)/10;
  const label = extMode==='heat' ? '폭염일' : '한파일';
  document.getElementById('extStat').innerHTML =
    `관측 초기 10년 평균 <span class="val">${fmt1(first10)}일</span> → 최근 10년 평균 <span class="val">${fmt1(recent10)}일</span> (${label}/년)`;

  extSvg.querySelectorAll('.bar').forEach(b=>{
    b.addEventListener('mousemove', e=>{
      const rect = extSvg.getBoundingClientRect();
      const scale = rect.width / W2;
      extTip.style.opacity=1;
      extTip.style.left = ((parseFloat(b.getAttribute('x'))+parseFloat(b.getAttribute('width'))/2)*scale) + 'px';
      extTip.style.top = (parseFloat(b.getAttribute('y'))*scale) + 'px';
      extTip.textContent = `${b.dataset.year}년 · ${b.dataset.v}일`;
    });
    b.addEventListener('mouseleave', ()=> extTip.style.opacity=0);
  });
}
drawExt();

// ---------- SECTION C: birthday lookup ----------
const monthSel = document.getElementById('monthSel');
const daySel = document.getElementById('daySel');
for(let m=1;m<=12;m++){
  const o=document.createElement('option'); o.value=m; o.textContent=m+'월';
  monthSel.appendChild(o);
}
function daysInMonth(m){ return [31,29,31,30,31,30,31,31,30,31,30,31][m-1]; }
function rebuildDays(){
  const m = parseInt(monthSel.value);
  daySel.innerHTML='';
  for(let d=1; d<=daysInMonth(m); d++){
    const o=document.createElement('option'); o.value=d; o.textContent=d+'일';
    daySel.appendChild(o);
  }
}
monthSel.value = 6; rebuildDays(); daySel.value = 19;
monthSel.addEventListener('change', ()=>{ rebuildDays(); drawMd(); });
daySel.addEventListener('change', drawMd);

const mdSvg = document.getElementById('mdChart');
const mdTip = document.getElementById('mdTip');

function drawMd(){
  const m = String(monthSel.value).padStart(2,'0');
  const d = String(daySel.value).padStart(2,'0');
  const key = `${m}-${d}`;
  const rows = (DAILY_MD[key]||[]).map(r=>({year:r[0],avg:r[1],min:r[2],max:r[3]})).sort((a,b)=>a.year-b.year);
  document.getElementById('mdCount').textContent = `${rows.length}개 연도 기록`;

  const W3=900,H3=260,P={l:42,r:18,t:16,b:34};
  if(rows.length===0){ mdSvg.innerHTML=''; document.getElementById('recordCards').innerHTML=''; return; }
  const xMin=rows[0].year, xMax=rows[rows.length-1].year;
  const yMin = Math.floor(Math.min(...rows.map(r=>r.min))-2);
  const yMax = Math.ceil(Math.max(...rows.map(r=>r.max))+2);
  const xScale = y => P.l + (xMax===xMin?0:(y-xMin)/(xMax-xMin)) * (W3-P.l-P.r);
  const yScale = v => H3-P.b - (v-yMin)/(yMax-yMin) * (H3-P.t-P.b);
  const barW = Math.max(1.6, (W3-P.l-P.r)/rows.length - 1);

  let svg='';
  for(let g=Math.ceil(yMin/10)*10; g<=yMax; g+=10){
    svg += `<line x1="${P.l}" x2="${W3-P.r}" y1="${yScale(g)}" y2="${yScale(g)}" stroke="var(--line)" stroke-width="1"/>`;
    svg += `<text class="axis-label" x="${P.l-8}" y="${yScale(g)+3}" text-anchor="end">${g}℃</text>`;
  }
  for(let yr=Math.ceil(xMin/20)*20; yr<=xMax; yr+=20){
    svg += `<text class="axis-label" x="${xScale(yr)}" y="${H3-P.b+16}" text-anchor="middle">${yr}</text>`;
  }
  rows.forEach(r=>{
    const x = xScale(r.year)-barW/2;
    const yTop = yScale(r.max), yBot = yScale(r.min);
    svg += `<line class="mdbar" data-row='${JSON.stringify(r)}' x1="${xScale(r.year).toFixed(1)}" x2="${xScale(r.year).toFixed(1)}" y1="${yTop.toFixed(1)}" y2="${yBot.toFixed(1)}" stroke="var(--cold-soft)" stroke-width="${barW.toFixed(1)}"/>`;
    svg += `<circle data-row='${JSON.stringify(r)}' class="mdbar" cx="${xScale(r.year).toFixed(1)}" cy="${yScale(r.avg).toFixed(1)}" r="2.6" fill="var(--heat)"/>`;
  });
  mdSvg.innerHTML = svg;

  mdSvg.querySelectorAll('.mdbar').forEach(el=>{
    el.addEventListener('mousemove', e=>{
      const rect = mdSvg.getBoundingClientRect();
      const scale = rect.width / W3;
      const row = JSON.parse(el.dataset.row);
      mdTip.style.opacity=1;
      mdTip.style.left = (xScale(row.year)*scale) + 'px';
      mdTip.style.top = (yScale(row.max)*scale) + 'px';
      mdTip.textContent = `${row.year}년 · 평균 ${fmt1(row.avg)}℃ (${fmt1(row.min)}~${fmt1(row.max)}℃)`;
    });
    el.addEventListener('mouseleave', ()=> mdTip.style.opacity=0);
  });

  const hottest = rows.reduce((a,b)=> b.avg>a.avg? b:a);
  const coldest = rows.reduce((a,b)=> b.avg<a.avg? b:a);
  const avgAll = rows.reduce((a,b)=>a+b.avg,0)/rows.length;
  document.getElementById('recordCards').innerHTML = `
    <div class="rcard hot"><div class="lbl">역대 가장 더운 해</div><div class="v">${fmt1(hottest.avg)}℃</div><div class="y">${hottest.year}년</div></div>
    <div class="rcard"><div class="lbl">${rows.length}개년 평균</div><div class="v">${fmt1(avgAll)}℃</div><div class="y">${m}월 ${d}일</div></div>
    <div class="rcard cold"><div class="lbl">역대 가장 추운 해</div><div class="v">${fmt1(coldest.avg)}℃</div><div class="y">${coldest.year}년</div></div>
  `;
}
drawMd();
</script>
</body>
</html>
"""


def main():
    print(f"읽는 중: {INPUT_CSV}")
    df = load_and_clean(INPUT_CSV)
    print(f"  총 {len(df)}행, 기간 {df['날짜'].min().date()} ~ {df['날짜'].max().date()}")

    yearly = build_yearly(df)
    daily_lookup = build_daily_lookup(df)

    html = HTML_TEMPLATE.replace(
        "__YEARLY_JSON__", json.dumps(yearly, ensure_ascii=False)
    ).replace(
        "__DAILY_JSON__", json.dumps(daily_lookup, ensure_ascii=False)
    )

    with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"완료: {OUTPUT_HTML} 생성됨 ({len(html)/1024/1024:.2f} MB)")


if __name__ == "__main__":
    main()
