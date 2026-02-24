import streamlit as st
import pandas as pd
from backend_logic import DataManager, PayrollEngine
from datetime import datetime

# Backend initialisieren
dm = DataManager()
engine = PayrollEngine()

st.set_page_config(page_title="SimpleBK - Erfassung", page_icon="🐾")
st.title("🐾 SimpleBK: Datenerfassung")

# Navigation in der Seitenleiste
menu = st.sidebar.radio("Navigation", ["Mitarbeiter anlegen", "Belege erfassen", "Lohn abrechnen", "Journal"])

# --- 1. MITARBEITER ANLEGEN ---
if menu == "Mitarbeiter anlegen":
    st.header("👤 Personal-Stammdaten")
    st.write("Hier legst du die Basiswerte für deine Mitarbeiter fest.")
    
    with st.form("employee_form"):
        name = st.text_input("Vollständiger Name")
        brutto = st.number_input("Monatlicher Bruttolohn (CHF)", min_value=0.0, step=100.0)
        qst = st.number_input("Quellensteuer-Satz (%)", min_value=0.0, max_value=20.0, value=1.97, step=0.01)
        bvg = st.number_input("BVG Fixbetrag (CHF)", min_value=0.0, value=25.0)
        
        submit = st.form_submit_button("Mitarbeiter speichern")
        
        if submit and name:
            dm.add_employee(name, brutto, qst, bvg)
            st.success(f"Mitarbeiter {name} wurde erfolgreich angelegt!")

# --- 2. BELEGE ERFASSEN (Kamera & Manuel) ---
elif menu == "Belege erfassen":
    st.header("📸 Ausgaben & Belege")
    
    # Kamera-Input
    img_file = st.camera_input("Beleg fotografieren")
    
    with st.form("entry_form"):
        datum = st.date_input("Datum", datetime.now())
        text = st.text_input("Beschreibung (Händler / Grund)")
        betrag = st.number_input("Bruttobetrag (CHF)", min_value=0.0, step=0.05)
        mwst = st.selectbox("MwSt-Satz (%)", [7.7, 8.1, 2.5, 2.6, 0.0]) # Aktuelle Schweizer Sätze
        kat = st.selectbox("Kategorie", ["Material", "Miete", "Versicherung", "Marketing", "Sonstiges"])
        
        save_btn = st.form_submit_button("Buchung speichern")
        
        if save_btn and text:
            dm.add_entry(datum.strftime("%Y-%m-%d"), kat, text, betrag, mwst, "AUSGABE")
            st.success("Buchung erfolgreich im Journal gespeichert!")

# --- 3. LOHN ABRECHNEN ---
elif menu == "Lohn abrechnen":
    st.header("💰 Monatlicher Lohnlauf")
    
    # Mitarbeiter aus DB laden
    import sqlite3
    conn = sqlite3.connect(dm.db_name)
    employees = pd.read_sql_query("SELECT * FROM employees", conn)
    conn.close()
    
    if employees.empty:
        st.warning("Bitte lege zuerst unter 'Mitarbeiter anlegen' Personal an.")
    else:
        selected_name = st.selectbox("Mitarbeiter wählen", employees['name'])
        emp_data = employees[employees['name'] == selected_name].iloc[0]
        
        # Berechnung via Backend Engine
        result = engine.calculate(emp_data['brutto_basis'], emp_data['qst_satz'], emp_data['bvg_fix'])
        
        st.subheader(f"Abrechnung für {selected_name}")
        st.metric("Netto-Auszahlung", f"{result['netto']} CHF")
        
        if st.button("Diesen Lohn jetzt buchen"):
            dm.add_entry(datetime.now().strftime("%Y-%m-%d"), "Personal", f"Lohn {selected_name}", result['netto'], 0.0, "AUSGABE")
            st.success(f"Lohnzahlung für {selected_name} im Journal erfasst.")

# --- 4. JOURNAL ---
elif menu == "Journal":
    st.header("📖 Journal 2026")
    import sqlite3
    conn = sqlite3.connect(dm.db_name)
    df = pd.read_sql_query("SELECT * FROM journal ORDER BY datum DESC", conn)
    conn.close()
    
    if not df.empty:
        st.dataframe(df)
        total = df[df['typ'] == 'AUSGABE']['betrag_brutto'].sum()
        st.info(f"Gesamtausgaben aktuell: {total:.2f} CHF")
    else:
        st.write("Noch keine Einträge vorhanden.")