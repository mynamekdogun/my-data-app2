import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# 1. 페이지 기본 설정
st.set_page_config(
    page_title="서울 기온 데이터 멀티 시각화",
    page_icon="🌡️",
    layout="wide"
)

# 2. 데이터 로드 및 전처리 함수 (캐싱 적용)
@st.cache_data
def load_and_preprocess_data():
    url = "https://raw.githubusercontent.com/greatsong/modudata/main/data/seoul.csv"
    try:
        # 대부분의 한국어 CSV는 CP949 인코딩입니다.
        df = pd.read_csv(url, encoding='cp949')
    except Exception:
        df = pd.read_csv(url, encoding='utf-8')
    
    # 열 이름 정제 (공백 제거, '(℃)' 제거)
    df.columns = df.columns.str.strip().str.replace('(℃)', '', regex=False).str.replace(' ', '', regex=False)
    
    # 날짜 데이터 변환
    df['날짜'] = pd.to_datetime(df['날짜'])
    
    # 분석에 필요한 시간 열 추가
    df['연도'] = df['날짜'].dt.year
    df['월'] = df['날짜'].dt.month
    df['년대'] = (df['연도'] // 10) * 10
    
    # 기온 데이터 숫자형 변환 및 결측치 제거
    for col in ['평균기온', '최저기온', '최고기온']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
            
    df = df.dropna(subset=['평균기온', '연도', '월'])
    return df

# 3. 앱 헤더 및 설명
st.title("🌡️ 서울 기온 데이터: 다각도 시각화")
st.markdown("""
이 앱은 지난 100년간의 서울 기온 데이터를 활용하여, 단순히 연도별 평균을 보는 것을 넘어
**데이터의 분포, 월별 변화 패턴, 10년 단위의 장기적 추세**를 보여줍니다.
""")

try:
    with st.spinner("데이터를 로드하는 중입니다..."):
        df = load_and_preprocess_data()

    # ==========================================
    # 사이드바 컨트롤러
    # ==========================================
    st.sidebar.header("📊 그래프 선택")
    graph_type = st.sidebar.radio(
        "어떤 관점의 그래프를 보시겠습니까?",
        ("월별 기온 분포 (박스플롯)", "연도x월 기온 변화 (히트맵)", "년대별 평균 기온 (바 차트)")
    )

    st.markdown("---")

    # ==========================================
    # 메인 화면: 그래프 표시
    # ==========================================

    # --- 1. 월별 기온 분포 (Box Plot) ---
    if graph_type == "월별 기온 분포 (박스플롯)":
        st.subheader("🗓️ 월별 평균 기온 분포 (100년 전체)")
        st.markdown("*   각 월의 기온이 어느 범위에 분포하는지, 이상치는 없는지 한눈에 보여줍니다.")
        
        # 월 데이터를 범주형으로 변환 (순서 보장)
        box_df = df.copy()
        box_df['월'] = box_df['월'].astype(str) + "월"
        month_order = [f"{i}월" for i in range(1, 13)]

        fig_box = px.box(
            box_df,
            x="월",
            y="평균기온",
            color="월",
            title="서울 월별 평균 기온 분포",
            category_orders={"월": month_order},
            labels={"평균기온": "기온 (℃)"},
            template="plotly_white"
        )
        fig_box.update_layout(showlegend=False, height=550)
        st.plotly_chart(fig_box, use_container_width=True)


    # --- 2. 연도x월 기온 변화 (Heatmap) ---
    elif graph_type == "연도x월 기온 변화 (히트맵)":
        st.subheader("🔥 연도 및 월별 기온 히트맵 (최근 30년)")
        st.markdown("*   세로축(연도)과 가로축(월)을 따라 색상의 변화를 통해 기온 상승 추세를 직관적으로 확인합니다.")
        
        # 최근 30년 데이터만 필터링
        heatmap_start_year = df['연도'].max() - 29
        heatmap_df = df[df['연도'] >= heatmap_start_year]
        
        # 피벗 테이블 생성 (연도 x 월)
        heatmap_pivot = heatmap_df.pivot_table(
            values='평균기온',
            index='연도',
            columns='월',
            aggfunc='mean'
        )

        fig_heat = px.imshow(
            heatmap_pivot,
            labels=dict(x="월", y="연도", color="기온 (℃)"),
            x=[f"{i}월" for i in range(1, 13)],
            title=f"서울 연도별/월별 평균 기온 히트맵 ({heatmap_start_year}년 ~ {df['연도'].max()}년)",
            color_continuous_scale="RdBu_r", # 빨간색-파란색 반전 (더우면 빨강)
            template="plotly_white"
        )
        fig_heat.update_layout(height=600)
        st.plotly_chart(fig_heat, use_container_width=True)


    # --- 3. 년대별 평균 기온 (Bar Chart) ---
    elif graph_type == "년대별 평균 기온 (바 차트)":
        st.subheader("📊 10년 단위(년대) 평균 기온 추이")
        st.markdown("*   100년간 10년 단위로 묶어서 평균 기온을 비교하여 장기적인 기후 변화를 보여줍니다.")
        
        # 년대별 평균 기온 계산
        decade_df = df.groupby('년대').agg(
            년대평균=('평균기온', 'mean')
        ).reset_index()
        
        # 온전한 10년 데이터만 표시 (예: 1910년대 ~ 2010년대)
        decade_df = decade_df[(decade_df['년대'] >= 1910) & (decade_df['년대'] <= 2010)]
        decade_df['년대_label'] = decade_df['년대'].astype(str) + "년대"

        # 시각화 (px.bar + go.Scatter 트렌드선)
        fig_bar = px.bar(
            decade_df,
            x="년대_label",
            y="년대평균",
            title="서울 10년 단위(년대) 평균 기온",
            labels={"년대평균": "평균 기온 (℃)", "년대_label": "년대"},
            color="년대평균",
            color_continuous_scale="YlOrRd", # 노랑-주황-빨강
            template="plotly_white"
        )
        
        # 전체 기간 평균선 추가
        total_avg = decade_df['년대평균'].mean()
        fig_bar.add_shape(
            type="line", line=dict(color="blue", width=2, dash="dash"),
            x0=0, x1=1, y0=total_avg, y1=total_avg, xref="paper", yref="y"
        )
        fig_bar.add_annotation(
            x=1, y=total_avg, text=f"기간 전체 평균: {total_avg:.2f}℃",
            showarrow=False, yshift=10, xanchor="right", font=dict(color="blue")
        )

        fig_bar.update_layout(height=550, coloraxis_showscale=False)
        st.plotly_chart(fig_bar, use_container_width=True)

    # 데이터 표 원본 확인 (필요시)
    with st.expander("📝 원본 데이터 요약 보기"):
        st.dataframe(df.head(100), use_container_width=True)

except Exception as e:
    st.error(f"데이터를 처리하는 중 오류가 발생했습니다: {e}")
