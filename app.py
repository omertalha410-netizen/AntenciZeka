from flask import Flask, render_template, request, jsonify
import google.generativeai as genai
import os

app = Flask(__name__)

# API Anahtarını al ve yapılandır
api_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=api_key)

# Model ismini TAM YOL olarak veriyoruz (En güvenli yol budur)
model = genai.GenerativeModel('models/gemini-1.5-flash')

SISTEM_MESAJI = "Senin adın Antenci Zeka. Seni Medrese adlı bir kişi kodladı."

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/mesaj", methods=["POST"])
def mesaj():
    data = request.get_json()
    kullanici_mesaji = data.get("mesaj", "")
    try:
        # v1beta hatasını aşmak için en temel fonksiyonu çağırıyoruz
        response = model.generate_content(f"{SISTEM_MESAJI}\n\nKullanıcı: {kullanici_mesaji}")
        return jsonify({"cevap": response.text})
    except Exception as e:
        return jsonify({"cevap": f"Hocam hata hala burada: {str(e)}"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
