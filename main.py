
import streamlit as st
import pandas as pd
import datetime

# 1. 페이지 기본 설정
st.set_page_config(
    page_title="기말고사 올A 탑승! 공부 계획표",
    page_icon="📅",
    layout="wide"
)

# 2. 타이틀 및 응원 메시지
st.markdown("<h1 style='text-align: center; color: #4A90E2;'>🔥 기말고사 폭풍 성장을 위한 일일 공부 계획표 🔥</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; font-size: 18px;'>계획 없는 목표는 한낱 꿈에 불과하다! 오늘 하루도 알차게 채워볼까요? 🚀</p>", unsafe_allow_html=True)
st.write("---")

# 날짜 표시
today = datetime.date.today()
st.subheader(f"📅 오늘 날짜: {today.strftime('%Y년 %m월 %d일')}")

# 화면을 두 개의 구역(Column)으로 나누어 배치
col1, col2 = st.columns([1, 1.2])

# ==========================================
# 좌측 컬럼 (col1): 오늘 공부 시간 확보하기
# ==========================================
with col1:
    st.markdown("### 🏫 1. 학교 자습 시간 체크 (7교시)")
    st.caption("자습을 할 수 있는 교시에 체크해 주세요. (1교시당 50분 자습으로 계산됩니다 ⏰)")
    
    # 7교시 체크박스 생성
    school_study_periods = 0
    periods = ["1교시", "2교시", "3교시", "4교시", "5교시", "6교시", "7교시"]
    
    # 2열로 나누어 이쁘게 배치
    p_cols = st.columns(2)
    for idx, period in enumerate(periods):
        with p_cols[idx % 2]:
            if st.checkbox(f"📖 {period} 자습", key=f"period_{idx}"):
                school_study_periods += 1
                
    # 학교 자습 시간 계산 (분 -> 시간 변환)
    school_minutes = school_study_periods * 50
    school_hours = round(school_minutes / 60, 1)
    
    st.info(f"💡 **학교 자습 가능 시간:** 총 {school_study_periods}개 교시 ({school_hours}시간)")
    
    st.write("---")
    
    st.markdown("### 🏃‍♂️ 2. 방과 후 공부 계획")
    # 공부 장소 선택
    study_place = st.selectbox(
        "방과 후에 어디서 공부할 예정인가요? 🎒",
        ["스터디카페 ✍️", "학원 🏫", "일반 카페 ☕", "집 🏠", "학교 독서실 📚", "기타"]
    )
    
    # 방과 후 공부 시간 선택
    after_school_hours = st.slider(
        "방과 후 장소에서 몇 시간 공부할 수 있나요? ⏱️",
        min_value=0.0, max_value=12.0, value=3.0, step=0.5
    )
    
    st.write("---")
    
    # 🔥 총 가용 공부 시간 계산 및 시각화
    total_available_hours = round(school_hours + after_school_hours, 1)
    st.markdown("### 📊 오늘 확보한 총 공부 시간")
    
    metric_cols = st.columns(3)
    metric_cols[0].metric(label="🏫 학교 자습", value=f"{school_hours} 시간")
    metric_cols[1].metric(label="🏃‍♂️ 방과 후", value=f"{after_school_hours} 시간")
    metric_cols[2].metric(label="🔥 총 목표 시간", value=f"{total_available_hours} 시간", delta="할 수 있다!")

# ==========================================
# 우측 컬럼 (col2): 실제 공부 기록 및 피드백
# ==========================================
with col2:
    st.markdown("### 📝 3. 과목별 공부 기록 데이터")
    st.caption("표에 직접 과목을 적고 시간을 입력해 주세요! 행 추가(➕)도 가능합니다.")
    
    # 초기 데이터 프레임 구성
    init_data = {
        "과목명": ["국어 📚", "수학 📐", "영어 🔤"],
        "실제 공부한 시간 (시간)": [1.0, 1.5, 1.0],
        "완벽 마스터까지 필요한 추가 시간 (시간)": [2.0, 1.0, 1.5]
    }
    df = pd.DataFrame(init_data)
    
    # 사용자가 표를 직접 수정할 수 있는 data_editor 활용
    edited_df = st.data_editor(
        df, 
        num_rows="dynamic", 
        use_container_width=True,
        key="study_tracker"
    )
    
    # 실제 공부한 총 시간 계산
    try:
        actual_total_hours = edited_df["실제 공부한 시간 (시간)"].sum()
        needed_total_hours = edited_df["완벽 마스터까지 필요한 추가 시간 (시간)"].sum()
    except Exception:
        actual_total_hours = 0
        needed_total_hours = 0

    st.success(f"✅ 현재까지 **총 {actual_total_hours:.1f}시간** 공부 완료! (앞으로 총 {needed_total_hours:.1f}시간 더 필요해요 🎯)")
    
    st.write("---")
    
    st.markdown("###🌟 4. 하루 마무리 피드백")
    
    # 오늘의 만족도 슬라이더 (이모지 활용)
    satisfaction = st.select_slider(
        "오늘 나의 공부 만족도는? 🤔",
        options=["✨ 최악이야 (반성하자)", "📉 조금 아쉬워", "😐 평범했어", "👍 만족스러워!", "👑 오늘 나 자신을 이겼다! "],
        value="😐 평범했어"
    )
    
    # 오늘 부족했던 점이나 내일의 다짐 기록
    feedback_text = st.text_area(
        "오늘 어떤 점이 부족했나요? 내일은 어떻게 보완할지 적어보세요 ✍️",
        placeholder="예시: 수학 오답노트 정리할 때 집중력이 흐려졌다. 내일은 스터디카페에 가면 수학을 가장 먼저 끝내야지!"
    )
    
    # 하루 저장 버튼
    if st.button("🎉 오늘의 공부 마스터! 플래너 저장하기 🎉", use_container_width=True):
        st.balloons() # 축하 풍선 이펙트
        st.markdown("### 🏆 오늘의 최종 리포트")
        
        # 성적표 느낌의 요약 정보 출력
        report_card = f"""
        * **날짜:** {today.strftime('%Y-%m-%d')}
        * **오늘 목표했던 시간:** {total_available_hours}시간 / **실제 공부한 시간:** {actual_total_hours:.1f}시간
        * **방과 후 열공 장소:** {study_place}
        * **오늘의 스스로 평가:** {satisfaction}
        * **피드백 및 다짐:** > {feedback_text if feedback_text else '오늘도 수고한 나에게 박수를! 👏'}
        """
        st.markdown(report_card)
        st.toast("오늘 하루도 정말 수고 많았어요! 기말고사 대박 나자! 💪", icon="🏅")

# 4. 하단 푸터
st.write("---")
st.markdown("<p style='text-align: center; color: gray;'>Designed for Final Exam Success 🎯 | 스트림릿 공부 플래너</p>", unsafe_allow_html=True)
