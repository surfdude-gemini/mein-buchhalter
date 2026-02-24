import streamlit as st
import pandas as pd
from backend_logic import DataManager, PayrollEngine, AIProcessor
from datetime import datetime
import PIL.Image
import sqlite3

st.set_page_config(page_title="SimpleBK", page_icon="🐾", layout="wide")

# CSS für großes Handy-Layout
st.markdown("""
    <style>
    div[data-testid="stCameraInput"] { width: 100% !important; }
    .stButton>button { width: 100%; height: 3.5em; border-radius: 12px; font-weight: bold; background-color: #ff4b4b; color: white; }
    </style>
    """, unsafe_allow_html=True)

dm = DataManager()
engine = PayrollEngine()

if "GEMINI_API_KEY" in st.secrets:
    ai_proc = AIProcessor(st.secrets["GEMINI_API_KEY"])
else:
    st.error("API Key fehlt in Secrets!")

st.title("🐾 SimpleBK")

menu = st.sidebar.radio("Navigation", ["Scanner", "Journal", "Lohn"])

if menu == "Scanner":
    st.header("📸 Beleg scannen")
    img_file = st.camera_input("Foto aufnehmen")
    
    if 'scan_data' not in st.session_state:
        st.session_state.scan_data = {"d": datetime.now(), "h": "", "b": 0.0, "m": 8.1}

    if img_file:
        try:
            img = PIL.Image.open(img_file)
            with st.spinner("KI liest..."):
                res = ai_proc.analyze_receipt(img)
                st.session_state.scan_data = {
                    "d": datetime.strptime(res['datum'], "%Y-%m-%d"),
                    "h": res['händler'],
                    "b": float(res['betrag']),
                    "m": float(res['mwst'])
                }
                st.success("Daten erkannt!")
        except Exception as e:
            st.error(f"Scan-Fehler: {e}")

    with st.form("entry_form"):
        col1, col2 = st.columns(2)
        with col1:
            d = st.date_input("Datum", st.session_state.scan_data["d"])
            h = st.text_input("Händler", st.session_state.scan_data["h"])
        with col2:
            b = st.number_input("Betrag (CHF)", value=st.session_state.scan_data["b"])
            m = st.number_input("MwSt %", value=st.session_state.scan_data["m"])
        
        if st.form_submit_button("Speichern"):
            dm.add_entry(d.strftime("%Y-%m-%d"), "Ausgabe", h, b, m, "AUSGABE")
            st.success("Gebucht!")

elif menu == "Journal":
    st.header("📖 Journal 2026")
    with sqlite3.connect(dm.db_name) as conn:
        df = pd.read_sql_query("SELECT * FROM journal ORDER BY datum DESC", conn)
    st.dataframe(df, use_container_width=True)
