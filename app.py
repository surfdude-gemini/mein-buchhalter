import streamlit as st
import pandas as pd
from backend_logic import DataManager, PayrollEngine, AIProcessor
from datetime import datetime
import PIL.Image
import sqlite3

st.set_page_config(page_title="SimpleBK", page_icon="🐾", layout="wide")

# CSS für besseres Handy-Feeling
st.markdown("""
    <style>
    [data-testid="stCameraInput"] { width: 100% !important; }
    .stButton>button { width: 100%; height: 3.5em; font-size: 1.1em; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

dm = DataManager()
engine = PayrollEngine()

# API-Key aus Streamlit Secrets
if "GEMINI_API_KEY" in st.secrets:
    ai_proc = AIProcessor(st.secrets["GEMINI_API_KEY"])
else:
    st.error("Bitte 'GEMINI_API_KEY' in den Streamlit Secrets hinterlegen!")

st.title("🐾 SimpleBK - Grooming Atelier")

menu = st.sidebar.radio("Navigation", ["Beleg-Scanner", "Journal", "Lohnabrechnung"])

if menu == "Beleg-Scanner":
    st.header("📸 Quittung scannen")
    img_file = st.camera_input("Beleg fotografieren")
    
    # Session State zur Zwischenspeicherung der erkannten Daten
    if 'scan_data' not in st.session_state:
        st.session_state.scan_data = {"d": datetime.now(), "h": "", "b": 0.0, "m": 8.1}

    if img_file:
        try:
            img = PIL.Image.open(img_file)
            with st.spinner("KI liest Beleg..."):
                res = ai_proc.analyze_receipt(img)
                st.session_state.scan_data = {
                    "d": datetime.strptime(res['datum'], "%Y-%m-%d"),
                    "h": res['händler'],
                    "b": float(res['betrag']),
                    "m": float(res['mwst'])
                }
                st.success("KI-Analyse erfolgreich!")
        except Exception as e:
            st.error(f"Scan-Fehler: {e}")

    with st.form("input_form"):
        col1, col2 = st.columns(2)
        with col1:
            final_date = st.date_input("Datum", st.session_state.scan_data["d"])
            final_shop = st.text_input("Händler", st.session_state.scan_data["h"])
        with col2:
            final_amt = st.number_input("Betrag (CHF)", value=st.session_state.scan_data["b"], step=0.05)
            final_tax = st.number_input("MwSt %", value=st.session_state.scan_data["m"], step=0.1)
        
        if st.form_submit_button("✅ Buchung speichern"):
            dm.add_entry(final_date.strftime("%Y-%m-%d"), "Ausgabe", final_shop, final_amt, final_tax, "AUSGABE")
            st.balloons()
            st.success("Erfolgreich im Journal gespeichert!")

elif menu == "Journal":
    st.header("📖 Journal 2026")
    with sqlite3.connect(dm.db_name) as conn:
        df = pd.read_sql_query("SELECT * FROM journal ORDER BY datum DESC", conn)
    
    if not df.empty:
        st.dataframe(df, use_container_width=True)
        st.metric("Total Ausgaben", f"{df['betrag_brutto'].sum():.2f} CHF")
    else:
        st.info("Noch keine Einträge vorhanden.")
