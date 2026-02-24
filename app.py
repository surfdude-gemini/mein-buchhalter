import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
from backend_logic import DataManager, PayrollEngine, AIProcessor
from PIL import Image
import io

# --- INITIALISIERUNG ---
dm = DataManager()
engine = PayrollEngine()

# Überprüfen, ob der API Key vorhanden ist
if "GEMINI_API_KEY" in st.secrets:
    ai_processor = AIProcessor(st.secrets["GEMINI_API_KEY"])
else:
    st.warning("Bitte hinterlege den GEMINI_API_KEY in den Streamlit Secrets.")
    ai_processor = None

# --- APP LAYOUT ---
st.set_page_config(page_title="SimpleBK - Grooming Atelier", page_icon="🐾", layout="centered")

# Custom CSS für ein schöneres Interface
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; background-color: #4CAF50; color: white; }
    </style>
    """, unsafe_allow_html=True)

st.title("🐾 SimpleBK: Business Cockpit")
st.subheader("Grooming Atelier - Finanzen & Lohn")

# --- NAVIGATION ---
menu = st.sidebar.radio("Menü", ["Dashboard", "Beleg scannen", "Mitarbeiter verwalten", "Lohnabrechnung", "Journal"])

# --- 1. DASHBOARD ---
if menu == "Dashboard":
    st.header("📊 Statistik 2026")
    with sqlite3.connect(dm.db_name) as conn:
        df = pd.read_sql_query("SELECT * FROM journal", conn)
    
    if not df.empty:
        col1, col2, col3 = st.columns(3)
        ausgaben = df[df['typ'] == 'AUSGABE']['betrag_brutto'].sum()
        einnahmen = df[df['typ'] == 'EINNAHME']['betrag_brutto'].sum()
        mwst = df['mwst_betrag'].sum()
        
        col1.metric("Einnahmen", f"{einnahmen:,.2f} CHF")
        col2.metric("Ausgaben", f"{ausgaben:,.2f} CHF")
        col3.metric("MwSt-Saldo", f"{mwst:,.2f} CHF")
        
        st.bar_chart(df.groupby('kategorie')['betrag_brutto'].sum())
    else:
        st.info("Noch keine Daten für 2026 vorhanden.")

# --- 2. BELEG SCANNEN (MIT KI) ---
elif menu == "Beleg scannen":
    st.header("📸 KI-Beleg-Scanner")
    
    img_file = st.camera_input("Quittung fotografieren")
    
    # Session State für KI-Ergebnisse initialisieren
    if 'ai_data' not in st.session_state:
        st.session_state.ai_data = {"datum": datetime.now(), "händler": "", "betrag": 0.0, "mwst": 8.1}

    if img_file and ai_processor:
        with st.spinner("Gemini analysiert den Beleg..."):
            try:
                # Bild für KI vorbereiten
                img_bytes = img_file.getvalue()
                result = ai_processor.analyze_receipt({"mime_type": "image/jpeg", "data": img_bytes})
                
                # Daten im Session State speichern
                st.session_state.ai_data = {
                    "datum": datetime.strptime(result['datum'], "%Y-%m-%d"),
                    "händler": result['händler'],
                    "betrag": float(result['betrag']),
                    "mwst": float(result['mwst'])
                }
                st.success("KI-Analyse erfolgreich!")
            except Exception as e:
                st.error(f"KI-Fehler: {e}")

    # Erfassungsformular (wird durch KI vorausgefüllt)
    with st.form("entry_form"):
        f_datum = st.date_input("Datum", st.session_state.ai_data["datum"])
        f_text = st.text_input("Händler / Beschreibung", st.session_state.ai_data["händler"])
        f_betrag = st.number_input("Betrag Brutto (CHF)", value=st.session_state.ai_data["betrag"], step=0.05)
        f_mwst = st.selectbox("MwSt-Satz (%)", [8.1, 2.6, 7.7, 2.5, 0.0], index=0)
        f_kat = st.selectbox("Kategorie", ["Material", "Miete", "Lohn", "Versicherung", "Marketing", "Einnahmen"])
        f_typ = st.radio("Typ", ["AUSGABE", "EINNAHME"], horizontal=True)
        
        if st.form_submit_button("In Journal speichern"):
            dm.add_entry(f_datum.strftime("%Y-%m-%d"), f_kat, f_text, f_betrag, f_mwst, f_typ)
            st.success("Buchung gespeichert!")
            st.balloons()

# --- 3. MITARBEITER VERWALTEN ---
elif menu == "Mitarbeiter verwalten":
    st.header("👤 Personal-Stammdaten")
    with st.form("emp_form"):
        name = st.text_input("Name des Mitarbeiters")
        brutto = st.number_input("Basis Bruttolohn (CHF)", min_value=0.0)
        qst = st.number_input("Quellensteuer-Satz (%)", value=1.97, step=0.01)
        bvg = st.number_input("BVG Fixabzug (CHF)", value=25.0)
        if st.form_submit_button("Mitarbeiter anlegen"):
            dm.add_employee(name, brutto, qst, bvg)
            st.success(f"{name} wurde im System registriert.")

# --- 4. LOHNABRECHNUNG ---
elif menu == "Lohnabrechnung":
    st.header("💰 Lohnlauf 2026")
    with sqlite3.connect(dm.db_name) as conn:
        employees = pd.read_sql_query("SELECT * FROM employees", conn)
    
    if not employees.empty:
        sel_emp = st.selectbox("Mitarbeiter wählen", employees['name'])
        emp_row = employees[employees['name'] == sel_emp].iloc[0]
        
        # Berechnung
        res = engine.calculate(emp_row['brutto_basis'], emp_row['qst_satz'], emp_row['bvg_fix'])
        
        st.info(f"Berechnung für {sel_emp} (Monat: {datetime.now().strftime('%B')})")
        st.write(f"**Netto-Auszahlung: {res['netto']:.2f} CHF**")
        
        if st.button("Lohn jetzt buchen"):
            dm.add_entry(datetime.now().strftime("%Y-%m-%d"), "Lohn", f"Lohnzahlung {sel_emp}", res['netto'], 0.0, "AUSGABE")
            st.success("Lohn wurde im Journal als Ausgabe erfasst.")
    else:
        st.warning("Noch kein Personal angelegt.")

# --- 5. JOURNAL ---
elif menu == "Journal":
    st.header("📖 Journal 2026")
    with sqlite3.connect(dm.db_name) as conn:
        df = pd.read_sql_query("SELECT * FROM journal ORDER BY datum DESC", conn)
    st.dataframe(df, use_container_width=True)