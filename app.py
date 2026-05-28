import streamlit as st
import pandas as pd
import random
import os

# --- 1. 세션 상태 설정 (페이지 및 퀴즈 상태 관리 변수) ---
if 'page' not in st.session_state:
    st.session_state.page = "main"         # 현재 페이지 (main, quiz, collection)
if 'coin' not in st.session_state:
    st.session_state.coin = 0
if 'quiz_queue' not in st.session_state:
    st.session_state.quiz_queue = []       # 10개 문제가 담길 리스트
if 'quiz_index' not in st.session_state:
    st.session_state.quiz_index = 0         # 현재 풀고 있는 문제 번호
if 'quiz_finished' not in st.session_state:
    st.session_state.quiz_finished = False   # 현재 문제의 정답 제출 여부
if 'user_feedback' not in st.session_state:
    st.session_state.user_feedback = None   # "정답입니다/틀렸습니다" 결과를 저장할 변수

# --- 2. 데이터 불러오기 및 분류 ---
try:
    df = pd.read_csv('spanish.csv', encoding='utf-8')
    category_dfs = {
        'ser': df[df['category']=='ser'],
        'estar': df[df['category']=='estar'],
        '이름 및 성': df[df['category']=='이름 및 성'],
        '상태 및 기분': df[df['category']=='상태 및 기분'],
        '현재진행형': df[df['category']=='현재진행형'],
        '성격 및 외모': df[df['category']=='성격 및 외모'],
        '국적, 국적형용사': df[df['category']=='국적, 국적형용사'],
        '가족 관계': df[df['category']=='가족 관계'],
        '생일': df[df['category']=='생일'],
        '시간': df[df['category']=='시간'],
        '요일 및 날짜': df[df['category']=='요일 및 날짜'],
        '몇시에': df[df['category']=='몇시에'],
        '날씨': df[df['category']=='날씨'],
        '숫자': df[df['category']=='숫자']
    }
except FileNotFoundError:
    st.error("Linux 파일 폴더에 'spanish.csv' 파일이 있는지 확인해주세요!")
    st.stop()

# 사이드바는 항상 보임
st.sidebar.metric(label="🪙 내 보유 코인", value=f"{st.session_state.coin} 개")


# ==========================================
# 🏠 1. 메인 페이지 화면 (카테고리 선택 & 상점)
# ==========================================
if st.session_state.page == "main":
    st.title("🇪🇸 스페인어 복습 퀴즈")
    
    # 컬렉션북 이동 버튼
    if st.button("📖 내 컬렉션북 보러가기 →"):
        st.session_state.page = "collection"
        st.rerun()

    st.markdown("---")
    st.subheader("🎯 퀴즈 시작하기")
    
    categories = list(category_dfs.keys())
    selected_category = st.selectbox('원하는 카테고리를 골라주세요', categories)

    # 🌟 퀴즈 시작 버튼을 누르면 퀴즈 페이지로 전환!
    if st.button("🚀 퀴즈 시작하기 (10문제 세트)"):
        selected_df = category_dfs[selected_category]
        if len(selected_df) == 0:
            st.warning("해당 카테고리에 데이터가 없습니다.")
        else:
            count = min(10, len(selected_df))
            st.session_state.quiz_queue = selected_df.sample(n=count).to_dict(orient='records')
            st.session_state.quiz_index = 0
            st.session_state.quiz_finished = False
            st.session_state.user_feedback = None
            st.session_state.page = "quiz" # 퀴즈 페이지로 이동!
            st.rerun()

    st.markdown("---")
    
    # --- 상점 섹션 ---
    st.subheader("🎁 띠부씰 뽑기 상점")
    if st.session_state.coin >= 10:
        if st.button("🎰 10코인으로 뽑기!!"):
            images = [f for f in os.listdir() if f.endswith(".png")]
            if images:
                st.session_state.coin -= 10
                selected_img = random.choice(images)
                st.balloons()
                st.image(selected_img, caption=f"축하합니다! {selected_img} 획득!", width=200)
                with open("collection.txt", "a", encoding='utf-8') as f:
                    f.write(selected_img + "\n")
            else:
                st.warning("이미지 파일이 없습니다.")
    else:
        st.write("코인을 더 모아서 뽑기에 도전하세요! 💪")


