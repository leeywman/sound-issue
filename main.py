import numpy as np
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

# ---------------------------------------------------------
# 1. 페이지 기본 설정 및 디자인
# ---------------------------------------------------------
st.set_page_config(
    page_title="달팽이관 맞춤형 휴식 타이머",
    page_icon="👂",
    layout="centered",
)

st.title("👂 맞춤형 달팽이관 휴식 타이머")
st.markdown(
    """
> **의예과/생명과학 융합 탐구 프로젝트**  
> 이어폰 사용 습관, 사용 기기(iOS/Android), 청취 시간, 그리고 **연령별 유세포 감수성**을 반영하여 일시적 청력 손실(TTS) 방지를 위한 최적의 휴식 시간을 정밀 계산합니다.
"""
)
st.divider()

# ---------------------------------------------------------
# 2. 1kHz 기준 음원 들어보기 (Web Audio API 활용)
# ---------------------------------------------------------
st.subheader("🔊 1. 기준 음원 대조 (1kHz 테스트 톤)")
st.caption(
    "스마트폰/컴퓨터 볼륨을 평소 음악 들을 때의 크기로 맞춘 후 아래 버튼을 눌러 테스트 소리를 들어보세요."
)

tone_html = """
<div style="text-align: center; margin: 10px 0;">
    <button onclick="play1kHzTone()" style="
        background-color: #0366d6;
        color: white;
        border: none;
        padding: 12px 24px;
        font-size: 16px;
        font-weight: bold;
        border-radius: 8px;
        cursor: pointer;
        box-shadow: 0 2px 5px rgba(0,0,0,0.2);
    ">
        🔊 1kHz 기준 소리 재생 (1.5초)
    </button>
</div>

<script>
function play1kHzTone() {
    const AudioContext = window.AudioContext || window.webkitAudioContext;
    if (!AudioContext) {
        alert("이 브라우저는 Web Audio API를 지원하지 않습니다.");
        return;
    }
    const audioCtx = new AudioContext();
    const osc = audioCtx.createOscillator();
    const gainNode = audioCtx.createGain();

    osc.type = 'sine';
    osc.frequency.setValueAtTime(1000, audioCtx.currentTime); // 1000Hz (1kHz)

    // 볼륨 부드럽게 시작 및 종료 (클릭 음 방지)
    gainNode.gain.setValueAtTime(0.1, audioCtx.currentTime);
    gainNode.gain.exponentialRampToValueAtTime(0.5, audioCtx.currentTime + 0.1);
    gainNode.gain.exponentialRampToValueAtTime(0.01, audioCtx.currentTime + 1.4);

    osc.connect(gainNode);
    gainNode.connect(audioCtx.destination);

    osc.start();
    osc.stop(audioCtx.currentTime + 1.5);
}
</script>
"""
components.html(tone_html, height=70)

st.divider()

# ---------------------------------------------------------
# 3. 사용자 데이터 입력 폼
# ---------------------------------------------------------
st.subheader("📋 2. 청취 환경 및 개인 정보 입력")

col1, col2 = st.columns(2)

with col1:
    # 연령대 선택 (유세포 감수성 가중치)
    age_option = st.selectbox(
        "👤 연령대 선택",
        options=[
            "10대 ~ 20대 초반 (회복력 높음 / 자각 피로 낮음)",
            "20대 후반 ~ 30대 (표준 회복 속도)",
            "40대 ~ 50대 (초기 세포 노화 진행 / 피로 누적 가속)",
            "60대 이상 (고음역 유세포 민감군 / 고위험)",
        ],
        index=0,
        help="연령에 따른 외부유세포(Outer Hair Cells)의 회복 및 생리적 감수성 차이를 반영합니다.",
    )

    # 연령 가중치 매핑
    age_weights = {
        "10대 ~ 20대 초반 (회복력 높음 / 자각 피로 낮음)": 1.0,
        "20대 후반 ~ 30대 (표준 회복 속도)": 1.25,
        "40대 ~ 50대 (초기 세포 노화 진행 / 피로 누적 가속)": 1.5,
        "60대 이상 (고음역 유세포 민감군 / 고위험)": 1.8,
    }
    age_weight = age_weights[age_option]

with col2:
    # 기기 종류 선택
    device_type = st.radio(
        "📱 사용 중인 스마트폰 OS",
        options=["아이폰 (iOS)", "삼성 갤럭시 (Android)"],
        horizontal=True,
    )

