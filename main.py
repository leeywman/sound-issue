import streamlit as st
import numpy as np
import math

# ==========================================
# 1. 페이지 기본 설정 및 헤더
# ==========================================
st.set_page_config(
    page_title="EarFit",
    page_icon="🎧",
    layout="centered"
)

# 메인 타이틀
st.title("EarFit")
st.write("---")

# ==========================================
# 2. 1kHz 기준음 생성 함수 (Web Audio API)
# ==========================================
def play_1khz_tone_html():
    """브라우저 Web Audio API를 사용하여 1kHz 정현파(Sine Wave) 기준음을 1.5초간 재생"""
    html_code = """
    <script>
    function playTone() {
        const AudioContext = window.AudioContext || window.webkitAudioContext;
        if (!AudioContext) {
            alert("이 브라우저는 Web Audio API를 지원하지 않습니다.");
            return;
        }
        const ctx = new AudioContext();
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();

        osc.type = 'sine';
        osc.frequency.setValueAtTime(1000, ctx.currentTime);

        gain.gain.setValueAtTime(0.01, ctx.currentTime);
        gain.gain.exponentialRampToValueAtTime(0.3, ctx.currentTime + 0.1);
        gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 1.5);

        osc.connect(gain);
        gain.connect(ctx.destination);

        osc.start();
        osc.stop(ctx.currentTime + 1.5);
    }
    </script>
    <button onclick="playTone()" style="
        background-color: #4CAF50;
        color: white;
        padding: 12px 24px;
        font-size: 16px;
        font-weight: bold;
        border: none;
        border-radius: 8px;
        cursor: pointer;
        transition: 0.3s;
    ">
        🔊 1kHz 기준 소리 재생 (1.5초)
    </button>
    """
    st.components.v1.html(html_code, height=70)

# ==========================================
# 3. 1kHz 기준음 테스트 가이드 영역
# ==========================================
st.subheader("1kHz 기준음 캘리브레이션")
st.info("아래 버튼을 눌러 소리를 들으시면서, 평소 음악을 들을 때의 크기와 비슷해지도록 스마트폰 볼륨을 조절해 보세요.")

play_1khz_tone_html()
st.write("---")

# ==========================================
# 4. 기본 정보 입력 섹션
# ==========================================
st.subheader("기본 정보 입력")

# (1) 연령대 선택
age_group = st.selectbox(
    "연령대를 선택하세요",
    ["10대 이하", "20대 ~ 30대", "40대 이상"]
)

# (2) 스마트폰 종류 선택
device_os = st.radio(
    "사용 중인 스마트폰 종류",
    ["아이폰 (iOS)", "삼성 갤럭시 (Android)"],
    horizontal=True
)

# (3) 청취 방식 선택
listening_method = st.radio(
    "청취 방식을 선택하세요",
    ["이어폰 / 헤드폰", "외부 스피커"],
    horizontal=True
)

# (4) 이어폰/헤드폰 선택 시 추가 질문
is_continuous = "쉬지 않고 연속으로 청취"
if listening_method == "이어폰 / 헤드폰":
    is_continuous = st.radio(
        "청취 형태를 선택하세요",
        ["쉬지 않고 연속으로 청취", "중간에 쉬면서 청취 (간헐적 청취)"],
        horizontal=True
    )

# (5) 기기별 독립 dB 음량 선택지 설정
if device_os == "아이폰 (iOS)":
    volume_options = {
        "볼륨 25% 이하 (약 52 dB)": 52,
        "볼륨 50% 수준 (약 68 dB)": 68,
        "볼륨 75% 수준 (약 82 dB)": 82,
        "볼륨 90% 이상 (약 94 dB)": 94
    }
else:
    volume_options = {
        "볼륨 25% 이하 (약 50 dB)": 50,
        "볼륨 50% 수준 (약 65 dB)": 65,
        "볼륨 75% 수준 (약 84 dB)": 84,
        "볼륨 90% 이상 (약 96 dB)": 96
    }

selected_vol_label = st.selectbox("평소 청취 음량을 선택하세요", list(volume_options.keys()))
base_db = volume_options[selected_vol_label]

# (6) 청취 시간 입력
listen_duration = st.number_input(
    "총 청취 시간 (분 단위)",
    min_value=10,
    max_value=480,
    value=60,
    step=10
)

st.write("---")

# ==========================================
# 5. 이비인후과 알고리즘 및 피로도 계산 (수정완료)
# ==========================================

# 연령대별 가중치 적용
if "10대" in age_group:
    age_factor = 1.15
elif "20대" in age_group:
    age_factor = 1.00
else:
    age_factor = 0.90

# 청취 방식별 실질 음압(dB) 보정
effective_db = base_db
if listening_method == "이어폰 / 헤드폰":
    effective_db += 3  # 귀 밀착 시 외이도 음압 3dB 상승

# 중간 휴식 여부 가중치
if listening_method == "이어폰 / 헤드폰" and "중간에 쉬면서" in is_continuous:
    rest_factor = 0.7  # 간헐적 청취: 피로도 30% 감쇄
else:
    rest_factor = 1.25 # 연속 청취: 피로 누적 가중치 적용

# 피로도 지수 계산 (수정된 통합 비선형 음압 곡선)
# 70dB 기준 지수 함수형 피로 누적 적용
db_weight = 10 ** ((effective_db - 70) / 20)
time_weight = listen_duration / 60.0

raw_fatigue = 20 * db_weight * time_weight * age_factor * rest_factor
fatigue_score = min(max(int(round(raw_fatigue)), 0), 100)

# ==========================================
# 6. 결과 분석 및 추천 휴식 시간 출력
# ==========================================
st.subheader("청각 피로도 진단 결과")

st.progress(fatigue_score / 100)

if fatigue_score < 30:
    st.success(f"**안전 단계 (피로도 점수: {fatigue_score}/100)**\n\n귀의 유세포에 무리가 없는 안전한 청취 습관입니다.")
    st.info("💡 **권장 휴식:** 지금 상태를 유지하시고, 2시간 청취 후 5분 정도 가볍게 쉬어주세요.")
elif fatigue_score < 70:
    st.warning(f"**주의 단계 (피로도 점수: {fatigue_score}/100)**\n\n내이 유세포에 일시적인 자극이 누적되고 있습니다. 일시적 청력 손실(TTS) 예방이 필요합니다.")
    st.info("💡 **권장 휴식:** 음악 청취를 마치고 **최소 15분 이상** 소음이 없는 조용한 환경에서 휴식을 취하세요.")
else:
    st.error(f"**위험 단계 (피로도 점수: {fatigue_score}/100)**\n\n청각 유세포 피로도가 매우 높습니다! 이 상태가 지속되면 영구적 청력 손실(PTS) 위험으로 이어질 수 있습니다.")
    st.info("💡 **권장 휴식:** 즉시 청취를 중단하고 **최소 45분 ~ 1시간 이상** 귀에 완전한 휴식을 주어야 합니다.")
