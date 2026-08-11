import streamlit as st
import requests
import json
import base64
import plotly.express as px
import pandas as pd
from websockets.sync.client import connect

import os

API_URL = os.environ.get("API_URL") or (st.secrets.get("API_URL") if "API_URL" in getattr(st, "secrets", {}) else "http://127.0.0.1:8000")
API_URL = API_URL.rstrip("/")

if API_URL.startswith("https://"):
    WS_URL = API_URL.replace("https://", "wss://")
elif API_URL.startswith("http://"):
    WS_URL = API_URL.replace("http://", "ws://")
else:
    WS_URL = "ws://127.0.0.1:8000"

st.set_page_config(page_title="AI Interview Coach", layout="wide")

def start_interview():
    response = requests.post(
        f"{API_URL}/session/start",
        json={
            "jd": st.session_state.jd,
            "resume_text": st.session_state.resume,
            "interview_mode": st.session_state.get("interview_mode", "Full Mock Interview (Mixed)"),
            "num_questions": 4 # Shortened for testing
        }
    )
    if response.status_code != 200:
        st.error(f"Failed to start session: {response.text}")
        return
        
    data = response.json()
    st.session_state.session_id = data["session_id"]
    st.session_state.current_question = data["first_question"]
    st.session_state.question_audio = data.get("question_audio")
    st.session_state.interview_started = True
    st.session_state.transcript_history = []
    st.session_state.interview_ended = False

def render_dashboard(session_id):
    st.header("Interview Complete! Here's your feedback:")
    response = requests.get(f"{API_URL}/session/{session_id}/summary")
    data = response.json()
    scores = data.get("scores", [])
    
    if not scores:
        st.info("No evaluation scores recorded yet. Answer at least 1 question during the interview to generate your performance radar chart and review.")
        return
        
    radar_data = []
    for s in scores:
        category = s["question"]["category"]
        for ds in s["evaluation"]["scores"]:
            radar_data.append({
                "Category": category,
                "Dimension": ds["dimension"],
                "Score": ds["score"]
            })
            
    df = pd.DataFrame(radar_data)
    if not df.empty:
        df_avg = df.groupby(["Category", "Dimension"]).mean().reset_index()
        fig = px.line_polar(df_avg, r="Score", theta="Dimension", color="Category", line_close=True,
                            range_r=[0, 5], title="Performance by Category and Dimension")
        fig.update_traces(fill='toself')
        st.plotly_chart(fig)
        
    st.subheader("Detailed Review")
    for idx, s in enumerate(scores):
        with st.expander(f"Q{idx+1}: {s['question']['question']}"):
            st.write("**Category:**", s["question"]["category"])
            st.write("**Feedback:**", s["review"])
            for ds in s["evaluation"]["scores"]:
                st.write(f"- **{ds['dimension']} ({ds['score']}/5):** {ds['justification']}")

if "interview_started" not in st.session_state:
    st.session_state.interview_started = False

if "resume" not in st.session_state:
    st.session_state.resume = ""

if not st.session_state.interview_started:
    st.title("AI Interview Coach")
    st.write("Welcome! Enter the Job Description and your Resume below to start.")
    st.session_state.jd = st.text_area("Job Description", height=200)
    
    st.session_state.interview_mode = st.selectbox(
        "🎯 Select Interview Mode",
        [
            "Full Mock Interview (Mixed)",
            "Coding & Technical Deep-Dive",
            "Behavioral (STAR Method Focus)",
            "System Design & Architecture"
        ],
        help="Choose the focus area for your interview session."
    )
    
    # Resume file uploader
    uploaded_file = st.file_uploader("Upload Resume (PDF, TXT, or MD)", type=["pdf", "txt", "md"])
    if uploaded_file is not None:
        try:
            file_key = f"processed_{uploaded_file.name}_{uploaded_file.size}"
            if file_key not in st.session_state:
                if uploaded_file.name.endswith(".pdf"):
                    import pypdf
                    reader = pypdf.PdfReader(uploaded_file)
                    text_parts = []
                    for page in reader.pages:
                        text_parts.append(page.extract_text() or "")
                    parsed_text = "\n".join(text_parts)
                else:
                    parsed_text = uploaded_file.read().decode("utf-8")
                
                st.session_state.resume = parsed_text
                st.session_state[file_key] = True
                st.success(f"Successfully uploaded and parsed: {uploaded_file.name}")
        except Exception as e:
            st.error(f"Error parsing resume file: {e}")
            
    st.session_state.resume = st.text_area("Resume", value=st.session_state.resume, height=200)
    
    col_btn1, col_btn2 = st.columns([1, 1])
    
    with col_btn1:
        analyze_clicked = st.button("🔍 Analyze Resume vs JD Match", use_container_width=True)
    with col_btn2:
        start_clicked = st.button("🚀 Start Interview", type="primary", use_container_width=True)
        
    if analyze_clicked:
        if st.session_state.jd and st.session_state.resume:
            with st.spinner("Analyzing Resume vs. Job Description..."):
                try:
                    res = requests.post(
                        f"{API_URL}/analyze/resume-match",
                        json={"jd": st.session_state.jd, "resume_text": st.session_state.resume}
                    )
                    if res.status_code == 200:
                        st.session_state.match_analysis = res.json()
                    else:
                        st.error(f"Analysis failed: {res.text}")
                except Exception as e:
                    st.error(f"Error connecting to backend: {e}")
        else:
            st.warning("Please enter both Job Description and Resume to analyze.")
            
    if "match_analysis" in st.session_state and st.session_state.match_analysis:
        analysis = st.session_state.match_analysis
        pct = analysis.get("match_percentage", 0)
        
        st.divider()
        st.subheader("🎯 Resume-to-JD Match Analysis")
        
        m_col1, m_col2 = st.columns([1, 3])
        with m_col1:
            st.metric(label="Match Score", value=f"{pct}%")
            if pct >= 75:
                st.success("High Compatibility")
            elif pct >= 50:
                st.warning("Moderate Compatibility")
            else:
                st.error("Low Compatibility")
        with m_col2:
            st.progress(pct / 100)
            
        g_col1, g_col2 = st.columns(2)
        with g_col1:
            st.markdown("##### ✅ Matching Skills Found")
            for skill in analysis.get("matching_skills", []):
                st.markdown(f"- **{skill}**")
        with g_col2:
            st.markdown("##### ⚠️ Missing Skills & Gaps")
            for skill in analysis.get("missing_skills", []):
                st.markdown(f"- 🔴 **{skill}**")
                
        st.markdown("##### 💡 Key Focus Recommendations for the Interview")
        for rec in analysis.get("recommendations", []):
            st.info(f"👉 {rec}")
        st.divider()
        
    if start_clicked:
        if st.session_state.jd and st.session_state.resume:
            with st.spinner("Starting session..."):
                start_interview()
            st.rerun()
        else:
            st.error("Please provide both JD and Resume.")
