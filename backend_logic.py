import sqlite3
import json
import requests
import base64
from io import BytesIO

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
        self.api_key = api_key
        # WIR NUTZEN JETZT GEMINI-PRO-VISION (STABILER FÜR DIREKTE HTTP CALLS)
        self.url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro-vision:generateContent?key={self.api_key}"

    def analyze_receipt(self, pil_image):
        # Bild in Base64 umwandeln
        buffered = BytesIO()
        pil_image.save(buffered, format="JPEG")
        img_str = base64.b64encode(buffered.getvalue()).decode()

        payload = {
            "contents": [{
                "parts": [
                    {"text": "Analysiere diese Quittung. Extrahiere Datum (YYYY-MM-DD), Händlername, Bruttobetrag (Zahl) und MwSt-Satz (Zahl). Gib NUR JSON zurück: {\"datum\": \"2026-02-24\", \"händler\": \"Coop\", \"betrag\": 15.50, \"mwst\": 8.1}"},
                    {"inline_data": {"mime_type": "image/jpeg", "data": img_str}}
                ]
            }]
        }

        response = requests.post(self.url, json=payload)
        res_json = response.json()

        # Fehlerbehandlung für die API Antwort
        if "candidates" in res_json:
            text_res = res_json["candidates"][0]["content"]["parts"][0]["text"].strip()
            # JSON-Säuberung (KI schreibt manchmal Markdown-Code-Blocks)
            if "```json" in text_res:
                text_res = text_res.split("```json")[1].split("```")[0].strip()
            elif "```" in text_res:
                text_res = text_res.split("```")[1].split("```")[0].strip()
            return json.loads(text_res)
        else:
            # Wenn es immer noch ein 404 ist, geben wir eine klare Meldung aus
            error_msg = res_json.get("error", {}).get("message", "Unbekannter API Fehler")
            raise Exception(f"Google API sagt: {error_msg}")
