class AIProcessor:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"

    def analyze_receipt(self, pil_image):
        # Wir nutzen das Modell, das laut deiner Liste garantiert existiert
        model_name = "models/gemini-2.0-flash" 
        url = f"{self.base_url}/{model_name}:generateContent?key={self.api_key}"
        
        buffered = BytesIO()
        pil_image.save(buffered, format="JPEG")
        img_str = base64.b64encode(buffered.getvalue()).decode()

        payload = {
            "contents": [{
                "parts": [
                    {"text": "Analysiere diese Quittung. Gib NUR JSON zurück: {\"datum\": \"YYYY-MM-DD\", \"händler\": \"Name\", \"betrag\": 0.0, \"mwst\": 8.1}"},
                    {"inline_data": {"mime_type": "image/jpeg", "data": img_str}}
                ]
            }]
        }

        try:
            response = requests.post(url, json=payload, timeout=15)
            res_json = response.json()
            
            if "candidates" in res_json:
                text_res = res_json["candidates"][0]["content"]["parts"][0]["text"].strip()
                # JSON-Säuberung (Markdown entfernen)
                if "```json" in text_res:
                    text_res = text_res.split("```json")[1].split("```")[0].strip()
                elif "```" in text_res:
                    text_res = text_res.split("```")[1].split("```")[0].strip()
                return json.loads(text_res)
            else:
                msg = res_json.get("error", {}).get("message", "Unbekannter Fehler")
                raise Exception(f"API Fehler: {msg}")
        except Exception as e:
            raise Exception(f"KI Fehler mit {model_name}: {str(e)}")