# ==========================================
# 📝 2. 퀴즈 페이지 화면 (독립된 퀴즈 전용 창)
# ==========================================
elif st.session_state.page == "quiz":
    st.title("📝 스페인어 퀴즈 진행 중")
    
    # 안전장치: 혹시나 문제가 비어있으면 메인으로 튕겨내기
    if not st.session_state.quiz_queue or st.session_state.quiz_index >= len(st.session_state.quiz_queue):
        st.success("🎉 10문제 세트를 모두 완료했습니다!")
        if st.button("🏠 메인 화면으로 가기"):
            st.session_state.page = "main"
            st.session_state.quiz_queue = [] # 큐 초기화
            st.rerun()
    else:
        current_idx = st.session_state.quiz_index
        total_questions = len(st.session_state.quiz_queue)
        q = st.session_state.quiz_queue[current_idx]
        
        st.subheader(f"❓ 문제 {current_idx + 1} / {total_questions}")
        st.caption(f"난이도: {q.get('level', '하')}")
        st.info(f"👉 **{q['quiz']}**")
        st.write(f"💡 뜻: {q['korean']}")
        
        # 🌟 핵심 기능: 정답 제출이 끝나면(quiz_finished가 True가 되면) disabled=True 가 작동하여 정답 수정 불가능!
        user_answer = st.text_input(
            "정답을 입력하세요:", 
            key=f"ans_{current_idx}", 
            disabled=st.session_state.quiz_finished
        )
        
        # 정답 제출 전 버튼
        if not st.session_state.quiz_finished:
            if st.button("정답 제출 🎯"):
                is_correct = (user_answer == str(q['answer'])) or ('answer2' in q and user_answer == str(q['answer2']))
                
                # 피드백 내용 저장 (화면 리셋 방지용)
                if is_correct:
                    st.session_state.user_feedback = {"status": "success", "msg": "Correct! 정답입니다! 🎉"}
                    lvl = q.get('level', '하')
                    st.session_state.coin += 3 if lvl=='상' else 2 if lvl=='중' else 1
                else:
                    st.session_state.user_feedback = {"status": "error", "msg": f"Incorrect! 정답은 [{q['answer']}] 입니다. 🥲"}
                
                st.session_state.quiz_finished = True
                st.rerun()
                
        # 정답 제출 후 화면 (결과를 보여주고 입력창과 제출버튼은 얼려버림)
        else:
            # 보관해 둔 피드백 화면에 뿌려주기
            if st.session_state.user_feedback["status"] == "success":
                st.success(st.session_state.user_feedback["msg"])
            else:
                st.error(st.session_state.user_feedback["msg"])
                
            # 제출 버튼 대신 "다음 문제" 버튼 띄우기
            if st.button("다음 문제 넘어가기 ➡️"):
                st.session_state.quiz_index += 1
                st.session_state.quiz_finished = False
                st.session_state.user_feedback = None
                st.rerun()


# ==========================================
# 📖 3. 컬렉션 페이지 화면 (도감)
# ==========================================
elif st.session_state.page == "collection":
    st.title("📖 나의 띠부씰 컬렉션북")
    
    if st.button("← 메인 화면으로 돌아가기"):
        st.session_state.page = "main"
        st.rerun()
    
    st.markdown("---")

    if os.path.exists("collection.txt"):
        with open("collection.txt", "r", encoding='utf-8') as f:
            collection = [line.strip() for line in f if line.strip()]
        
        if collection:
            cols = st.columns(4) 
            for idx, item in enumerate(collection):
                with cols[idx % 4]:
                    try:
                        st.image(item, caption=item, use_container_width=True)
                    except:
                        st.caption(f"⚠️ {item} 없음")
        else:
            st.write("아직 수집한 띠부씰이 없습니다.")
    else:
        st.write("도감이 텅 비어있네요. 첫 번째 뽑기를 진행해보세요!")
