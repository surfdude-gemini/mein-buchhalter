import streamlit as st
import pandas as pd
from backend_logic import DataManager, PayrollEngine, AIProcessor
from datetime import datetime
import PIL.Image
import sqlite3

# Wide-Layout für mobile Nutzung
st.set_page_config(page_title="SimpleBK", page_icon="🐾", layout="wide")

# CSS für großes Kamera-Fenster
st.markdown("""
    <style>
    div[data-testid="stCameraInput"] { width: 100% !important; }
    .stButton>button { width: 100%; height: 3.5em; font-size: 1.2rem; border-radius: 12px; background-color: #ff4b4b; color: white; }
    </style>
    """, unsafe_allow_html=True)

dm = DataManager()
engine = PayrollEngine()

# API Key sicher laden
if "GEMINI_API_KEY" in st.secrets:
    ai_proc = AIProcessor(st.secrets["GEMINI_API_KEY"])
else:
    st.error("API Key fehlt! Bitte in den Streamlit Settings unter 'Secrets' hinzufügen.")

st.title("🐾 SimpleBK - Grooming Atelier")

menu = st.sidebar.radio("Navigation", ["Scanner", "Journal", "Lohn"])

if menu == "Scanner":
    st.header("📸 Beleg erfassen")
    img_file = st.camera_input("Foto aufnehmen")
    
    # Session State zur Datenspeicherung
    if 'data' not in st.session_state:
        st.session_state.data = {"d": datetime.now(), "h": "", "b": 0.0, "m": 8.1}

    if img_file:
        try:
            img = PIL.Image.open(img_file)
            with st.spinner("KI liest Beleg..."):
                res = ai_proc.analyze_receipt(img)
                st.session_state.data = {
                    "d": datetime.strptime(res['datum'], "%Y-%m-%d"),
                    "h": res['händler'],
                    "b": float(res['betrag']),
                    "m": float(res['mwst'])
                }
                st.success("Erkannt!")
        except Exception as e:
            st.error(f"Scan-Fehler: {e}")

    with st.form("entry_form"):
        col1, col2 = st.columns(2)
        with col1:
            d = st.date_input("Datum", st.session_state.data["d"])
            h = st.text_input("Händler", st.session_state.data["h"])
        with col2:
            b = st.number_input("Betrag (CHF)", value=st.session_state.data["b"], step=0.05)
            m = st.number_input("MwSt %", value=st.session_state.data["m"], step=0.1)
        
        if st.form_submit_button("Buchung speichern"):
            dm.add_entry(d.strftime("%Y-%m-%d"), "Ausgabe", h, b, m, "AUSGABE")
            st.balloons()
            st.success("Gespeichert!")

elif menu == "Journal":
    st.header("📖 Journal 2026")
    with sqlite3.connect(dm.db_name) as conn:
        df = pd.read_sql_query("SELECT * FROM journal ORDER BY datum DESC", conn)
    st.dataframe(df, use_container_width=True)
