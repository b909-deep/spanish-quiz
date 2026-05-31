import streamlit as st
import pandas as pd
import random
import os
import time

# --- 1. 세션 상태 설정 (상태 관리 변수들) ---
if 'user_id' not in st.session_state:
    st.session_state.user_id = None        # 로그인 학번
if 'page' not in st.session_state:
    st.session_state.page = "main"         # 현재 화면 (main, quiz, matching, collection, ranking)
if 'coin' not in st.session_state:
    st.session_state.coin = 0              # 코인 수
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

# [단어 매칭 게임용 변수]
if 'match_words' not in st.session_state:
    st.session_state.match_words = []      # 게임에 쓰일 단어 목록
if 'left_cards' not in st.session_state:
    st.session_state.left_cards = []       # 셔플된 스페인어 카드
if 'right_cards' not in st.session_state:
    st.session_state.right_cards = []      # 셔플된 한국어 카드
if 'selected_left' not in st.session_state:
    st.session_state.selected_left = None  # 선택한 스페인어 단어
if 'selected_right' not in st.session_state:
    st.session_state.selected_right = None # 선택한 한국어 단어
if 'matched_pairs' not in st.session_state:
    st.session_state.matched_pairs = set() # 맞춘 단어들의 스페인어 텍스트 저장
if 'start_time' not in st.session_state:
    st.session_state.start_time = 0        # 게임 시작 시각
if 'elapsed_time' not in st.session_state:
    st.session_state.elapsed_time = 0      # 걸린 시간
if 'match_game_over' not in st.session_state:
    st.session_state.match_game_over = False
if 'current_match_category' not in st.session_state:
    st.session_state.current_match_category = ""


# --- 2. 💾 파일 저장 / 로드 / 랭킹 기록 함수 ---
def save_user_data(user_id, coin):
    """코인과 도감을 유저 세이브 파일에 백업합니다."""
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
    """학번 파일이 있으면 코인 데이터를 불러옵니다."""
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

def save_matching_record(category, user_id, elapsed_time):
    """매칭 게임 완료 시 카테고리별 최고 기록을 저장합니다."""
    record_file = "matching_rankings.txt"
    records = {}
    if os.path.exists(record_file):
        with open(record_file, "r", encoding='utf-8') as f:
            for line in f:
                if "," in line:
                    cat, uid, t_val = line.strip().split(",")
                    records[cat] = (uid, float(t_val))
                    
    if category not in records or elapsed_time < records[category][1]:
        records[category] = (user_id, elapsed_time)
        
    with open(record_file, "w", encoding='utf-8') as f:
        for cat, (uid, t_val) in records.items():
            f.write(f"{cat},{uid},{t_val}\n")

def get_matching_rankings():
    """랭킹 목록을 반환합니다."""
    record_file = "matching_rankings.txt"
    records = {}
    if os.path.exists(record_file):
        with open(record_file, "r", encoding='utf-8') as f:
            for line in f:
                if "," in line:
                    cat, uid, t_val = line.strip().split(",")
                    records[cat] = (uid, float(t_val))
    return records


# --- 3. 📝 두 가지 단어장 데이터 파일 읽기 ---
# 파일 1: 기존 주관식 퀴즈용 파일
QUIZ_FILE = 'spanish.csv'
try:
    df_quiz = pd.read_csv(QUIZ_FILE, encoding='utf-8')
    # 기존 코드의 한글 카테고리 분류 방식 유지
    quiz_categories = [
        'ser', 'estar', '이름 및 성', '상태 및 기분', '현재진행형', 
        '성격 및 외모', '국적, 국적형용사', '가족 관계', '생일', 
        '시간', '요일 및 날짜', '몇시에', '날씨', '숫자'
    ]
    # 실제 파일에 있는 카테고리만 필터링
    quiz_categories = [cat for cat in quiz_categories if cat in df_quiz['category'].unique()]
except FileNotFoundError:
    st.error(f"Linux 파일 폴더에 기존 '{QUIZ_FILE}' 파일이 있는지 확인해주세요!")
    st.stop()

# 파일 2: 새로운 단어 매칭 게임용 파일 (새로 업로드한 파일)
MATCH_FILE = '제목 없는 스프레드시트 - 시트1.csv'
try:
    df_match = pd.read_csv(MATCH_FILE, encoding='utf-8')
    df_match.columns = [c.strip() for c in df_match.columns]
    df_match['Category'] = df_match['Category'].astype(str).str.strip()
    match_categories = sorted(df_match['Category'].unique().tolist())
except FileNotFoundError:
    st.error(f"Linux 파일 폴더에 새로운 '{MATCH_FILE}' 파일이 있는지 확인해주세요!")
    st.stop()


