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
        # Wir setzen die Konfiguration global
        genai.configure(api_key=api_key)
        # Wir nutzen den stabilsten Modell-Namen ohne Pfad-Präfix
        self.model = genai.GenerativeModel('gemini-1.5-flash')

    def analyze_receipt(self, pil_image):
        # Präziser Prompt für strukturiertes JSON
        prompt = """Analysiere dieses Bild. Extrahiere:
        - datum: YYYY-MM-DD
        - händler: Name des Shops
        - betrag: Gesamtsumme (Zahl)
        - mwst: MwSt-Satz (Zahl)
        Gib NUR JSON zurück: {"datum": "...", "händler": "...", "betrag": 0.0, "mwst": 0.0}"""
        
        try:
            # Wir nutzen die generate_content Methode mit dem Bildobjekt
            response = self.model.generate_content([prompt, pil_image])
            
            # JSON-Extraktion (falls die KI Markdown ```json ... ``` mitsendet)
            res_text = response.text.strip()
            if "```json" in res_text:
                res_text = res_text.split("```json")[1].split("```")[0].strip()
            elif "```" in res_text:
                res_text = res_text.split("```")[1].split("```")[0].strip()
                
            return json.loads(res_text)
        except Exception as e:
            # Wir geben den Fehler detailliert aus, um ihn zu verstehen
            raise Exception(f"KI konnte Bild nicht verarbeiten: {str(e)}")
