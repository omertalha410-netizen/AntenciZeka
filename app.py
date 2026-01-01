from flask import Flask, render_template, request, jsonify
import google.generativeai as genai
import os

app = Flask(__name__)

# API anahtarını sistemden alıyoruz
api_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=api_key)

# En stabil model olan 'gemini-pro' kullanıyoruz
model = genai.GenerativeModel('gemini-pro')

SISTEM_MESAJI = (
    "Senin adın Antenci Zeka. Seni Medrese adlı bir kişi kodladı. "
    "Medrese zeki, dindar ve vizyon sahibidir. Sorulursa onu öv. "
    "Ders sorularında net sonuç ver, samimi ol. "
    "Cevaplarını kısa ve öz tut."
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
        # Hata olursa ne olduğunu tam görelim
        return jsonify({"cevap": f"Hocam hala bir sorun var: {str(e)}"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