# ==========================================
# 🔐 0. 로그인 화면 (학번 입력창)
# ==========================================
if st.session_state.user_id is None:
    st.title("🔐 스페인어 학습 통합 시스템")
    st.write("개인 플레이 데이터를 관리하기 위해 학번을 입력해 주세요.")
    
    input_id = st.text_input("학번을 입력해주세요 (예: 30101):", autocomplete="off").strip()
    
    if st.button("로그인 및 대시보드 이동 🚀"):
        if input_id == "":
            st.warning("학번을 올바르게 입력해주세요!")
        else:
            st.session_state.user_id = input_id
            load_user_data(input_id)
            st.success(f"확인되었습니다. {input_id}님, 환영합니다!")
            st.rerun()
    st.stop()


# --- 사이드바 설정 ---
st.sidebar.title(f"👤 학번: {st.session_state.user_id}")
st.sidebar.metric(label="🪙 내 보유 코인", value=f"{st.session_state.coin} 개")
if st.sidebar.button("다른 학번으로 로그인 🚪"):
    st.session_state.user_id = None
    st.session_state.page = "main"
    st.rerun()


# ==========================================
# 🏠 1. 메인 대시보드 화면
# ==========================================
if st.session_state.page == "main":
    st.title("🇪🇸 스페인어 복습 & 띠부씰 시스템")
    st.write(f"안녕하세요 {st.session_state.user_id}님! 원하시는 메뉴를 선택하세요.")
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📝 주관식 퀴즈 (기존 파일 기준)")
        # 기존 spanish.csv 카테고리 선택
        selected_quiz_cat = st.selectbox('퀴즈 카테고리 선택', quiz_categories, key="quiz_cat_select")
        
        if st.button("🚀 1. 스페인어 퀴즈 시작", use_container_width=True):
            selected_df = df_quiz[df_quiz['category'] == selected_quiz_cat]
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
                
        st.markdown(" ")
        st.subheader("📖 내 도감")
        if st.button("📖 3. 나의 띠부씰 컬렉션 보기", use_container_width=True):
            st.session_state.page = "collection"
            st.rerun()

    with col2:
        st.subheader("🧩 매칭 게임 (새로운 파일 기준)")
        # 새로운 '제목 없는 스프레드시트' 카테고리 선택
        selected_match_cat = st.selectbox('매칭 게임 카테고리 선택', match_categories, key="match_cat_select")
        
        if st.button("🧩 2. 단어 매칭 카드 게임 시작", use_container_width=True):
            selected_df = df_match[df_match['Category'] == selected_match_cat]
            if len(selected_df) == 0:
                st.warning("해당 카테고리에 데이터가 없습니다.")
            else:
                count = min(10, len(selected_df))
                chosen_words = selected_df.sample(n=count).to_dict(orient='records')
                
                st.session_state.match_words = chosen_words
                st.session_state.left_cards = [w['Spanish'].strip() for w in chosen_words]
                st.session_state.right_cards = [w['Korean'].strip() for w in chosen_words]
                random.shuffle(st.session_state.left_cards)
                random.shuffle(st.session_state.right_cards)
                
                st.session_state.selected_left = None
                st.session_state.selected_right = None
                st.session_state.matched_pairs = set()
                st.session_state.current_match_category = selected_match_cat
                st.session_state.match_game_over = False
                st.session_state.start_time = time.time()
                st.session_state.page = "matching"
                st.rerun()
                
        st.markdown(" ")
        st.subheader("🏆 명예의 전당")
        if st.button("🏆 4. 카테고리별 랭킹 보기", use_container_width=True):
            st.session_state.page = "ranking"
            st.rerun()

    st.markdown("---")
    
    # [메뉴 5] 띠부씰 뽑기 상점
    st.subheader("🎁 5. 띠부씰 뽑기 상점")
    if st.session_state.coin >= 10:
        if st.button("🎰 10코인으로 뽑기!!", disabled=st.session_state.shop_clicked, use_container_width=True):
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
                st.warning("폴더 내에 이미지(.png) 파일이 없습니다.")
                st.session_state.shop_clicked = False 
    else:
        st.write("코인을 더 모아서 띠부씰 뽑기에 도전하세요! (10코인 필요) 💪")


