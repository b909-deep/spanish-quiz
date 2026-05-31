import streamlit as st
import pandas as pd
import random
import os
import time

# --- 1. 세션 상태 설정 (상태 관리 변수들) ---
if 'user_id' not in st.session_state:
    st.session_state.user_id = None        # 로그인 학번
if 'page' not in st.session_state:
    st.session_state.page = "main"         # 현재 화면 
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
    st.session_state.match_words = []      # 현재 세트의 단어 목록
if 'left_cards' not in st.session_state:
    st.session_state.left_cards = []       # 셔플된 스페인어 카드
if 'right_cards' not in st.session_state:
    st.session_state.right_cards = []      # 셔플된 한국어 카드
if 'selected_left' not in st.session_state:
    st.session_state.selected_left = None  # 선택한 스페인어 단어
if 'selected_right' not in st.session_state:
    st.session_state.selected_right = None # 선택한 한국어 단어
if 'matched_pairs' not in st.session_state:
    st.session_state.matched_pairs = set() # 이번 세트에서 맞춘 단어들
if 'start_time' not in st.session_state:
    st.session_state.start_time = 0        # 게임 시작 시각
if 'elapsed_time' not in st.session_state:
    st.session_state.elapsed_time = 0      # 걸린 시간
if 'match_game_over' not in st.session_state:
    st.session_state.match_game_over = False
if 'current_match_category' not in st.session_state:
    st.session_state.current_match_category = ""

# 🌟 [새 기능용 변수] number 카테고리 20개 타임어택 관리 변수
if 'number_stage' not in st.session_state:
    st.session_state.number_stage = 1      # number 카테고리일 때 1세트인지 2세트인지 기록
if 'number_pool' not in st.session_state:
    st.session_state.number_pool = []      # 중복 출제를 막기 위한 전체 단어 풀


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
    """매칭 게임 완료 시 랭킹 기록을 추가합니다. (기록 누적형태로 변경)"""
    record_file = "matching_rankings.txt"
    with open(record_file, "a", encoding='utf-8') as f:
        f.write(f"{category},{user_id},{elapsed_time}\n")

def get_matching_rankings(category):
    """선택한 카테고리의 랭킹 기록을 정렬하여 리스트로 반환합니다."""
    record_file = "matching_rankings.txt"
    records = []
    if os.path.exists(record_file):
        with open(record_file, "r", encoding='utf-8') as f:
            for line in f:
                if "," in line:
                    cat, uid, t_val = line.strip().split(",")
                    if cat.strip() == category.strip():
                        records.append({"학번": uid, "기록 (초)": float(t_val)})
    # 시간이 적게 걸린(빠른) 순서대로 정렬
    records = sorted(records, key=lambda x: x["기록 (초)"])
    return records


# --- 3. 📝 두 가지 단어장 데이터 파일 읽기 ---
QUIZ_FILE = 'spanish.csv'
try:
    df_quiz = pd.read_csv(QUIZ_FILE, encoding='utf-8')
    quiz_categories = [
        'ser', 'estar', '이름 및 성', '상태 및 기분', '현재진행형', 
        '성격 및 외모', '국적, 국적형용사', '가족 관계', '생일', 
        '시간', '요일 및 날짜', '몇시에', '날씨', '숫자'
    ]
    quiz_categories = [cat for cat in quiz_categories if cat in df_quiz['category'].unique()]
except FileNotFoundError:
    st.error(f"Linux 파일 폴더에 기존 '{QUIZ_FILE}' 파일이 있는지 확인해주세요!")
    st.stop()

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
        st.subheader("🧩 매칭 게임 (새 단어장 파일 기준)")
        selected_match_cat = st.selectbox('매칭 게임 카테고리 선택', match_categories, key="match_cat_select")
        
