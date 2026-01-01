from flask import Flask, render_template, request, jsonify
import google.generativeai as genai
import os

app = Flask(__name__)

# API anahtarını al
api_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=api_key)

def kesin_calisan_modeli_getir():
    try:
        # Google'ın senin için tanımladığı tüm modelleri tara
        for m in genai.list_models():
            # generateContent destekleyen ve kotalı olmayan (1.5 flash) önceliğimiz
            if 'generateContent' in m.supported_generation_methods:
                if "1.5-flash" in m.name:
                    return m.name # Tam ismi (models/gemini-1.5-flash vb.) döndürür
        
        # Eğer yukarıdaki bulunamazsa, çalışan ilk modeli döndür
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                return m.name
    except:
        pass
    return "models/gemini-pro" # En son çare

# Modeli tam ismiyle (ID) başlatıyoruz
SECILEN_ID = kesin_calisan_modeli_getir()
model = genai.GenerativeModel(model_name=SECILEN_ID)

SISTEM_MESAJI = "Senin adın Antenci Zeka. Seni Medrese adlı bir kişi kodladı."

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/mesaj", methods=["POST"])
def mesaj():
    data = request.get_json()
    kullanici_mesaji = data.get("mesaj", "")
    try:
        # response = model.generate_content(...) yerine en temel haliyle çağırıyoruz
        response = model.generate_content(f"{SISTEM_MESAJI}\n\nKullanıcı: {kullanici_mesaji}")
        return jsonify({"cevap": response.text})
    except Exception as e:
        return jsonify({"cevap": f"Hocam denenen ID ({SECILEN_ID}) hatası: {str(e)}"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