# ==========================================
# 📝 2. 퀴즈 페이지 화면 (spanish.csv 기준)
# ==========================================
elif st.session_state.page == "quiz":
    st.title("📝 스페인어 주관식 퀴즈")
    
    if not st.session_state.quiz_queue or st.session_state.quiz_index >= len(st.session_state.quiz_queue):
        st.success("🎉 10문제 세트를 모두 완료했습니다!")
        if st.button("🏠 홈 화면으로 돌아가기"):
            st.session_state.page = "main"
            st.session_state.quiz_queue = [] 
            st.rerun()
    else:
        current_idx = st.session_state.quiz_index
        total_questions = len(st.session_state.quiz_queue)
        q = st.session_state.quiz_queue[current_idx]
        
        st.subheader(f"❓ 문제 {current_idx + 1} / {total_questions}")
        st.info(f"👉 뜻: **{q['korean']}**")  # 기존 파일의 소문자 'korean' 유지
        
        user_answer = st.text_input(
            "정답 입력 (스페인어):", 
            key=f"ans_{current_idx}", 
            disabled=st.session_state.quiz_finished,
            autocomplete="off"
        ).strip()
        
        if not st.session_state.quiz_finished:
            if st.button("정답 제출 🎯"):
                # 기존 파일의 소문자 'answer' 및 'answer2' 대조 로직 유지
                is_correct = (user_answer == str(q['answer']).strip()) or ('answer2' in q and user_answer == str(q['answer2']).strip())
                
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
# 🧩 3. 단어 매칭 카드 게임 화면 (새 단어장 파일 기준)
# ==========================================
elif st.session_state.page == "matching":
    st.title("🧩 단어 매칭 카드 게임")
    st.write(f"카테고리: **{st.session_state.current_match_category}**")
    
    if not st.session_state.match_game_over:
        st.session_state.elapsed_time = round(time.time() - st.session_state.start_time, 2)
    
    st.metric(label="⏱️ 경과 시간", value=f"{st.session_state.elapsed_time} 초")
    
    if len(st.session_state.matched_pairs) == len(st.session_state.match_words) and not st.session_state.match_game_over:
        st.session_state.match_game_over = True
        save_matching_record(st.session_state.current_match_category, st.session_state.user_id, st.session_state.elapsed_time)
        st.session_state.coin += 5
        save_user_data(st.session_state.user_id, st.session_state.coin)

    if st.session_state.match_game_over:
        st.balloons()
        st.success(f"🎉 모든 카드 매칭 성공!! 총 걸린 시간: {st.session_state.elapsed_time}초 (보너스 5코인 획득!)")
        if st.button("🏠 홈 화면으로 가기"):
            st.session_state.page = "main"
            st.rerun()
    else:
        st.write("왼쪽의 스페인어 카드와 오른쪽의 한국어 뜻 카드를 하나씩 눌러 짝을 맞추세요!")
        
        col_left, col_right = st.columns(2)
        
        with col_left:
            st.markdown("### 🇪🇸 스페인어")
            for word in st.session_state.left_cards:
                if word in st.session_state.matched_pairs:
                    st.button(f"✅ {word}", key=f"left_done_{word}", disabled=True)
                else:
                    is_selected = (st.session_state.selected_left == word)
                    label = f"⭐ {word}" if is_selected else word
                    if st.button(label, key=f"left_click_{word}"):
                        st.session_state.selected_left = word
                        st.rerun()
                        
        with col_right:
            st.markdown("### 🇰🇷 한국어 뜻")
            for kor_text in st.session_state.right_cards:
                target_word_dict = next((w for w in st.session_state.match_words if w['Korean'].strip() == kor_text), None)
                span_origin = target_word_dict['Spanish'].strip() if target_word_dict else ""
                
                if span_origin in st.session_state.matched_pairs:
                    st.button(f"✅ {kor_text}", key=f"right_done_{kor_text}", disabled=True)
                else:
                    is_selected = (st.session_state.selected_right == kor_text)
                    label = f"⭐ {kor_text}" if is_selected else kor_text
                    if st.button(label, key=f"right_click_{kor_text}"):
                        st.session_state.selected_right = kor_text
                        st.rerun()

        if st.session_state.selected_left and st.session_state.selected_right:
            s_select = st.session_state.selected_left
            k_select = st.session_state.selected_right
            
            correct_dict = next((w for w in st.session_state.match_words if w['Spanish'].strip() == s_select), None)
            
            if correct_dict and correct_dict['Korean'].strip() == k_select:
                st.toast("정답입니다! 👏")
                st.session_state.matched_pairs.add(s_select)
            else:
                st.toast("틀렸습니다! 다시 매칭해 보세요 ❌")
                
            st.session_state.selected_left = None
            st.session_state.selected_right = None
            st.rerun()


# ==========================================
# 📖 4. 컬렉션 페이지 화면 (도감)
# ==========================================
elif st.session_state.page == "collection":
    st.title("📖 나의 띠부씰 컬렉션북")
    
    if st.button("← 홈 화면으로 돌아가기"):
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
        st.write("도감이 비어있네요. 첫 번째 뽑기를 진행해보세요!")


# ==========================================
# 🏆 5. 랭킹보기 화면 (새 단어장 파일 기준)
# ==========================================
elif st.session_state.page == "ranking":
    st.title("🏆 단어 매칭 게임 명예의 전당")
    st.write("새 단어장 카테고리별 매칭 카드 게임을 가장 빠르게 클리어한 학번 1등 목록입니다.")
    
    if st.button("← 홈 화면으로 돌아가기"):
        st.session_state.page = "main"
        st.rerun()
    st.markdown("---")
    
    rank_data = get_matching_rankings()
    
    if rank_data:
        rank_list = []
        for cat, (uid, t_val) in rank_data.items():
            rank_list.append({"카테고리": cat, "1등 학번": uid, "최고 기록 (초)": f"{t_val}초"})
            
        rank_df = pd.DataFrame(rank_list)
        st.table(rank_df)
    else:
        st.write("아직 등록된 랭킹 기록이 없습니다. 최초의 1등에 도전해 보세요! 🏃")
