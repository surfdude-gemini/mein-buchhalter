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

    def add_entry(self, datum, kategorie, text, brutto, mwst_satz, typ):
        mwst_betrag = round(brutto - (brutto / (1 + mwst_satz/100)), 2)
        with sqlite3.connect(self.db_name) as conn:
            c = conn.cursor()
            c.execute("INSERT INTO journal (datum, kategorie, text, betrag_brutto, mwst_satz, mwst_betrag, typ) VALUES (?, ?, ?, ?, ?, ?, ?)",
                      (datum, kategorie, text, brutto, mwst_satz, mwst_betrag, typ))
            conn.commit()

class AIProcessor:
    def __init__(self, api_key):
        genai.configure(api_key=api_key)
        # Wir nutzen 'gemini-1.5-flash', da es am schnellsten für Belege ist
        self.model = genai.GenerativeModel('gemini-1.5-flash')

    def analyze_receipt(self, image_data):
        prompt = """Extrahiere aus diesem Bild: Datum (YYYY-MM-DD), Händlername, Bruttobetrag (Zahl) und MwSt-Satz (Zahl). 
        Antworte NUR im JSON-Format wie dieses Beispiel: {"datum": "2026-02-24", "händler": "Beispiel Shop", "betrag": 45.50, "mwst": 8.1}"""
        
        # Sicherstellen, dass das Bild korrekt übergeben wird
        response = self.model.generate_content([prompt, image_data])
        
        # JSON-Bereinigung (entfernt eventuelle Markdown-Tags der KI)
        text_response = response.text.strip()
        if text_response.startswith("```json"):
            text_response = text_response.split("```json")[1].split("```")[0].strip()
        elif text_response.startswith("```"):
            text_response = text_response.split("```")[1].split("```")[0].strip()
            
        return json.loads(text_response)