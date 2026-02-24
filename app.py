from backend_logic import DataManager, PayrollEngine

import streamlit as st
import pandas as pd
import sqlite3

# Datenbank initialisieren
conn = sqlite3.connect('business.db', check_same_thread=False)
c = conn.cursor()
c.execute('CREATE TABLE IF NOT EXISTS journal (datum TEXT, text TEXT, betrag REAL, typ TEXT)')
conn.commit()

st.set_page_config(page_title="SimpleBK", page_icon="🐾")
st.title("SimpleBK - Grooming Atelier")

menu = st.sidebar.selectbox("Navigation", ["Dashboard", "Kamera-Scan", "Lohnabrechnung"])

if menu == "Kamera-Scan":
    st.header("📸 Beleg scannen")
    img = st.camera_input("Foto machen")
    if img:
        st.success("Bild empfangen! KI Analyse startet...")
        # Hier kommt der Gemini-API Teil rein

elif menu == "Lohnabrechnung":
    st.header("💰 Lohn-Master 2026")
    name = st.text_input("Mitarbeiter Name", "Bernadett Schweitzer")
    brutto = st.number_input("Bruttolohn (CHF)", value=4500.0)
    
    # Die Logik aus deinem Mindmap/Excel
    ahv = brutto * 0.053
    alv = brutto * 0.011
    nbu = brutto * 0.012
    qst = brutto * 0.0197
    bvg = 25.0  # Fixbetrag
    
    netto = brutto - (ahv + alv + nbu + qst + bvg)
    
    st.metric("Auszahlung Netto", f"{netto:.2f} CHF")
    
    if st.button("Lohn buchen"):
        c.execute("INSERT INTO journal VALUES (?,?,?,?)", 
                  (pd.Timestamp.now().strftime("%Y-%m-%d"), f"Lohn {name}", -netto, "Lohn"))
        conn.commit()
        st.success("Gebucht!")

elif menu == "Dashboard":
    st.header("📊 Jahres-Statistik")
    data = pd.read_sql_query("SELECT * FROM journal", conn)
    st.dataframe(data)