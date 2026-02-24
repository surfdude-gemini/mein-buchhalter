import streamlit as st
import pandas as pd
from datetime import datetime

# --- KONFIGURATION & STYLES ---
st.set_page_config(page_title="SimpleBK - Grooming Atelier", layout="centered")
st.title("🐾 SimpleBK - Business Cockpit")

# --- NAVIGATION ---
menu = st.sidebar.selectbox("Menü", ["Dashboard", "Beleg scannen", "Lohnabrechnung", "Jahresjournal"])

# --- MODUL 1: BELEG SCANNEN (Kamera) ---
if menu == "Beleg scannen":
    st.header("📸 Beleg-Erfassung")
    img_file = st.camera_input("Quittung fotografieren")
    
    if img_file:
        st.image(img_file, caption="Scan läuft...", width=300)
        # Hier wird später der Gemini-API-Call eingefügt
        st.info("System-Aktion: Bild wird an KI gesendet & Daten extrahiert...")
        
        # Dummy-Ergebnis zur Visualisierung
        st.success("Erkannt: 24.02.2026 | MediaMarkt | 119.00 CHF | 19% MwSt")
        if st.button("In Journal speichern"):
            st.write("Eintrag wurde in der Datenbank (2026) abgelegt.")

# --- MODUL 2: LOHNABRECHNUNG (Deine Excel-Logik) ---
elif menu == "Lohnabrechnung":
    st.header("工资 Lohn-Master")
    mitarbeiter = st.selectbox("Mitarbeiter wählen", ["Bernadett Schweitzer", "Weitere..."])
    brutto = st.number_input("Bruttolohn (CHF)", value=4500.00)
    
    # System-Aktion: Mathematische Berechnung (Deine Werte!)
    ahv = brutto * 0.053    # 5.3%
    alv = brutto * 0.011    # 1.1%
    nbu = brutto * 0.012    # 1.2%
    bvg = 25.00             # Fixbetrag aus deiner Vorlage
    qst = brutto * 0.0197   # 1.97% Quellensteuer
    
    netto = brutto - (ahv + alv + nbu + bvg + qst)
    
    st.subheader(f"Abrechnung für {mitarbeiter}")
    col1, col2 = st.columns(2)
    with col1:
        st.write(f"AHV/IV/EO (5.3%):")
        st.write(f"ALV (1.1%):")
        st.write(f"Quellensteuer (1.97%):")
    with col2:
        st.write(f"- {ahv:.2f} CHF")
        st.write(f"- {alv:.2f} CHF")
        st.write(f"- {qst:.2f} CHF")
    
    st.metric("Auszahlungsbetrag (Netto)", f"{netto:.2f} CHF")
    
    if st.button("Lohnabrechnung PDF & Buchen"):
        st.write("PDF wird generiert und als Ausgabe im Journal erfasst.")

# --- MODUL 3: DASHBOARD ---
elif menu == "Dashboard":
    st.header("📊 Statistik 2026")
    col1, col2, col3 = st.columns(3)
    col1.metric("Einnahmen", "12'450 CHF", "+5%")
    col2.metric("Ausgaben", "8'120 CHF", "-2%")
    col3.metric("MwSt-Saldo", "1'240 CHF")
    
    st.bar_chart({"Einnahmen": [4000, 5000, 4500], "Ausgaben": [3000, 3200, 3100]})