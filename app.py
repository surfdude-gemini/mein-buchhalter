import streamlit as st
import pandas as pd
from backend_logic import DataManager, AIProcessor
from datetime import datetime
import PIL.Image
import sqlite3

st.set_page_config(page_title="SimpleBK", page_icon="🐾", layout="wide")

# CSS für mobile Nutzung
st.markdown("""
    <style>
    [data-testid="stCameraInput"] { width: 100% !important; }
    .stButton>button { width: 100%; height: 3.5em; border-radius: 12px; font-weight: bold; background-color: #ff4b4b; color: white; }
    </style>
    """, unsafe_allow_html=True)

dm = DataManager()

if "GEMINI_API_KEY" in st.secrets:
    ai_proc = AIProcessor(st.secrets["GEMINI_API_KEY"])
else:
    st.error("API Key fehlt in Secrets!")

st.title("🐾 SimpleBK")

menu = st.sidebar.radio("Navigation", ["Scanner", "Journal"])

if menu == "Scanner":
    st.header("📸 Beleg scannen")
    img_file = st.camera_input("Foto aufnehmen")
    
    if 'scan_data' not in st.session_state:
        st.session_state.scan_data = {"d": datetime.now(), "h": "", "b": 0.0, "m": 8.1}

    if img_file:
        try:
            img = PIL.Image.open(img_file)
            with st.spinner("KI liest mit Gemini 2.0..."):
                res = ai_proc.analyze_receipt(img)
                st.session_state.scan_data = {
                    "d": datetime.strptime(res['datum'], "%Y-%m-%d"),
                    "h": res['händler'],
                    "b": float(res['betrag']),
                    "m": float(res['mwst'])
                }
                st.success("Erkannt!")
        except Exception as e:
            st.error(f"Scan-Fehler: {e}")

    with st.form("entry_form"):
        d = st.date_input("Datum", st.session_state.scan_data["d"])
        h = st.text_input("Händler", st.session_state.scan_data["h"])
        b = st.number_input("Betrag (CHF)", value=st.session_state.scan_data["b"])
        m = st.number_input("MwSt %", value=st.session_state.scan_data["m"])
        
        if st.form_submit_button("Speichern"):
            dm.add_entry(d.strftime("%Y-%m-%d"), "Ausgabe", h, b, m, "AUSGABE")
            st.success("Buchung gespeichert!")

elif menu == "Journal":
    st.header("📖 Journal 2026")
    with sqlite3.connect(dm.db_name) as conn:
        df = pd.read_sql_query("SELECT * FROM journal ORDER BY datum DESC", conn)
    st.dataframe(df, use_container_width=True)
