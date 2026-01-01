from flask import Flask, render_template, request, jsonify
import google.generativeai as genai
import os

app = Flask(__name__)

# API anahtarını al
api_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=api_key)

def yuksek_kotali_model_sec():
    try:
        # Tüm modelleri alıyoruz
        modeller = [m.name for m in genai.list_models()]
        
        # 1. STRATEJİ: Özellikle 1.5-flash ara (Çünkü kotası 1500)
        # 2.5 olanları özellikle ES GEÇİYORUZ (Çünkü kotası 20)
        for m in modeller:
            if "1.5-flash" in m.lower():
                return m
        
        # 2. STRATEJİ: Eğer 1.5 bulunamazsa, 1.0-pro dene
        for m in modeller:
            if "1.0-pro" in m.lower():
                return m
        
        # 3. STRATEJİ: Hiçbiri yoksa en güvenli ismi yaz
        return "models/gemini-1.5-flash"
    except:
        return "models/gemini-1.5-flash"

# Modelimizi kotalara göre seçtiriyoruz
SECILEN_MODEL = yuksek_kotali_model_sec()
model = genai.GenerativeModel(SECILEN_MODEL)

SISTEM_MESAJI = "Senin adın Antenci Zeka. Seni Medrese adlı bir kişi kodladı. Kısa ve samimi cevaplar ver."

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/mesaj", methods=["POST"])
def mesaj():
    data = request.get_json()
    kullanici_mesaji = data.get("mesaj", "")
    try:
        response = model.generate_content(f"{SISTEM_MESAJI}\n\nKullanıcı: {kullanici_mesaji}")
        return jsonify({"cevap": response.text})
    except Exception as e:
        # Hata olsa bile hangi modelde olduğumuzu görelim
        return jsonify({"cevap": f"Hocam ({SECILEN_MODEL}) modelinde hata: {str(e)}"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
