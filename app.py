import streamlit as st
import pandas as pd
from backend_logic import DataManager, AIProcessor
from datetime import datetime
import PIL.Image

# Wide Mode für besseres Handy-Layout
st.set_page_config(page_title="SimpleBK", page_icon="🐾", layout="wide")

# CSS für größeres Kamera-Fenster
st.markdown("""
    <style>
    div[data-testid="stCameraInput"] > label { font-size: 20px; font-weight: bold; }
    div[data-testid="stCameraInput"] { width: 100% !important; max-width: 800px !important; }
    </style>
    """, unsafe_allow_html=True)

dm = DataManager()

if "GEMINI_API_KEY" in st.secrets:
    ai_proc = AIProcessor(st.secrets["GEMINI_API_KEY"])
else:
    st.error("API Key fehlt in den Streamlit Secrets!")

st.title("🐾 SimpleBK Scan")

menu = st.sidebar.radio("Navigation", ["Beleg scannen", "Journal"])

if menu == "Beleg scannen":
    # Zwei Spalten: Links die Kamera, rechts die Daten
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("1. Foto machen")
        img_file = st.camera_input("Quittung erfassen")
    
    # Session State zur Speicherung der KI-Ergebnisse
    if 'receipt_data' not in st.session_state:
        st.session_state.receipt_data = {"datum": datetime.now(), "händler": "", "betrag": 0.0, "mwst": 8.1}

    if img_file:
        try:
            img = PIL.Image.open(img_file)
            with st.spinner("KI liest Beleg..."):
                res = ai_proc.analyze_receipt(img)
                st.session_state.receipt_data = {
                    "datum": datetime.strptime(res['datum'], "%Y-%m-%d"),
                    "händler": res['händler'],
                    "betrag": float(res['betrag']),
                    "mwst": float(res['mwst'])
                }
                st.success("Daten erkannt!")
        except Exception as e:
            st.error(f"Scan-Fehler: {e}")

    with col2:
        st.subheader("2. Daten prüfen & speichern")
        with st.form("entry_form"):
            d = st.date_input("Datum", st.session_state.receipt_data["datum"])
            t = st.text_input("Händler / Beschreibung", st.session_state.receipt_data["händler"])
            b = st.number_input("Betrag (CHF)", value=st.session_state.receipt_data["betrag"], step=0.05)
            m = st.number_input("MwSt-Satz (%)", value=st.session_state.receipt_data["mwst"], step=0.1)
            
            if st.form_submit_button("In Journal buchen"):
                dm.add_entry(d.strftime("%Y-%m-%d"), "Ausgabe", t, b, m, "AUSGABE")
                st.balloons()
                st.success("Erfolgreich gebucht!")