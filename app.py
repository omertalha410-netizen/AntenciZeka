from flask import Flask, render_template, request, jsonify
import google.generativeai as genai
import os

app = Flask(__name__)

# API anahtarını al
api_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=api_key)

def kotasiz_model_bul():
    try:
        # Google'ın senin için izin verdiği TÜM modelleri al
        modeller = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        
        # HOCAM BURASI ÇOK KRİTİK:
        # Eğer listede 2.5-flash varsa onu LİSTEDEN KOVUYORUZ (Kotası 20 olduğu için)
        temiz_liste = [m for m in modeller if "2.5" not in m]
        
        # Şimdi elimizde kalan (muhtemelen 1.5-flash veya 1.0-pro) modellerden ilkini seç
        if temiz_liste:
            print(f"Hocam bulduğum güvenli model: {temiz_liste[0]}")
            return temiz_liste[0]
        
        return modeller[0] # Eğer hiç temiz model yoksa mecburen ilkini al
    except Exception as e:
        return "models/gemini-1.5-flash"

# Filtrelenmiş, güvenli modeli başlat
SECILEN_ID = kotasiz_model_bul()
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
        response = model.generate_content(f"{SISTEM_MESAJI}\n\nKullanıcı: {kullanici_mesaji}")
        return jsonify({"cevap": response.text})
    except Exception as e:
        return jsonify({"cevap": f"Hocam şu modelde ({SECILEN_ID}) bir takılma oldu: {str(e)}"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
