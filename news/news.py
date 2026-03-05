# TELEGRAM_TOKEN = "8716377813:AAFXQwYLxJSA0Afiob_bzlFgBnCiF1n3oJM"
# CHAT_ID = "8628716011"

            
            
import streamlit as st
from newspaper import Article, Config
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np
import re
import asyncio
import threading
import time
import schedule
from googlesearch import search
from telegram import Bot

# --- 1. 설정 (본인의 정보로 수정하세요) ---
TELEGRAM_TOKEN = "8716377813:AAFXQwYLxJSA0Afiob_bzlFgBnCiF1n3oJM"
CHAT_ID = "8628716011"
SEARCH_KEYWORD = "삼성전자"

# --- 2. 초기화 ---
if 'history' not in st.session_state:
    st.session_state['history'] = []

# --- 3. 핵심 함수 (요약 및 클리닝) ---
def summarize_text(text, n=3):
    # 문장 분리
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    
    # 강력한 노이즈 필터링
    bad_patterns = [
        "기사 섹션 분류", "언론사는 개별 기사", "중복 분류할 수 있습니다", 
        "무단 전재", "재배포 금지", "기자 =", "저작권자", "구독하기"
    ]
    
    clean_sentences = []
    for s in sentences:
        s_clean = s.strip()
        # 노이즈 문구 포함 여부 확인 및 길이 체크 (20자 이상만 진짜 문장으로 취급)
        if not any(pattern in s_clean for pattern in bad_patterns) and len(s_clean) > 20:
            clean_sentences.append(s_clean)

    # 본문이 너무 없으면 앞부분이라도 가져옴
    if not clean_sentences:
        return [text[:150].strip() + "..."] if text else ["본문 내용을 추출할 수 없습니다."]

    if len(clean_sentences) <= n:
        return clean_sentences

    try:
        tfidf = TfidfVectorizer().fit_transform(clean_sentences)
        sentence_scores = np.array(tfidf.sum(axis=1)).flatten()
        top_indices = np.argsort(sentence_scores)[-n:]
        top_indices.sort()
        return [clean_sentences[i] for i in top_indices]
    except:
        return clean_sentences[:n]

# --- 4. UI 구성 및 CSS ---
st.set_page_config(page_title="AI News Push", layout="wide")

st.markdown("""
    <style>
    .news-card {
        background-color: #ffffff;
        padding: 25px;
        border-radius: 15px;
        border: 1px solid #e1e4e8;
        box-shadow: 0 4px 10px rgba(0,0,0,0.05);
        margin-bottom: 20px;
        min-height: 200px;
    }
    .card-title { font-size: 1.3rem; font-weight: bold; color: #1a73e8; margin-bottom: 12px; }
    .card-summary { background-color: #f1f3f4; padding: 15px; border-radius: 8px; line-height: 1.6; color: #3c4043; }
    </style>
    """, unsafe_allow_html=True)

with st.sidebar:
    st.title("📲 메뉴")
    input_url = st.text_input("🔗 뉴스 URL 입력")
    summary_count = st.slider("요약 문장 수", 1, 5, 3)
    analyze_btn = st.button("뉴스 분석 시작", use_container_width=True)
    
    st.markdown("---")
    # 전체 삭제 버튼 다시 추가
    if st.button("🗑️ 전체 내역 초기화", use_container_width=True):
        st.session_state['history'] = []
        st.rerun()

# --- 5. 분석 로직 ---
if analyze_btn and input_url:
    with st.spinner('뉴스를 읽고 요약하는 중...'):
        try:
            config = Config()
            config.browser_user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            
            article = Article(input_url, language='ko', config=config)
            article.download()
            article.parse()
            
            summ_list = summarize_text(article.text, n=summary_count)
            full_summ = "\n".join([f"• {s}" for s in summ_list])
            
            st.session_state['history'].insert(0, {
                "title": article.title,
                "summary": full_summ,
                "url": input_url
            })
            st.rerun()
        except Exception as e:
            st.error(f"오류가 발생했습니다: {e}")

# --- 6. 카드 출력 ---
st.title("🚀 스마트 뉴스 요약 카드")

if st.session_state['history']:
    cols = st.columns(2)
    for idx, item in enumerate(st.session_state['history']):
        with cols[idx % 2]:
            # 카드 디자인 (삭제 버튼 공간 확보를 위해 relative 포지션 사용)
            st.markdown(f"""
                <div class="news-card" style="position: relative;">
                    <div class="card-title">📌 {item['title']}</div>
                    <div class="card-summary">{item['summary'].replace('\n', '<br>')}</div>
                </div>
                """, unsafe_allow_html=True)
            
            # 버튼들을 가로로 배치 (전송 / 삭제)
            btn_col1, btn_col2 = st.columns([4, 1])
            with btn_col1:
                if st.button(f"📱 {idx+1}번 뉴스 전송", key=f"send_{idx}", use_container_width=True):
                    st.toast("전송 기능을 실행합니다.")
            with btn_col2:
                # 개별 삭제 버튼
                if st.button("❌", key=f"del_{idx}", help="이 카드 삭제"):
                    st.session_state['history'].pop(idx)
                    st.rerun()




