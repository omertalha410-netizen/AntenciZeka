from flask import Flask, render_template, request, jsonify
import google.generativeai as genai
import os

app = Flask(__name__)

# DİKKAT: Buraya o yeni aldığın AIza... ile başlayan anahtarı TIRNAK İÇİNE yapıştır
# Örnek: genai.configure(api_key="AIzaSyA123...")
genai.configure(api_key="AIzaSyDCLdoBxAhmfWRWG2HO2Kg8c8e3h97Qjz0")

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
        return jsonify({"cevap": f"Hocam hata hala burada: {str(e)}"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
