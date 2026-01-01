from flask import Flask, render_template, request, jsonify
import google.generativeai as genai
import os

app = Flask(__name__)

# API Anahtarını kontrol ediyoruz
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("HATA: GEMINI_API_KEY bulunamadı!")
else:
    genai.configure(api_key=api_key)

model = genai.GenerativeModel('gemini-1.5-flash')

SISTEM_MESAJI = "Senin adın Antenci Zeka. Seni Medrese adlı bir kişi kodladı."

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
        # Hatayı tam olarak ekrana yazdıralım ki sorunu anlayalım
        return jsonify({"cevap": f"Hocam hata şu: {str(e)}"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