# 기기별 볼륨 단계 및 추정 dB 매핑
if device_type == "아이폰 (iOS)":
    volume_options = {
        "볼륨 25% 이하 (약 50~52 dB - 조용한 방)": 52,
        "볼륨 50% 수준 (약 68 dB - 일반 실내/대화)": 68,
        "볼륨 75% 수준 (약 82 dB - 시끄러운 버스/지하철)": 82,
        "볼륨 90% 이상 (약 94 dB - 최대 볼륨 인근)": 94,
    }
else:
    volume_options = {
        "볼륨 25% 이하 (약 50 dB - 조용한 방)": 50,
        "볼륨 50% 수준 (약 65 dB - 일반 실내/대화)": 65,
        "볼륨 75% 수준 (약 84 dB - 시끄러운 버스/지하철)": 84,
        "볼륨 90% 이상 (약 96 dB - 최대 볼륨 인근)": 96,
    }

selected_volume_label = st.selectbox(
    "🔊 평소/현재 설정된 체감 볼륨 단계",
    options=list(volume_options.keys()),
    index=1,
)
est_db = volume_options[selected_volume_label]

col3, col4 = st.columns(2)

with col3:
    # 청취 시간 입력
    listen_hours = st.number_input(
        "⏱️ 오늘 음악/영상을 들은 총 시간 (시간)",
        min_value=0.1,
        max_value=24.0,
        value=2.0,
        step=0.5,
    )

with col4:
    # 청취 방식 (연속 여부)
    continuous_type = st.selectbox(
        "🔄 청취 방식",
        options=["중간중간 이어폰을 빼고 쉬었음", "쉬지 않고 연속으로 계속 들음"],
        index=0,
    )
    continuous_weight = 1.2 if continuous_type == "쉬지 않고 연속으로 계속 들음" else 1.0

st.divider()

# ---------------------------------------------------------
# 4. 분석 결과 출력
# ---------------------------------------------------------
st.subheader("📊 3. 달팽이관 피로도 분석 결과")

if st.button("🚨 내 달팽이관 권장 휴식 시간 계산하기", use_container_width=True):
    # 계산 공식: (dB / 50)^2.2 * 시간 * 연령 가중치 * 연속 청취 가중치
    base_fatigue = ((est_db / 50.0) ** 2.2) * listen_hours
    total_fatigue_score = base_fatigue * age_weight * continuous_weight
    required_rest = round(total_fatigue_score * 0.6, 1)

    # 결과 대시보드
    m1, m2, m3 = st.columns(3)
    m1.metric("추정 소음 노출 음량", f"{est_db} dB")
    m2.metric("통합 피로 가중치", f"{(age_weight * continuous_weight):.2f}x")
    m3.metric("권장 휴식 시간", f"{required_rest} 시간")

    st.markdown("---")

    # 피로도에 따른 경고 및 지침
    if required_rest < 1.5:
        st.success(
            f"✅ **[안전~경미]** 달팽이관 회복을 위해 약 **{required_rest}시간 동안** 이어폰 착용을 쉬어주세요."
        )
    elif required_rest < 4.0:
        st.warning(
            f"⚠️ **[주의 - 일시적 청력 손실(TTS) 위험]** 내이 유세포가 피로해진 상태입니다. 최소 **{required_rest}시간 동안** 60dB 이하의 조용한 환경에서 귀를 휴식시켜 주세요."
        )
    else:
        st.error(
            f"🚨 **[고위험 - 소음성 난청 누적 주의]** 유세포 손상 피로도가 매우 높습니다! **{required_rest}시간 이상** 노출을 차단하고, 이명이나 귀 먹먹함이 지속될 경우 이비인후과 검진을 권장합니다."
        )

    # 의학적 학술 배경 탭
    with st.expander("💡 의학적·기술적 탐구 원리 보기"):
        st.markdown(
            """
        * **등가 소음도(Leq)와 노출 에너지:** 소음성 난청은 단시간의 Peak 음량보다 **'노출 음량(dB) × 지속 시간'**의 총 에너지에 의해 결정됩니다.
        * **일시적 청력 손실(TTS vs PTS):** 고음량 소음에 장시간 노출되면 달팽이관 유세포가 일시적으로 지치며(TTS), 휴식 없이 누적될 경우 영구적 손상(PTS)으로 발전합니다.
        * **연령별 유세포 민감도:** 연령이 증가함에 따라 외부유세포의 능동적 증폭 기능 및 수용체 회복 속도가 지연되는 생리적 특성을 반영하였습니다.
        """
        )