if st.button("🧩 2. 단어 매칭 카드 게임 시작", use_container_width=True):
            selected_df = df_match[df_match['Category'] == selected_match_cat]
            if len(selected_df) == 0:
                st.warning("해당 카테고리에 데이터가 없습니다.")
            else:
                st.session_state.current_match_category = selected_match_cat
                st.session_state.match_game_over = False
                st.session_state.start_time = time.time()
                st.session_state.selected_left = None
                st.session_state.selected_right = None
                st.session_state.matched_pairs = set()

                # 전체 단어를 무작위로 섞어서 풀(Pool)에 저장
                all_words = selected_df.sample(frac=1).to_dict(orient='records')
                st.session_state.number_pool = all_words
                st.session_state.number_stage = 1  # 1세트 시작
                
                # 카테고리가 'number'면 10개씩 2세트(총 20개), 일반 카테고리면 5개씩 2세트(총 10개)로 설정
                if selected_match_cat == "number":
                    st.session_state.match_words = all_words[:10]  # 첫 세트 10개
                else:
                    st.session_state.match_words = all_words[:5]   # 첫 세트 5개
                
                # 카드 리스트 셔플
                st.session_state.left_cards = [w['Spanish'].strip() for w in st.session_state.match_words]
                st.session_state.right_cards = [w['Korean'].strip() for w in st.session_state.match_words]
                random.shuffle(st.session_state.left_cards)
                random.shuffle(st.session_state.right_cards)
                
                st.session_state.page = "matching"
                st.rerun()
                
        st.markdown(" ")
        st.subheader("🏆 명예의 전당")
        if st.button("🏆 4. 카테고리별 랭킹 보기", use_container_width=True):
            st.session_state.page = "ranking"
            st.rerun()

    st.markdown("---")
    
    # 띠부씰 뽑기 상점
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
# 📝 2. 퀴즈 페이지 화면
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
        st.info(f"👉 뜻: **{q['korean']}**")
        
        user_answer = st.text_input(
            "정답 입력 (스페인어):", 
            key=f"ans_{current_idx}", 
            disabled=st.session_state.quiz_finished,
            autocomplete="off"
        ).strip()
        
        if not st.session_state.quiz_finished:
            if st.button("정답 제출 🎯"):
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
# 🧩 3. 단어 매칭 카드 게임 화면 (5개씩 2세트 구성 및 number 10개씩 2세트)
# ==========================================
elif st.session_state.page == "matching":
    st.title("🧩 단어 매칭 카드 게임")
    
    # 상단 정보 메타데이터 표시 (몇 번째 세트인지 직관적으로 인지 가능)
    st.subheader(f"📌 카테고리: {st.session_state.current_match_category} [세트 {st.session_state.number_stage} / 2]")
        
    # 타이머 작동
    if not st.session_state.match_game_over:
        st.session_state.elapsed_time = round(time.time() - st.session_state.start_time, 2)
    
    st.metric(label="⏱️ 현재 경과 시간", value=f"{st.session_state.elapsed_time} 초")
    
    # 이번 세트 단어를 모두 맞췄을 때의 판정
    if len(st.session_state.matched_pairs) == len(st.session_state.match_words) and not st.session_state.match_game_over:
        
        # 아직 1세트 완료 상황일 때 -> 2세트로 자동 연장 진행
        if st.session_state.number_stage == 1:
            st.session_state.number_stage = 2
            st.session_state.matched_pairs = set()  # 맞춘 기록 초기화
            
            # 다음 2세트 단어 범위 가져오기
            if st.session_state.current_match_category == "number":
                # number는 11번째~20번째 단어 (총 20개 완성)
                next_words = st.session_state.number_pool[10:20]
            else:
                # 일반 카테고리는 6번째~10번째 단어 (총 10개 완성)
                next_words = st.session_state.number_pool[5:10]
                
            if len(next_words) > 0:
                st.session_state.match_words = next_words
                st.session_state.left_cards = [w['Spanish'].strip() for w in next_words]
                st.session_state.right_cards = [w['Korean'].strip() for w in next_words]
                random.shuffle(st.session_state.left_cards)
                random.shuffle(st.session_state.right_cards)
                st.toast("👏 1세트 완료! 이어서 2세트가 시작됩니다. 파이팅!")
                st.rerun()
            else:
                # 단어장에 단어가 부족해서 2세트를 만들 수 없는 경우 바로 게임 종료
                st.session_state.match_game_over = True
                save_matching_record(st.session_state.current_match_category, st.session_state.user_id, st.session_state.elapsed_time)
        else:
            # 2세트까지 모두 최종 완료되었을 때 종료
            st.session_state.match_game_over = True
            save_matching_record(st.session_state.current_match_category, st.session_state.user_id, st.session_state.elapsed_time)

    # 게임 종료 화면 출력
    if st.session_state.match_game_over:
        st.balloons()
        if st.session_state.current_match_category == "number":
            st.success(f"🎉 2세트 완료! 총 20개 단어 매칭 성공!! 기록: {st.session_state.elapsed_time}초")
        else:
            st.success(f"🎉 2세트 완료! 총 10개 단어 매칭 성공!! 기록: {st.session_state.elapsed_time}초")
            
        st.caption("⚠️ 매칭 게임은 코인이 제공되지 않습니다.")
        if st.button("🏠 홈 화면으로 가기"):
            st.session_state.page = "main"
            st.rerun()
    else:
        st.write("스페인어 카드와 한글 카드 뜻을 하나씩 매칭하세요! 화면 내에 쏙 들어오도록 구성되었습니다.")
        
        # 좌우 배치를 활용하여 스크롤 유발 요소를 완벽히 억제
        col_left, col_right = st.columns(2)
        
        with col_left:
            st.markdown("### 🇪🇸 스페인어")
            for word in st.session_state.left_cards:
                if word in st.session_state.matched_pairs:
                    st.button(f"✅ {word}", key=f"left_done_{word}", disabled=True, use_container_width=True)
                else:
                    is_selected = (st.session_state.selected_left == word)
                    label = f"⭐ {word}" if is_selected else word
                    if st.button(label, key=f"left_click_{word}", use_container_width=True):
                        st.session_state.selected_left = word
                        st.rerun()
                        
        with col_right:
            st.markdown("### 🇰🇷 한국어 뜻")
            for kor_text in st.session_state.right_cards:
                target_word_dict = next((w for w in st.session_state.match_words if w['Korean'].strip() == kor_text), None)
                span_origin = target_word_dict['Spanish'].strip() if target_word_dict else ""
                
                if span_origin in st.session_state.matched_pairs:
                    st.button(f"✅ {kor_text}", key=f"right_done_{kor_text}", disabled=True, use_container_width=True)
                else:
                    is_selected = (st.session_state.selected_right == kor_text)
                    label = f"⭐ {kor_text}" if is_selected else kor_text
                    if st.button(label, key=f"right_click_{kor_text}", use_container_width=True):
                        st.session_state.selected_right = kor_text
                        st.rerun()

        # 정답 대조 판정 로직
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
# 🏆 5. 랭킹보기 화면 (카테고리별 선택 조회형태로 개선!)
# ==========================================
elif st.session_state.page == "ranking":
    st.title("🏆 단어 매칭 게임 명예의 전당")
    
    if st.button("← 홈 화면으로 돌아가기"):
        st.session_state.page = "main"
        st.rerun()
    st.markdown("---")
    
    # 🌟 [요청사항 반영] 카테고리별로 선택해서 랭킹을 모아볼 수 있는 창 구축
    st.subheader("📊 카테고리 선택 필터")
    selected_rank_cat = st.selectbox("기록을 확인할 카테고리를 고르세요", match_categories)
    
    st.write(f"### 📍 '{selected_rank_cat}' 카테고리 순위 현황")
    
    rank_data = get_matching_rankings(selected_rank_cat)
    
    if rank_data:
        # 순위(1등, 2등...)를 직관적으로 추가하기 위해 DataFrame 생성
        rank_list = []
        for index, item in enumerate(rank_data):
            rank_list.append({
                "순위": f"{index + 1}등",
                "학번": item["학번"],
                "클리어 기록": f"{item['기록 (초)']}초"
            })
            
        rank_df = pd.DataFrame(rank_list)
        st.table(rank_df) # 깔끔한 표 형태로 정렬 노출
    else:
        st.info(f"아직 '{selected_rank_cat}' 카테고리에 등록된 타임어택 기록이 없습니다. 첫 기록의 주인공이 되어보세요! 🏃")
