import streamlit as st
import pandas as pd
import random
import os

# --- 1. 세션 상태 설정 ---
if 'page' not in st.session_state:
    st.session_state.page = "main"         
if 'coin' not in st.session_state:
    st.session_state.coin = 0
if 'quiz_queue' not in st.session_state:
    st.session_state.quiz_queue = []       
if 'quiz_index' not in st.session_state:
    st.session_state.quiz_index = 0         
if 'quiz_finished' not in st.session_state:
    st.session_state.quiz_finished = False   
if 'user_feedback' not in st.session_state:
    st.session_state.user_feedback = None   
# 🌟 [버그 수정용] 뽑기 버튼이 클릭되었는지 감지하는 변수 추가
if 'shop_clicked' not in st.session_state:
    st.session_state.shop_clicked = False

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

# 사이드바 설정
st.sidebar.metric(label="🪙 내 보유 코인", value=f"{st.session_state.coin} 개")


# ==========================================
# 🏠 1. 메인 페이지 화면 (카테고리 선택 & 상점)
# ==========================================
if st.session_state.page == "main":
    st.title("🇪🇸 스페인어 복습 퀴즈 & 띠부씰 상점")
    st.markdown("---")
    
    # --- 🎯 퀴즈 섹션 ---
    st.subheader("🎯 퀴즈 도전하기")
    categories = list(category_dfs.keys())
    selected_category = st.selectbox('원하는 카테고리를 골라주세요', categories)

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
            st.session_state.page = "quiz" 
            st.rerun()

    st.markdown("---")
    
    # --- 🎁 상점 섹션 (버그 수정 반영) ---
    st.subheader("🎁 띠부씰 뽑기 상점")
    if st.session_state.coin >= 10:
        # 🌟 버튼을 누르면 disabled가 작동해 두 번 다시 누를 수 없게 잠금 처리합니다.
        if st.button("🎰 10코인으로 뽑기!!", disabled=st.session_state.shop_clicked):
            st.session_state.shop_clicked = True # 버튼 즉시 잠금🔒
            
            images = [f for f in os.listdir() if f.endswith(".png")]
            if images:
                st.session_state.coin -= 10      # 코인부터 깎기!
                selected_img = random.choice(images)
                st.balloons()
                st.image(selected_img, caption=f"축하합니다! {selected_img} 획득!", width=200)
                with open("collection.txt", "a", encoding='utf-8') as f:
                    f.write(selected_img + "\n")
                
                # 뽑기 처리가 끝나면 다음 번을 위해 잠금 해제
                st.session_state.shop_clicked = False
                st.rerun()
            else:
                st.warning("이미지 파일이 없습니다.")
                st.session_state.shop_clicked = False # 에러 시 잠금 해제
    else:
        st.write("코인을 더 모아서 뽑기에 도전하세요! 💪")

    st.markdown("---")
    
    # --- 📖 도감 이동 섹션 ---
    st.subheader("📖 도감 확인하기")
    if st.button("📖 내 컬렉션북 보러가기 →"):
        st.session_state.page = "collection"
        st.rerun()


# ==========================================
# 📝 2. 퀴즈 페이지 화면
# ==========================================
elif st.session_state.page == "quiz":
    st.title("📝 스페인어 퀴즈 진행 중")
    
    if not st.session_state.quiz_queue or st.session_state.quiz_index >= len(st.session_state.quiz_queue):
        st.success("🎉 10문제 세트를 모두 완료했습니다!")
        if st.button("🏠 메인 화면으로 가기"):
            st.session_state.page = "main"
            st.session_state.quiz_queue = [] 
            st.rerun()
    else:
        current_idx = st.session_state.quiz_index
        total_questions = len(st.session_state.quiz_queue)
        q = st.session_state.quiz_queue[current_idx]
        
        st.subheader(f"❓ 문제 {current_idx + 1} / {total_questions}")
        st.caption(f"난이도: {q.get('level', '하')}")
        st.info(f"👉 **{q['quiz']}**")
        st.write(f"💡 뜻: {q['korean']}")
        
        user_answer = st.text_input(
            "정답을 입력하세요:", 
            key=f"ans_{current_idx}", 
            disabled=st.session_state.quiz_finished,
            autocomplete="off"
        )
        
        if not st.session_state.quiz_finished:
            if st.button("정답 제출 🎯"):
                is_correct = (user_answer == str(q['answer'])) or ('answer2' in q and user_answer == str(q['answer2']))
                
                if is_correct:
                    st.session_state.user_feedback = {"status": "success", "msg": "Correct! 정답입니다! 🎉"}
                    lvl = q.get('level', '하')
                    st.session_state.coin += 3 if lvl=='상' else 2 if lvl=='중' else 1
                else:
                    st.session_state.user_feedback = {"status": "error", "msg": f"Incorrect! 정답은 [{q['answer']}] 입니다. 🥲"}
                
                st.session_state.quiz_finished = True
                st.rerun()
                
        else:
            if st.session_state.user_feedback["status"] == "success":
                st.success(st.session_state.user_feedback["msg"])
            else:
                st.error(st.session_state.user_feedback["msg"])
                
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
