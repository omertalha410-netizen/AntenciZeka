from flask import Flask, render_template, request, jsonify
import google.generativeai as genai
import os

app = Flask(__name__)

# API anahtarını al
api_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=api_key)

# HOCAM: Senin listeden seçtiğimiz, kotası en geniş olan model budur.
# 404 hatası almamak için listedeki tam ismini kullanıyoruz.
SECILEN_MODEL = "models/gemini-2.5-flash-lite" 

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
        # Mesajı gönderiyoruz
        response = model.generate_content(f"{SISTEM_MESAJI}\n\nKullanıcı: {kullanici_mesaji}")
        return jsonify({"cevap": response.text})
    except Exception as e:
        # Eğer bu modelde de bir sorun olursa listedeki diğerine (2.0-flash-lite) geçer
        try:
            yedek_model = genai.GenerativeModel("models/gemini-2.0-flash-lite")
            response = yedek_model.generate_content(f"{SISTEM_MESAJI}\n\nKullanıcı: {kullanici_mesaji}")
            return jsonify({"cevap": response.text})
        except:
            return jsonify({"cevap": f"Hocam bir sorun çıktı, ama çözüyoruz! Hata: {str(e)}"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
