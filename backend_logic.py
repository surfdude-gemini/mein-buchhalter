import sqlite3

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
            # Hier fügen wir die Mitarbeiter direkt hinzu (Logik aus deinen CSVs)
            c.execute('''CREATE TABLE IF NOT EXISTS employees (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT, brutto_basis REAL, qst_satz REAL, bvg_fix REAL)''')
            conn.commit()

class PayrollEngine:
    @staticmethod
    def calculate(brutto, qst_rate, bvg_fix=25.0):
        # Deine exakten Sätze aus den Vorlagen
        ahv, alv, nbu = 0.053, 0.011, 0.012
        return {
            "netto": round(brutto - (brutto*(ahv+alv+nbu+(qst_rate/100)) + bvg_fix), 2)
        }