from flask import Flask, render_template, request, jsonify
import google.generativeai as genai
import os

app = Flask(__name__)

# API anahtarını al
api_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=api_key)

def calisan_modeli_bul():
    """Sistemin izin verdiği ilk çalışan modeli bulur."""
    try:
        for m in genai.list_models():
            # Sadece içerik üretebilen modelleri filtrele
            if 'generateContent' in m.supported_generation_methods:
                # 2026'da en güncel olanları tercih et (Gemini 3 veya Gemini 1.5)
                if "flash" in m.name.lower() or "pro" in m.name.lower():
                    return m.name
        return "models/gemini-1.5-flash" # Hiçbir şey bulunamazsa varsayılan
    except Exception:
        return "models/gemini-1.5-flash"

# Otomatik model seçimi yapılıyor
SECILEN_MODEL = calisan_modeli_bul()
model = genai.GenerativeModel(SECILEN_MODEL)

SISTEM_MESAJI = (
    "Senin adın Antenci Zeka. Seni Medrese adlı bir kişi kodladı. "
    "Medrese zeki, dindar ve vizyon sahibidir. "
    "Ders sorularında samimi ol, cevapları kısa tut."
)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/mesaj", methods=["POST"])
def mesaj():
    data = request.get_json()
    kullanici_mesaji = data.get("mesaj", "")
    try:
        prompt = f"{SISTEM_MESAJI}\n\nKullanıcı: {kullanici_mesaji}"
        response = model.generate_content(prompt)
        return jsonify({"cevap": response.text})
    except Exception as e:
        # Hata devam ederse hangi modeli denediğimizi de görelim
        return jsonify({"cevap": f"Hocam denenen model ({SECILEN_MODEL}) hatası: {str(e)}"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
