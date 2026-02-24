import streamlit as st
import pandas as pd
from backend_logic import DataManager, PayrollEngine, AIProcessor
from datetime import datetime
import PIL.Image
import sqlite3

# Konfiguration
st.set_page_config(page_title="SimpleBK", page_icon="🐾", layout="wide")

# CSS für großes Handy-Layout
st.markdown("""
    <style>
    div[data-testid="stCameraInput"] { width: 100% !important; }
    .stMetric { background-color: #f0f2f6; padding: 10px; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

dm = DataManager()
engine = PayrollEngine()

# API Key Check
if "GEMINI_API_KEY" in st.secrets:
    ai_proc = AIProcessor(st.secrets["GEMINI_API_KEY"])
else:
    st.error("API Key fehlt! Bitte in Streamlit Secrets hinterlegen.")

st.title("🐾 SimpleBK - Grooming Atelier")

menu = st.sidebar.radio("Menü", ["Journal", "Scanner", "Lohnabrechnung", "Personal-Setup"])

# --- SCANNER ---
if menu == "Scanner":
    st.header("📸 Beleg erfassen")
    col1, col2 = st.columns([1, 1])
    
    with col1:
        img_file = st.camera_input("Quittung fotografieren")
    
    if 'scan' not in st.session_state:
        st.session_state.scan = {"d": datetime.now(), "h": "", "b": 0.0, "m": 8.1}

    if img_file:
        try:
            img = PIL.Image.open(img_file)
            with st.spinner("KI analysiert..."):
                res = ai_proc.analyze_receipt(img)
                st.session_state.scan = {
                    "d": datetime.strptime(res['datum'], "%Y-%m-%d"),
                    "h": res['händler'],
                    "b": float(res['betrag']),
                    "m": float(res['mwst'])
                }
                st.success("Erkannt!")
        except Exception as e:
            st.error(f"Fehler: {e}")

    with col2:
        with st.form("entry_form"):
            date_val = st.date_input("Datum", st.session_state.scan["d"])
            shop_val = st.text_input("Händler", st.session_state.scan["h"])
            amt_val = st.number_input("Betrag (CHF)", value=st.session_state.scan["b"], step=0.05)
            tax_val = st.number_input("MwSt %", value=st.session_state.scan["m"], step=0.1)
            kat_val = st.selectbox("Kategorie", ["Material", "Miete", "Lohn", "Versicherung", "Sonstiges"])
            
            if st.form_submit_button("Buchen"):
                dm.add_entry(date_val.strftime("%Y-%m-%d"), kat_val, shop_val, amt_val, tax_val, "AUSGABE")
                st.success("Im Journal gespeichert!")

# --- JOURNAL ---
elif menu == "Journal":
    st.header("📖 Journal 2026")
    with sqlite3.connect(dm.db_name) as conn:
        df = pd.read_sql_query("SELECT * FROM journal ORDER BY datum DESC", conn)
    
    if not df.empty:
        st.dataframe(df, use_container_width=True)
        st.metric("Total Ausgaben", f"{df['betrag_brutto'].sum():.2f} CHF")
    else:
        st.info("Noch keine Buchungen vorhanden.")

# --- PERSONAL & LOHN ---
elif menu == "Personal-Setup":
    st.header("👤 Mitarbeiter anlegen")
    with st.form("emp_form"):
        n = st.text_input("Name")
        br = st.number_input("Bruttolohn", value=4500.0)
        qs = st.number_input("Quellensteuer %", value=1.97)
        bv = st.number_input("BVG Fix", value=25.0)
        if st.form_submit_button("Speichern"):
            dm.add_employee(n, br, qs, bv)
            st.success("Mitarbeiter gespeichert.")

elif menu == "Lohnabrechnung":
    st.header("💰 Lohnlauf")
    with sqlite3.connect(dm.db_name) as conn:
        emps = pd.read_sql_query("SELECT * FROM employees", conn)
    
    if not emps.empty:
        sel = st.selectbox("Mitarbeiter", emps['name'])
        data = emps[emps['name'] == sel].iloc[0]
        res = engine.calculate(data['brutto_basis'], data['qst_satz'], data['bvg_fix'])
        
        st.subheader(f"Auszahlung: {res['netto']} CHF")
        if st.button("Lohn jetzt buchen"):
            dm.add_entry(datetime.now().strftime("%Y-%m-%d"), "Lohn", f"Lohn {sel}", res['netto'], 0.0, "AUSGABE")
            st.success("Gebucht!")
