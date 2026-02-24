class AIProcessor:
    def __init__(self, api_key):
        genai.configure(api_key=api_key)
        # Wir definieren eine Liste von Modellen, die wir durchprobieren
        self.model_names = ['gemini-1.5-flash', 'gemini-1.5-flash-latest', 'gemini-pro-vision']
        self.model = None

    def analyze_receipt(self, pil_image):
        prompt = """Extrahiere: datum (YYYY-MM-DD), händler, betrag (Zahl), mwst (Zahl). 
        Antworte NUR als JSON: {"datum": "2026-02-24", "händler": "Shop", "betrag": 10.50, "mwst": 8.1}"""
        
        last_error = None
        for name in self.model_names:
            try:
                model = genai.GenerativeModel(name)
                # Der entscheidende Fix: Wir senden das PIL Image direkt
                response = model.generate_content([prompt, pil_image])
                
                text_response = response.text.strip()
                if "```json" in text_response:
                    text_response = text_response.split("```json")[1].split("```")[0].strip()
                elif "```" in text_response:
                    text_response = text_response.split("```")[1].split("```")[0].strip()
                
                return json.loads(text_response)
            except Exception as e:
                last_error = e
                continue # Probiere das nächste Modell in der Liste
        
        raise Exception(f"Alle KI-Modelle fehlgeschlagen. Letzter Fehler: {str(last_error)}")
