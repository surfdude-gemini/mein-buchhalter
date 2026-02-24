import streamlit as st
import pandas as pd
from backend_logic import DataManager, PayrollEngine, AIProcessor
from datetime import datetime
import PIL.Image

dm = DataManager()
engine = PayrollEngine()

st.set_page_config(page_title="SimpleBK", page_icon="🐾")

# KI-Initialisierung (falls Key vorhanden)
if "GEMINI_API_KEY" in st.secrets:
    ai_proc = AIProcessor(st.secrets["GEMINI_API_KEY"])
else:
    st.warning("Kein API Key in Secrets gefunden. KI-Scan deaktiviert.")

menu = st.sidebar.radio("Navigation", ["Journal", "Beleg scannen", "Lohnabrechnung", "Mitarbeiter Setup"])

if menu == "Beleg scannen":
    st.header("📸 Neuer Scan")
    img_file = st.camera_input("Quittung fotografieren")
    
    # Standardwerte für das Formular
    init_values = {"datum": datetime.now(), "text": "", "betrag": 0.0, "mwst": 8.1}

    if img_file:
        try:
            img = PIL.Image.open(img_file)
            with st.spinner("KI liest Beleg..."):
                res = ai_proc.analyze_receipt(img)
                init_values["datum"] = datetime.strptime(res['datum'], "%Y-%m-%d")
                init_values["text"] = res['händler']
                init_values["betrag"] = float(res['betrag'])
                init_values["mwst"] = float(res['mwst'])
                st.success("Daten erkannt!")
        except Exception as e:
            st.error(f"KI-Fehler: {e}")

    with st.form("entry_form"):
        d = st.date_input("Datum", init_values["datum"])
        t = st.text_input("Händler / Grund", init_values["text"])
        b = st.number_input("Betrag (CHF)", value=init_values["betrag"])
        m = st.number_input("MwSt-Satz (%)", value=init_values["mwst"])
        if st.form_submit_button("Speichern"):
            dm.add_entry(d.strftime("%Y-%m-%d"), "Ausgabe", t, b, m, "AUSGABE")
            st.success("Gespeichert!")

elif menu == "Journal":
    st.header("📖 Journal 2026")
    import sqlite3
    with sqlite3.connect(dm.db_name) as conn:
        df = pd.read_sql_query("SELECT * FROM journal ORDER BY datum DESC", conn)
    st.dataframe(df)

# (Lohn- und Setup-Menüs hier wie gehabt ergänzen...)