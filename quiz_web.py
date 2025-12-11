import streamlit as st
import json
import random
import os
import re

# --- Configuration ---
st.set_page_config(page_title="PIPE Elements Reviewer", layout="centered")


# --- 1. Load Data (Cached for performance) ---
@st.cache_data
def load_data():
    # Look for file in the same directory
    file_path = os.path.join(os.path.dirname(__file__), "questions.json")
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return []
    except json.JSONDecodeError:
        st.error("Error: questions.json is corrupted.")
        return []


# --- 2. Initialize Session State ---
# This keeps track of data across button clicks (like pages in an app)
if 'quiz_data' not in st.session_state:
    st.session_state.quiz_data = []
if 'score' not in st.session_state:
    st.session_state.score = 0
if 'current_index' not in st.session_state:
    st.session_state.current_index = 0
if 'wrong_answers' not in st.session_state:
    st.session_state.wrong_answers = []
if 'screen' not in st.session_state:
    st.session_state.screen = "home"
if 'shuffled_options' not in st.session_state:
    st.session_state.shuffled_options = []


# --- Helper: Sort Chapters ---
def get_sorted_chapters(data):
    unique_chapters = set(q.get("chapter", "General") for q in data)
    try:
        # Sort numerically if possible
        return sorted(unique_chapters,
                      key=lambda x: int(re.search(r'\d+', str(x)).group()) if re.search(r'\d+', str(x)) else str(x))
    except:
        return sorted(list(unique_chapters), key=str)


# --- SCREEN 1: HOME (Selection) ---
def show_home(all_data):
    st.title("PIPE Elements Exam")
    st.write("### Select Chapter/s To Take (60 items)")

    # Chapter Dictionary for pretty names
    chapter_titles = {
        "1": "THERMODYNAMICS", "2": "FUELS & COMBUSTION", "3": "DIESEL POWER PLANT",
        "4": "GAS TURBINE", "5": "STEAM POWER PLANT", "6": "GEOTHERMAL & NON CONVENTIONAL",
        "7": "NUCLEAR POWER PLANT", "8": "BOILERS", "9": "HYDROELECTRIC POWER PLANT",
        "10": "VARIABLE LOAD & ENVIRONMENTAL", "11": "FLUID MECHANICS", "12": "FLUID MACHINERIES",
        "13": "HEAT TRANSFER", "14": "REFRIGERATION", "15": "AIR CONDITIONING",
        "16": "MACHINE FOUNDATION", "17": "INSTRUMENTATION", "18": "BASIC EE",
        "19": "LATEST BOARD QUESTIONS"
    }

    # Get available chapters
    chapters = get_sorted_chapters(all_data)

    # Format options for the multiselect
    options_map = {}
    for ch in chapters:
        num = str(ch)
        name = chapter_titles.get(num, "")
        label = f"CHAPTER {num}: {name}" if name else f"Chapter {num}"
        options_map[label] = ch

    # Multiselect widget
    selected_labels = st.multiselect("Choose Topics:", list(options_map.keys()))

    # Select All Button helper
    if st.button("Select All Chapters"):
        selected_labels = list(options_map.keys())

    if st.button("START EXAM", type="primary"):
        if not selected_labels:
            st.warning("Please select at least one chapter.")
        else:
            # Filter Logic
            selected_ids = [options_map[label] for label in selected_labels]
            full_pool = [q for q in all_data if q.get("chapter", "General") in selected_ids]

            # Shuffle and Limit
            random.shuffle(full_pool)
            st.session_state.quiz_data = full_pool[:60]

            # Reset State
            st.session_state.score = 0
            st.session_state.current_index = 0
            st.session_state.wrong_answers = []
            st.session_state.screen = "quiz"
            st.session_state.shuffled_options = []  # Reset options buffer
            st.rerun()


# --- SCREEN 2: QUIZ ---
def show_quiz():
    q_index = st.session_state.current_index
    total = len(st.session_state.quiz_data)

    # Progress Bar
    progress = (q_index / total)
    st.progress(progress)
    st.caption(f"Question {q_index + 1} of {total}")

    # Get current question
    question_data = st.session_state.quiz_data[q_index]

    # Logic to shuffle options ONLY ONCE per question
    # We store the shuffled list in session_state so it doesn't reshuffle when you click buttons
    if not st.session_state.shuffled_options:
        opts = question_data["options"].copy()
        random.shuffle(opts)
        st.session_state.shuffled_options = opts

    st.subheader(question_data["question"])

    # Radio Button for Answer
    # We use a unique key based on index to reset selection for next question
    user_choice = st.radio("Choose your answer:", st.session_state.shuffled_options, index=None, key=f"q_{q_index}")

    if st.button("Next Question", type="primary"):
        if not user_choice:
            st.warning("Please select an answer.")
        else:
            # Check Answer
            correct = question_data["answer"]
            if user_choice.strip().lower() == correct.strip().lower():
                st.session_state.score += 1
            else:
                st.session_state.wrong_answers.append({
                    "question": question_data["question"],
                    "selected": user_choice,
                    "correct": correct
                })

            # Advance
            st.session_state.current_index += 1
            st.session_state.shuffled_options = []  # Clear options so next question shuffles new ones

            # Check if finished
            if st.session_state.current_index >= total:
                st.session_state.screen = "results"

            st.rerun()


# --- SCREEN 3: RESULTS ---
def show_results():
    total = len(st.session_state.quiz_data)
    score = st.session_state.score
    percent = (score / total) * 100

    st.title("Exam Results")
    st.markdown(f"### Final Score: {score} / {total} ({percent:.2f}%)")

    if score == total:
        st.success("Perfect Score! You got everything right!")
    else:
        st.write("---")
        st.subheader("Review of Incorrect Answers")

        for i, item in enumerate(st.session_state.wrong_answers, 1):
            with st.container():
                st.markdown(f"**{i}. {item['question']}**")
                # Red for wrong, Green for correct using Streamlit markdown color syntax
                st.markdown(f":red[**Your Answer:** {item['selected']}]")
                st.markdown(f":green[**Correct Answer:** {item['correct']}]")
                st.divider()

    if st.button("Take Another Quiz"):
        st.session_state.screen = "home"
        st.rerun()


# --- MAIN APP LOGIC ---
data = load_data()

if st.session_state.screen == "home":
    show_home(data)
elif st.session_state.screen == "quiz":
    show_quiz()
elif st.session_state.screen == "results":
    show_results()