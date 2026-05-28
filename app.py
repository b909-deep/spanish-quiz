import streamlit as st
import pandas as pd
import random
import os

# --- 1. Streamlit 웹사이트 세션 상태(변수 기억하기) 설정 ---
if 'coin' not in st.session_state:
    st.session_state.coin = 0
if 'current_quiz' not in st.session_state:
    st.session_state.current_quiz = None
if 'quiz_finished' not in st.session_state:
    st.session_state.quiz_finished = False

st.title("🇪🇸 스페인어 복습 퀴즈 & 띠부씰")

# --- 2. 내 컴퓨터(리눅스 폴더)에서 파일 바로 읽기 ---
try:
    df = pd.read_csv('spanish.csv', encoding='utf-8')
    
    # 🌟 [요청하신 코드 위치!] 파일을 읽어온 후 바로 카테고리별로 분류합니다.
    ser_df = df[df['category']=='ser']
    estar_df = df[df['category']=='estar']
    name_df = df[df['category']=='이름 및 성']
    feeling_df = df[df['category']=='상태 및 기분']
    ing_df = df[df['category']=='현재진행형']
    per_df = df[df['category']=='성격 및 외모']
    nat_df = df[df['category']=='국적, 국적형용사']
    fam_df = df[df['category']=='가족 관계']
    bir_df = df[df['category']=='생일']
    tim_df = df[df['category']=='시간']
    day_df = df[df['category']=='요일 및 날짜']
    at_df = df[df['category']=='몇시에']
    wet_df = df[df['category']=='날씨']
    num_df = df[df['category']=='숫자']

except FileNotFoundError:
    st.error("Linux 파일 폴더에 'spanish.csv' 파일이 있는지 확인해주세요!")
    st.stop()

# 사이드바에 현재 코인 표시
st.sidebar.metric(label="🪙 내 보유 코인", value=f"{st.session_state.coin} 개")

# --- 3. 카테고리 선택 및 퀴즈 기능 ---
categories = ['ser', 'estar', '이름 및 성', '상태 및 기분', '현재진행형', '성격 및 외모', '국적, 국적형용사', '가족 관계', '생일', '시간', '요일 및 날짜', '몇시에', '날씨', '숫자']
selected_category = st.selectbox('원하는 카테고리를 골라주세요', categories)

if st.button("🚀 퀴즈 가져오기"):
    # 사용자가 선택한 글자에 따라 미리 분류해둔 데이터프레임을 selected_df에 넣어줍니다.
    if selected_category == 'ser': selected_df = ser_df
    elif selected_category == 'estar': selected_df = estar_df
    elif selected_category == '이름 및 성': selected_df = name_df
    elif selected_category == '상태 및 기분': selected_df = feeling_df
    elif selected_category == '현재진행형': selected_df = ing_df
    elif selected_category == '성격 및 외모': selected_df = per_df
    elif selected_category == '국적, 국적형용사': selected_df = nat_df
    elif selected_category == '가족 관계': selected_df = fam_df
    elif selected_category == '생일': selected_df = bir_df
    elif selected_category == '시간': selected_df = tim_df
    elif selected_category == '요일 및 날짜': selected_df = day_df
    elif selected_category == '몇시에': selected_df = at_df
    elif selected_category == '날씨': selected_df = wet_df
    elif selected_category == '숫자': selected_df = num_df

    if len(selected_df) == 0:
        st.warning("해당 카테고리에 데이터가 없습니다.")
    else:
        st.session_state.current_quiz = selected_df.sample(n=1).iloc[0].to_dict()
        st.session_state.quiz_finished = False

if st.session_state.current_quiz and not st.session_state.quiz_finished:
    quiz = st.session_state.current_quiz
    st.markdown("---")
    st.subheader(f"📝 문제를 풀어보세요!")
    
    if 'quiz' in quiz:
        st.info(f"👉 {quiz['quiz']}")
    st.write(f"💡 뜻: {quiz['korean']}")
    
    user_answer = st.text_input("정답을 입력하세요:", key="ans_input")
    
    if st.button("정답 제출 🎯"):
        is_correct = (user_answer == str(quiz['answer'])) or ('answer2' in quiz and user_answer == str(quiz['answer2']))
        if is_correct:
            st.success("Correct! 정답입니다! 🎉")
            level = quiz.get('level', '하')
            if level == '상': st.session_state.coin += 3
            elif level == '중': st.session_state.coin += 2
            else: st.session_state.coin += 1
        else:
            st.error(f"Incorrect! 정답은 [{quiz['answer']}] 입니다. 🥲")
        st.session_state.quiz_finished = True
        st.rerun()

# --- 4. 🪙 띠부씰 뽑기 상점 ---
st.markdown("---")
st.subheader("🎁 띠부씰 뽑기 상점 (10 코인 필요)")

if st.session_state.coin >= 10:
    if st.button("🎰 띠부씰 뽑기!! (10코인 차감)"):
        images = [file for file in os.listdir() if file.endswith(".png")]
        if len(images) == 0:
            st.warning("Linux 파일 폴더에 띠부씰 이미지(.png) 파일이 없습니다!")
        else:
            st.session_state.coin -= 10
            selected_img = random.choice(images)
            st.balloons()
            st.success(f"축하합니다! [ {selected_img} ] 획득!! 🥳")
            st.image(selected_img, caption=selected_img, width=200)
            with open("collection.txt", "a", encoding='utf-8') as f:
                f.write(selected_img + "\n")
            st.rerun()
else:
    st.write("퀴즈를 풀어서 10코인을 모아보세요! 💪")

# --- 5. 🖼️ 내 컬렉션북 보기 ---
st.markdown("---")
st.subheader("📖 나의 띠부씰 컬렉션북")

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
    st.write("아직 도감이 비어있습니다.")