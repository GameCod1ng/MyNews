# TELEGRAM_TOKEN = "8716377813:AAFXQwYLxJSA0Afiob_bzlFgBnCiF1n3oJM"
# CHAT_ID = "8628716011"

            
            
import streamlit as st
from newspaper import Article
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
    """TF-IDF 기반 문장 요약"""
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    if len(sentences) <= n: return sentences
    tfidf = TfidfVectorizer().fit_transform(sentences)
    sentence_scores = np.array(tfidf.sum(axis=1)).flatten()
    top_indices = np.argsort(sentence_scores)[-n:]
    top_indices.sort()
    return [sentences[i] for i in top_indices]

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
    with st.spinner('뉴스를 읽고 요약하는 중...'):
        try:
            article = Article(input_url, language='ko')
            article.download()
            article.parse()
            
            summ_list = summarize_text(article.text, n=summary_count)
            full_summ = "\n".join([f"• {s}" for s in summ_list])
            
            # 히스토리에 저장 (최신순)
            new_item = {
                "title": article.title,
                "summary": full_summ,
                "url": input_url
            }
            st.session_state['history'].insert(0, new_item)
            st.success("새로운 뉴스 카드가 추가되었습니다!")
        except Exception as e:
            st.error(f"오류 발생: {e}")

# [중앙 뉴스 카드 출력 영역]
if st.session_state['history']:
    st.subheader("📋 요약된 뉴스 카드 목록")
    
    # 컬럼을 나누어 배치 (2열 배치)
    cols = st.columns(2)
    for idx, item in enumerate(st.session_state['history']):
        col_idx = idx % 2
        with cols[col_idx]:
            # 카드 렌더링
            st.markdown(f"""
                <div class="news-card">
                    <div class="card-title">{item['title']}</div>
                    <div class="card-body">{item['summary'].replace('•', '<br>•')}</div>
                </div>
                """, unsafe_allow_html=True)
            
            # 전송 버튼 (key 값은 고유해야 함)
            if st.button(f"📱 {idx+1}번 뉴스 푸시 전송", key=f"push_{idx}"):
                push_msg = f"📢 뉴스 요약: {item['title']}\n\n{item['summary']}\n\n바로가기: {item['url']}"
                try:
                    asyncio.run(send_telegram_msg(push_msg))
                    st.toast("텔레그램 전송 완료!")
                except Exception as e:
                    st.error(f"전송 실패: {e}")
else:
    st.write("아직 요약된 뉴스가 없습니다. 왼쪽 사이드바에서 URL을 입력하세요.")
