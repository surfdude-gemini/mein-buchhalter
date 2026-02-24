import sqlite3
import google.generativeai as genai
import json

class DataManager:
    def __init__(self, db_name="business_2026.db"):
        self.db_name = db_name
        self.init_db()

    def init_db(self):
        with sqlite3.connect(self.db_name) as conn:
            c = conn.cursor()
            # Haupt-Journal
            c.execute('''CREATE TABLE IF NOT EXISTS journal (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                datum TEXT, kategorie TEXT, text TEXT, 
                betrag_brutto REAL, mwst_satz REAL, mwst_betrag REAL, typ TEXT)''')
            # Mitarbeiter-Stammdaten
            c.execute('''CREATE TABLE IF NOT EXISTS employees (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT, brutto_basis REAL, qst_satz REAL, bvg_fix REAL)''')
            conn.commit()

    def add_employee(self, name, brutto, qst, bvg):
        with sqlite3.connect(self.db_name) as conn:
            c = conn.cursor()
            c.execute("INSERT INTO employees (name, brutto_basis, qst_satz, bvg_fix) VALUES (?, ?, ?, ?)", 
                      (name, brutto, qst, bvg))
            conn.commit()

    def add_entry(self, datum, kategorie, text, brutto, mwst_satz, typ):
        mwst_betrag = round(brutto - (brutto / (1 + mwst_satz/100)), 2)
        with sqlite3.connect(self.db_name) as conn:
            c = conn.cursor()
            c.execute("INSERT INTO journal (datum, kategorie, text, betrag_brutto, mwst_satz, mwst_betrag, typ) VALUES (?, ?, ?, ?, ?, ?, ?)",
                      (datum, kategorie, text, brutto, mwst_satz, mwst_betrag, typ))
            conn.commit()

class PayrollEngine:
    @staticmethod
    def calculate(brutto, qst_rate, bvg_fix=25.0):
        # Sätze Grooming Atelier 2026
        ahv, alv, nbu = 0.053, 0.011, 0.012
        total_sozial = ahv + alv + nbu
        abzug_sozial = brutto * total_sozial
        abzug_qst = brutto * (qst_rate / 100)
        netto = brutto - abzug_sozial - abzug_qst - bvg_fix
        return {"netto": round(netto, 2)}

class AIProcessor:
    def __init__(self, api_key):
        genai.configure(api_key=api_key)
        # Wir nutzen das robusteste Modell-Tag
        self.model = genai.GenerativeModel('gemini-1.5-flash-latest')

    def analyze_receipt(self, image_data):
        prompt = """Extrahiere aus diesem Bild: Datum (Format YYYY-MM-DD), Händlername, Bruttobetrag (Zahl) und MwSt-Satz (Zahl). 
        Antworte NUR im JSON-Format wie dieses Beispiel: {"datum": "2026-02-24", "händler": "Coop", "betrag": 45.50, "mwst": 8.1}"""
        
        response = self.model.generate_content([prompt, image_data])
        text_response = response.text.strip()
        
        # JSON-Cleanup für robuste Verarbeitung
        if "```json" in text_response:
            text_response = text_response.split("```json")[1].split("```")[0].strip()
        elif "```" in text_response:
            text_response = text_response.split("```")[1].split("```")[0].strip()
            
        return json.loads(text_response)