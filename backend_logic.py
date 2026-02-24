import sqlite3
from datetime import datetime

class DataManager:
    def __init__(self, db_name="business_2026.db"):
        self.db_name = db_name
        self.init_db()

    def init_db(self):
        with sqlite3.connect(self.db_name) as conn:
            c = conn.cursor()
            # Haupt-Journal für Einnahmen/Ausgaben
            c.execute('''CREATE TABLE IF NOT EXISTS journal (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                datum TEXT, kategorie TEXT, text TEXT, 
                betrag_brutto REAL, mwst_satz REAL, mwst_betrag REAL, typ TEXT)''')
            
            # Stammdaten Mitarbeiter (Wichtig für deine Erfassung)
            c.execute('''CREATE TABLE IF NOT EXISTS employees (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT, brutto_basis REAL, qst_satz REAL, bvg_fix REAL)''')
            conn.commit()

    # Funktion um einen neuen Mitarbeiter anzulegen
    def add_employee(self, name, brutto, qst, bvg):
        with sqlite3.connect(self.db_name) as conn:
            c = conn.cursor()
            c.execute("INSERT INTO employees (name, brutto_basis, qst_satz, bvg_fix) VALUES (?, ?, ?, ?)", 
                      (name, brutto, qst, bvg))
            conn.commit()

    # Funktion um eine Buchung zu speichern
    def add_entry(self, datum, kategorie, text, brutto, mwst_satz, typ):
        mwst_betrag = round(brutto - (brutto / (1 + mwst_satz/100)), 2)
        with sqlite3.connect(self.db_name) as conn:
            c = conn.cursor()
            c.execute("INSERT INTO journal (datum, kategorie, text, betrag_brutto, mwst_satz, mwst_betrag, typ) VALUES (?, ?, ?, ?, ?, ?, ?)",
                      (datum, kategorie, text, brutto, mwst_satz, mwst_betrag, typ))
import google.generativeai as genai
import json

class AIProcessor:
    def __init__(self, api_key):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')

    def analyze_receipt(self, image_data):
        prompt = """
        Analysiere dieses Quittungsbild und extrahiere:
        1. Datum (Format YYYY-MM-DD)
        2. Händlername
        3. Bruttobetrag (Zahl)
        4. MwSt-Satz (Zahl, z.B. 8.1 oder 2.6)
        Gib das Ergebnis NUR als valides JSON zurück, z.B.:
        {"datum": "2026-02-24", "händler": "MediaMarkt", "betrag": 119.00, "mwst": 8.1}
        """
        response = self.model.generate_content([prompt, image_data])
        # Extrahiere JSON aus der Antwort (entferne Markdown-Formatierung falls vorhanden)
        clean_json = response.text.replace("```json", "").replace("```", "").strip()
        return json.loads(clean_json)
            conn.commit()