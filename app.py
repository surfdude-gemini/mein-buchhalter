import streamlit as st
import sqlite3
import pandas as pd
import os

# --- DATENBANK FUNKTIONEN ---
DB_FILE = "buchhaltung_2026.db"

def init_db():
    # Erstellt die Datei automatisch, falls sie nicht existiert
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    # Tabelle für Ausgaben/Einnahmen
    c.execute('''CREATE TABLE IF NOT EXISTS journal 
                 (id INTEGER PRIMARY KEY, datum TEXT, typ TEXT, text TEXT, 
                  betrag REAL, mwst_satz REAL, mwst_betrag REAL, kategorie TEXT)''')
    conn.commit()
    conn.close()

# Datenbank beim Start initialisieren
init_db()

# --- APP LAYOUT ---
st.set_page_config(page_title="SimpleBK - Grooming Atelier", layout="centered")
st.title("🐾 SimpleBK - Business Cockpit")

menu = st.sidebar.selectbox("Menü", ["Dashboard", "Beleg scannen", "Lohnabrechnung", "Jahresjournal"])

if menu == "Beleg scannen":
    st.header("📸 Beleg-Erfassung")
    img_file = st.camera_input("Quittung fotografieren")
    
    if img_file:
        st.info("System-Aktion: Bild erkannt. KI-Analyse wird vorbereitet...")
        # Hier ergänzen wir später den API-Key für Gemini
        
elif menu == "Jahresjournal":
    st.header("📖 Journal 2026")
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT * FROM journal", conn)
    st.dataframe(df)
    conn.close()