else:
    if st.session_state.get("interview_ended"):
        render_dashboard(st.session_state.session_id)
        if st.button("Start New Interview"):
            st.session_state.interview_started = False
            st.rerun()
    else:
        header_col1, header_col2 = st.columns([3, 1])
        with header_col1:
            st.title("Live Interview")
        with header_col2:
            st.write("") # Alignment spacing
            if st.button("⏹️ End Interview Early", type="secondary"):
                st.session_state.interview_ended = True
                st.rerun()
                
        # Sidebar control
        with st.sidebar:
            st.header("Session Controls")
            if st.button("End Interview & View Dashboard", use_container_width=True):
                st.session_state.interview_ended = True
                st.rerun()
        
        # Display transcript history
        for msg in st.session_state.transcript_history:
            st.chat_message(msg["role"]).write(msg["content"])
            
        # Display current question only if interview is ongoing
        st.chat_message("assistant").write(st.session_state.current_question["question"])
        
        # Play spoken question audio if available (Voice Synthesis)
        if "question_audio" in st.session_state and st.session_state.question_audio:
            q_bytes = base64.b64decode(st.session_state.question_audio)
            st.audio(q_bytes, format="audio/mp3", autoplay=True)
            st.session_state.question_audio = None
            
        # Play feedback audio if available
        if "feedback_audio" in st.session_state and st.session_state.feedback_audio:
            audio_bytes = base64.b64decode(st.session_state.feedback_audio)
            st.audio(audio_bytes, format="audio/mp3", autoplay=True)
            st.session_state.feedback_audio = None
            
        col1, col2 = st.columns([1, 1])
        
        with col1:
            audio_key = f"audio_{len(st.session_state.transcript_history)}"
            audio_val = st.audio_input("Record your answer", key=audio_key)
            
        with col2:
            text_val = st.chat_input("Type your answer here...")
            
        submitted_answer = None
        is_audio = False
        
        if audio_val:
            audio_bytes = audio_val.read()
            submitted_answer = base64.b64encode(audio_bytes).decode('utf-8')
            is_audio = True
        elif text_val:
            submitted_answer = text_val
            is_audio = False
            
        if submitted_answer:
            with st.spinner("Evaluating answer..."):
                response = None
                user_display = "(Audio Answer Recorded)" if is_audio else submitted_answer
                message = {
                    "type": "answer_audio" if is_audio else "answer_text",
                    "audio_data": submitted_answer if is_audio else None,
                    "transcript": submitted_answer if not is_audio else None
                }
                
                # 1. Primary: Try WebSocket
                try:
                    with connect(f"{WS_URL}/session/{st.session_state.session_id}/answer", timeout=10) as websocket:
                        websocket.send(json.dumps(message))
                        response_str = websocket.recv()
                        response = json.loads(response_str)
                except Exception as ws_err:
                    # 2. Fallback: HTTP POST
                    try:
                        res = requests.post(
                            f"{API_URL}/session/{st.session_state.session_id}/answer",
                            json=message,
                            timeout=30
                        )
                        if res.status_code == 200:
                            response = res.json()
                        else:
                            st.error(f"Server Error: {res.text}")
                    except Exception as http_err:
                        st.error(f"Failed to submit answer: {http_err}")
                
                if response:
                    # Add question and answer to transcript history
                    st.session_state.transcript_history.append({"role": "assistant", "content": st.session_state.current_question["question"]})
                    st.session_state.transcript_history.append({"role": "user", "content": user_display})
                    
                    if response.get("feedback_live"):
                        st.session_state.transcript_history.append({"role": "assistant", "content": f"💡 **Feedback:** {response['feedback_live']}"})
                    
                    if response.get("feedback_audio"):
                        st.session_state.feedback_audio = response["feedback_audio"]
                        
                    if response.get("type") == "end_interview":
                        st.session_state.interview_ended = True
                    else:
                        st.session_state.current_question = response["next_question"]
                        if response.get("question_audio"):
                            st.session_state.question_audio = response["question_audio"]
                            
                st.rerun()

