import sqlite3
import google.generativeai as genai
import json
from datetime import datetime

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
        # Wir versuchen es direkt mit dem stabilen Flash-Modell
        self.model = genai.GenerativeModel('gemini-1.5-flash')

    def analyze_receipt(self, pil_image):
        prompt = """Analysiere dieses Bild einer Quittung. 
        Extrahiere die Daten und gib sie NUR als JSON zurück:
        {"datum": "YYYY-MM-DD", "händler": "Name", "betrag": 0.0, "mwst": 8.1}
        Wichtig: Wenn du den MwSt-Satz nicht sicher weißt, nimm 8.1."""
        
        try:
            # Bild direkt übergeben
            response = self.model.generate_content([prompt, pil_image])
            res_text = response.text.strip()
            
            # JSON-Bereinigung falls die KI Markdown-Codeblöcke nutzt
            if "```json" in res_text:
                res_text = res_text.split("```json")[1].split("```")[0].strip()
            elif "```" in res_text:
                res_text = res_text.split("```")[1].split("```")[0].strip()
            
            return json.loads(res_text)
        except Exception as e:
            raise Exception(f"KI-Fehler Details: {str(e)}")

class PayrollEngine:
    @staticmethod
    def calculate(brutto, qst_rate, bvg_fix=25.0):
        ahv, alv, nbu = 0.053, 0.011, 0.012
        netto = brutto - (brutto * (ahv + alv + nbu + (qst_rate / 100))) - bvg_fix
        return {"netto": round(netto, 2)}
