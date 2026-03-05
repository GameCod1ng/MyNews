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

# --- 2. 세션 상태 초기화 ---
if 'history' not in st.session_state:
    st.session_state['history'] = []

# --- 3. 핵심 기능 함수 ---

async def send_telegram_msg(text):
    """텔레그램 메시지 전송 (비동기)"""
    if not TELEGRAM_TOKEN or "YOUR" in TELEGRAM_TOKEN:
        return
    bot = Bot(token=TELEGRAM_TOKEN)
    await bot.send_message(chat_id=CHAT_ID, text=text)

def summarize_text(text, n=3):
    # 1. 텍스트가 너무 짧으면 필터링 없이 반환
    if len(text.strip()) < 50:
        return ["본문 내용이 너무 짧아 요약이 불가능합니다."]

    # 2. 문장 분리
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    
    # 3. 필터링 (최소한의 필터만 적용)
    filter_keywords = ["기사 섹션 분류", "중복 분류"]
    clean_sentences = [s.strip() for s in sentences if len(s.strip()) > 10 
                       and not any(k in s for k in filter_keywords)]

    # 4. 필터링 후 문장이 너무 적으면 그냥 앞부분 반환
    if len(clean_sentences) <= n:
        return clean_sentences if clean_sentences else [text[:200] + "..."]

    try:
        tfidf = TfidfVectorizer().fit_transform(clean_sentences)
        sentence_scores = np.array(tfidf.sum(axis=1)).flatten()
        top_indices = np.argsort(sentence_scores)[-n:]
        top_indices.sort()
        return [clean_sentences[i] for i in top_indices]
    except:
        # 오류 발생 시 앞 3문장 강제 반환
        return clean_sentences[:n]

def get_latest_news_url(keyword):
    """구글에서 키워드로 최신 뉴스 URL 1개 추출"""
    try:
        query = f"{keyword} 뉴스"
        # stop=10으로 상위 결과 중 하나를 가져옴
        for url in search(query, num_results=5, lang="ko"):
            if "news" in url or "article" in url:
                return url
    except Exception as e:
        print(f"검색 오류: {e}")
    return None

# --- 4. 자동화 스케줄러 로직 ---

def auto_morning_push():
    """아침 8시에 실행될 작업 내용"""
    url = get_latest_news_url(SEARCH_KEYWORD)
    if url:
        article = Article(url, language='ko')
        article.download()
        article.parse()
        
        summary_list = summarize_text(article.text, n=3)
        summary_text = "\n".join([f"• {s}" for s in summary_list])
        
        msg = f"⏰ [아침 8시 정기 알림]\n키워드: {SEARCH_KEYWORD}\n\n제목: {article.title}\n{summary_text}\n\n링크: {url}"
        
        # 비동기 함수 실행을 위한 이벤트 루프 생성
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(send_telegram_msg(msg))
        loop.close()

def run_scheduler():
    """별도 스레드에서 돌아갈 스케줄러 루프"""
    schedule.every().day.at("08:00").do(auto_morning_push)
    while True:
        schedule.run_pending()
        time.sleep(60) # 1분마다 체크

# 앱 시작 시 스케줄러 스레드 딱 한 번만 실행
if 'scheduler_started' not in st.session_state:
    daemon_thread = threading.Thread(target=run_scheduler, daemon=True)
    daemon_thread.start()
    st.session_state['scheduler_started'] = True

# --- 5. UI 구성 (Streamlit) ---

st.set_page_config(page_title="AI News Push", page_icon="📲", layout="wide")

# 카드 스타일 CSS
st.markdown("""
    <style>
    .news-card {
        background-color: #f9f9f9;
        padding: 20px;
        border-radius: 12px;
        border-left: 6px solid #007BFF;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.05);
        margin-bottom: 15px;
        color: #333;
    }
    .card-title { font-size: 1.2rem; font-weight: bold; color: #111; margin-bottom: 8px; }
    .card-body { font-size: 0.95rem; line-height: 1.6; }
    </style>
    """, unsafe_allow_html=True)

# 사이드바 설정
with st.sidebar:
    st.title("📲 알림 설정")
    st.info(f"💡 매일 아침 08:00에 '{SEARCH_KEYWORD}' 뉴스를 자동으로 발송합니다.")
    
    st.divider()
    
    input_url = st.text_input("🔗 분석할 뉴스 URL 입력")
    summary_count = st.slider("요약 문장 수", 1, 5, 3)
    analyze_btn = st.button("뉴스 분석 및 카드 추가")
    
    if st.button("내역 모두 삭제"):
        st.session_state['history'] = []
        st.rerun()

st.title("🚀 AI 뉴스 스마트 푸시 & 카드")

# [수동 분석 로직]
if analyze_btn and input_url:
    with st.spinner('뉴스를 읽어오는 중...'):
        try:
            # 브라우저처럼 보이기 위한 설정 추가
            config = Config()
            config.browser_user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            
            article = Article(input_url, language='ko', config=config)
            article.download()
            article.parse()
            
            # 본문 추출 확인용 로그 (디버깅용)
            if not article.text.strip():
                st.error("사이트에서 본문을 읽어오지 못했습니다. URL을 다시 확인해주세요.")
            else:
                summ_list = summarize_text(article.text, n=summary_count)
                full_summ = "\n".join([f"• {s}" for s in summ_list])
                
                st.session_state['history'].insert(0, {
                    "title": article.title,
                    "summary": full_summ,
                    "url": input_url
                })
                st.rerun() # 화면 즉시 갱신
        except Exception as e:
            st.error(f"분석 중 오류 발생: {e}")

# 2. [중앙 뉴스 카드 출력 영역] - HTML 구조 재점검
if st.session_state['history']:
    st.subheader("📋 요약된 뉴스 카드 목록")
    cols = st.columns(2)
    
    for idx, item in enumerate(st.session_state['history']):
        col_idx = idx % 2
        with cols[col_idx]:
            # HTML용 줄바꿈 처리
            display_summary = item['summary'].replace('\n', '<br>')
            
            st.markdown(f"""
                <div class="news-card">
                    <div style="font-size: 1.25rem; font-weight: bold; color: #007BFF; margin-bottom: 10px;">
                        📌 {item['title']}
                    </div>
                    <div style="background-color: #f1f3f5; padding: 15px; border-radius: 8px; font-size: 0.95rem; color: #333; line-height: 1.6;">
                        {display_summary}
                    </div>
                    <div style="margin-top: 15px; font-size: 0.85rem; color: #888; word-break: break-all;">
                        📎 소스: <a href="{item['url']}" target="_blank" style="color: #888; text-decoration: none;">{item['url'][:60]}...</a>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            if st.button(f"📱 {idx+1}번 뉴스 전송", key=f"send_{idx}", use_container_width=True):
                # 전송 로직 생략 (기존과 동일)
                pass




