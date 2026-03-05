import streamlit as st
from newspaper import Article
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np
import re
import asyncio
from telegram import Bot

# --- 텔레그램 설정 (본인의 정보로 수정하세요) ---
TELEGRAM_TOKEN = "8716377813:AAFXQwYLxJSA0Afiob_bzlFgBnCiF1n3oJM"
CHAT_ID = "8628716011"

# 메시지 전송 함수
async def send_telegram_msg(text):
    bot = Bot(token=TELEGRAM_TOKEN)
    await bot.send_message(chat_id=CHAT_ID, text=text)

# 요약 함수
def summarize_text(text, n=3):
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    if len(sentences) <= n: return sentences
    tfidf = TfidfVectorizer().fit_transform(sentences)
    sentence_scores = np.array(tfidf.sum(axis=1)).flatten()
    top_indices = np.argsort(sentence_scores)[-n:]
    top_indices.sort()
    return [sentences[i] for i in top_indices]

# --- UI 구성 ---
st.set_page_config(page_title="AI News Push", page_icon="📲")

with st.sidebar:
    st.title("📲 알림 설정")
    url = st.text_input("🔗 뉴스 URL")
    summary_count = st.slider("요약 문장 수", 1, 5, 3)
    analyze_btn = st.button("분석 시작")

st.title("🚀 뉴스 분석 및 스마트 푸시")

if analyze_btn and url:
    with st.spinner('분석 중...'):
        article = Article(url, language='ko')
        article.download(); article.parse()
        
        summary_list = summarize_text(article.text, n=summary_count)
        full_summary = "\n".join([f"• {s}" for s in summary_list])
        
        st.subheader(article.title)
        st.info(full_summary)
        
        # 세션 상태에 요약본 저장 (전송 버튼용)
        st.session_state['summary'] = f"📢 뉴스 요약: {article.title}\n\n{full_summary}\n\n바로가기: {url}"

# 전송 버튼 (요약 결과가 있을 때만 표시)
if 'summary' in st.session_state:
    if st.button("📱 내 휴대폰으로 푸시 알림 보내기"):
        try:
            asyncio.run(send_telegram_msg(st.session_state['summary']))
            st.success("✅ 텔레그램으로 알림을 보냈습니다!")
        except Exception as e:
            st.error(f"전송 실패: {e}")