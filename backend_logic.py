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
        # Wir definieren die Basis-URL fest auf v1beta
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"

    def analyze_receipt(self, pil_image):
        # Schritt 1: Verfügbare Modelle prüfen (um den 404 zu debuggen)
        list_url = f"{self.base_url}/models?key={self.api_key}"
        try:
            models_res = requests.get(list_url).json()
            available_models = [m["name"] for m in models_res.get("models", [])]
        except:
            available_models = []

        # Schritt 2: Wir probieren die zwei wahrscheinlichsten Pfade
        # Beachte das Präfix 'models/' - das fehlt oft und verursacht 404
        endpoints = [
            f"{self.base_url}/models/gemini-1.5-flash:generateContent?key={self.api_key}",
            f"{self.base_url}/models/gemini-pro-vision:generateContent?key={self.api_key}"
        ]
        
        buffered = BytesIO()
        pil_image.save(buffered, format="JPEG")
        img_str = base64.b64encode(buffered.getvalue()).decode()

        payload = {
            "contents": [{
                "parts": [
                    {"text": "Gib NUR JSON zurück: {\"datum\": \"YYYY-MM-DD\", \"händler\": \"Name\", \"betrag\": 0.0, \"mwst\": 8.1}"},
                    {"inline_data": {"mime_type": "image/jpeg", "data": img_str}}
                ]
            }]
        }

        last_err = "Kein Modell antwortet."
        for url in endpoints:
            try:
                response = requests.post(url, json=payload, timeout=15)
                res_json = response.json()
                
                if "candidates" in res_json:
                    text_res = res_json["candidates"][0]["content"]["parts"][0]["text"].strip()
                    if "```json" in text_res:
                        text_res = text_res.split("```json")[1].split("```")[0].strip()
                    elif "```" in text_res:
                        text_res = text_res.split("```")[1].split("```")[0].strip()
                    return json.loads(text_res)
                else:
                    last_err = res_json.get("error", {}).get("message", str(res_json))
            except Exception as e:
                last_err = str(e)
        
        # Wenn alles fehlschlägt, geben wir die Liste der verfügbaren Modelle aus!
        raise Exception(f"Modell-Fehler. Verfügbar für deinen Key: {available_models}. Fehler: {last_err}")
