import streamlit as st
import pandas as pd
from backend_logic import DataManager, PayrollEngine, AIProcessor
from datetime import datetime
import PIL.Image
import sqlite3

# Backend initialisieren
dm = DataManager()
engine = PayrollEngine()

st.set_page_config(page_title="SimpleBK - Grooming Atelier", page_icon="🐾", layout="centered")
st.title("🐾 SimpleBK: Business Cockpit")

# KI-Initialisierung via Secrets
if "GEMINI_API_KEY" in st.secrets:
    ai_proc = AIProcessor(st.secrets["GEMINI_API_KEY"])
else:
    ai_proc = None
    st.sidebar.warning("KI-Key fehlt in den Secrets.")

# Navigation
menu = st.sidebar.radio("Navigation", ["Journal", "Beleg scannen", "Lohnabrechnung", "Mitarbeiter Setup"])

# --- 1. JOURNAL ---
if menu == "Journal":
    st.header("📖 Journal 2026")
    with sqlite3.connect(dm.db_name) as conn:
        df = pd.read_sql_query("SELECT * FROM journal ORDER BY datum DESC", conn)
    if not df.empty:
        st.dataframe(df)
        ausgaben = df[df['typ'] == 'AUSGABE']['betrag_brutto'].sum()
        st.metric("Gesamtausgaben", f"{ausgaben:.2f} CHF")
    else:
        st.info("Noch keine Einträge vorhanden.")

# --- 2. BELEG SCANNEN ---
elif menu == "Beleg scannen":
    st.header("📸 Neuer Beleg-Scan")
    img_file = st.camera_input("Quittung fotografieren")
    
    # Standardwerte
    init_val = {"datum": datetime.now(), "text": "", "betrag": 0.0, "mwst": 8.1}

    if img_file and ai_proc:
        try:
            img = PIL.Image.open(img_file)
            with st.spinner("KI analysiert Beleg..."):
                res = ai_proc.analyze_receipt(img)
                init_val["datum"] = datetime.strptime(res['datum'], "%Y-%m-%d")
                init_val["text"] = res['händler']
                init_val["betrag"] = float(res['betrag'])
                init_val["mwst"] = float(res['mwst'])
                st.success("KI hat Daten erkannt!")
        except Exception as e:
            st.error(f"KI konnte Daten nicht automatisch lesen: {e}")

    with st.form("entry_form"):
        d = st.date_input("Datum", init_val["datum"])
        t = st.text_input("Händler / Grund", init_val["text"])
        b = st.number_input("Bruttobetrag (CHF)", value=init_val["betrag"], step=0.05)
        m = st.number_input("MwSt-Satz (%)", value=init_val["mwst"], step=0.1)
        kat = st.selectbox("Kategorie", ["Material", "Miete", "Lohn", "Versicherung", "Sonstiges"])
        if st.form_submit_button("Buchung speichern"):
            dm.add_entry(d.strftime("%Y-%m-%d"), kat, t, b, m, "AUSGABE")
            st.success("Gespeichert!")

# --- 3. LOHNABRECHNUNG ---
elif menu == "Lohnabrechnung":
    st.header("💰 Monatlicher Lohnlauf")
    with sqlite3.connect(dm.db_name) as conn:
        employees = pd.read_sql_query("SELECT * FROM employees", conn)
    
    if employees.empty:
        st.warning("Bitte zuerst Mitarbeiter im Setup anlegen.")
    else:
        sel_name = st.selectbox("Mitarbeiter wählen", employees['name'])
        emp = employees[employees['name'] == sel_name].iloc[0]
        res = engine.calculate(emp['brutto_basis'], emp['qst_satz'], emp['bvg_fix'])
        
        st.subheader(f"Auszahlung für {sel_name}")
        st.metric("Netto (CHF)", f"{res['netto']:.2f}")
        
        if st.button("Lohn jetzt buchen"):
            dm.add_entry(datetime.now().strftime("%Y-%m-%d"), "Lohn", f"Lohn {sel_name}", res['netto'], 0.0, "AUSGABE")
            st.success("Lohnzahlung verbucht.")

# --- 4. MITARBEITER SETUP ---
elif menu == "Mitarbeiter Setup":
    st.header("👤 Personal-Stammdaten")
    with st.form("emp_setup"):
        name = st.text_input("Name des Mitarbeiters")
        brutto = st.number_input("Bruttolohn (Basis)", value=4500.0)
        qst = st.number_input("Quellensteuer (%)", value=1.97)
        bvg = st.number_input("BVG Fixbetrag (CHF)", value=25.0)
        if st.form_submit_button("Mitarbeiter anlegen"):
            dm.add_employee(name, brutto, qst, bvg)
            st.success(f"{name} wurde angelegt.")