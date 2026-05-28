import streamlit as st
import pandas as pd
import random
import os

# --- 1. 세션 상태 설정 (사용자 로그인 및 페이지 관리) ---
if 'user_id' not in st.session_state:
    st.session_state.user_id = None        # 로그인한 학번 저장 변수
if 'page' not in st.session_state:
    st.session_state.page = "main"         # 현재 페이지 (main, quiz, collection)
if 'coin' not in st.session_state:
    st.session_state.coin = 0              # 현재 코인
if 'quiz_queue' not in st.session_state:
    st.session_state.quiz_queue = []       
if 'quiz_index' not in st.session_state:
    st.session_state.quiz_index = 0         
if 'quiz_finished' not in st.session_state:
    st.session_state.quiz_finished = False   
if 'user_feedback' not in st.session_state:
    st.session_state.user_feedback = None   
if 'shop_clicked' not in st.session_state:
    st.session_state.shop_clicked = False


# --- 2. 💾 파일 저장 및 불러오기 함수 정의 ---
def save_user_data(user_id, coin):
    """현재 세션의 코인 상태와 기존 도감을 학번 파일에 저장합니다."""
    collection_file = f"{user_id}_collection.txt"
    current_items = []
    if os.path.exists(collection_file):
        with open(collection_file, "r", encoding='utf-8') as f:
            current_items = [line.strip() for line in f if line.strip()]
            
    with open(f"{user_id}_save.txt", "w", encoding='utf-8') as f:
        f.write(f"{coin}\n")
        for item in current_items:
            f.write(f"{item}\n")

def load_user_data(user_id):
    """학번 파일이 있으면 코인과 도감 데이터를 불러옵니다."""
    save_file = f"{user_id}_save.txt"
    collection_file = f"{user_id}_collection.txt"
    
    if os.path.exists(save_file):
        with open(save_file, "r", encoding='utf-8') as f:
            lines = [line.strip() for line in f if line.strip()]
        if lines:
            st.session_state.coin = int(lines[0])
            with open(collection_file, "w", encoding='utf-8') as cf:
                for item in lines[1:]:
                    cf.write(f"{item}\n")
    else:
        st.session_state.coin = 0
        if os.path.exists(collection_file):
            os.remove(collection_file)
        save_user_data(user_id, 0)


# --- 3. 데이터 불러오기 및 분류 ---
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


# ==========================================
# 🔐 0. 로그인 화면 (요청사항 반영: 학번 입력 안내)
# ==========================================
if st.session_state.user_id is None:
    st.title("🔐 스페인어 복습 퀴즈 시스템")
    st.write("개인 플레이 데이터를 저장하고 불러오기 위해 학번을 입력해 주세요.")
    
    # 🌟 문구를 "학번을 입력해주세요"로 친절하게 수정했습니다.
    input_id = st.text_input("학번을 입력해주세요 (예: 30101):", autocomplete="off").strip()
    
    if st.button("로그인 및 메인화면 이동 🚀"):
        if input_id == "":
            st.warning("학번을 올바르게 입력해주세요!")
        else:
            st.session_state.user_id = input_id
            load_user_data(input_id) # 💾 입력한 학번에 맞는 데이터 로드
            st.success(f"확인되었습니다. {input_id}님, 환영합니다!")
            st.rerun() # 메인 화면으로 즉시 이동
    st.stop() 


# 사이드바 설정 (로그인 완료 후 학번 표시)
st.sidebar.title(f"👤 학번: {st.session_state.user_id}")
st.sidebar.metric(label="🪙 내 보유 코인", value=f"{st.session_state.coin} 개")
if st.sidebar.button("다른 학번으로 로그인 🚪"):
    st.session_state.user_id = None
    st.session_state.page = "main"
    st.rerun()


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
    
    # --- 🎁 상점 섹션 ---
    st.subheader("🎁 띠부씰 뽑기 상점")
    if st.session_state.coin >= 10:
        if st.button("🎰 10코인으로 뽑기!!", disabled=st.session_state.shop_clicked):
            st.session_state.shop_clicked = True 
            
            images = [f for f in os.listdir() if f.endswith(".png")]
            if images:
                st.session_state.coin -= 10      
                selected_img = random.choice(images)
                st.balloons()
                st.image(selected_img, caption=f"축하합니다! {selected_img} 획득!", width=200)
                
                user_collection = f"{st.session_state.user_id}_collection.txt"
                with open(user_collection, "a", encoding='utf-8') as f:
                    f.write(selected_img + "\n")
                
                save_user_data(st.session_state.user_id, st.session_state.coin)
                
                st.session_state.shop_clicked = False
                st.rerun()
            else:
                st.warning("이미지 파일이 없습니다.")
                st.session_state.shop_clicked = False 
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
                
                save_user_data(st.session_state.user_id, st.session_state.coin)
                
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

    user_collection = f"{st.session_state.user_id}_collection.txt"
    if os.path.exists(user_collection):
        with open(user_collection, "r", encoding='utf-8') as f:
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
