from flask import Flask, render_template, request, jsonify
import google.generativeai as genai
import os

app = Flask(__name__)

# API anahtarını al
api_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=api_key)

def yuksek_kotalı_model_bul():
    try:
        modeller = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        
        # 1. ÖNCELİK: 1500 mesaj kotalı 1.5-flash modelleri
        for m in modeller:
            if "1.5-flash" in m:
                return m
        
        # 2. ÖNCELİK: Eğer o yoksa 1.0-pro (Eski ama sağlam kota)
        for m in modeller:
            if "pro" in m and "1.0" in m:
                return m
                
        # 3. ÖNCELİK: Liste boş değilse ilk bulduğun çalışan modeli al
        if modeller:
            return modeller[0]
            
        return "models/gemini-1.5-flash"
    except:
        return "models/gemini-1.5-flash"

# Yüksek kotalı olanı seçiyoruz
SECILEN_MODEL = yuksek_kotalı_model_bul()
model = genai.GenerativeModel(SECILEN_MODEL)

SISTEM_MESAJI = "Senin adın Antenci Zeka. Seni Medrese adlı bir kişi kodladı."

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
        return jsonify({"cevap": f"Hocam şu modelde ({SECILEN_MODEL}) kota/hata sorunu var: {str(e)}"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
