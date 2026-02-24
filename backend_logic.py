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
            c.execute('''CREATE TABLE IF NOT EXISTS journal (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                datum TEXT, kategorie TEXT, text TEXT, 
                betrag_brutto REAL, mwst_satz REAL, mwst_betrag REAL, typ TEXT)''')
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
        ahv, alv, nbu = 0.053, 0.011, 0.012
        total_sozial = ahv + alv + nbu
        abzug_sozial = brutto * total_sozial
        abzug_qst = brutto * (qst_rate / 100)
        netto = brutto - abzug_sozial - abzug_qst - bvg_fix
        return {"netto": round(netto, 2)}

class AIProcessor:
    def __init__(self, api_key):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')

    def analyze_receipt(self, image_data):
        prompt = "Extrahiere Datum (YYYY-MM-DD), Händler, Bruttobetrag (Zahl) und MwSt-Satz (Zahl). Gib NUR JSON zurück: {\"datum\": \"...\", \"händler\": \"...\", \"betrag\": 0.0, \"mwst\": 0.0}"
        response = self.model.generate_content([prompt, image_data])
        clean_json = response.text.replace("```json", "").replace("```", "").strip()
        return json.loads(clean_json)