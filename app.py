from flask import Flask, render_template, request, jsonify
import google.generativeai as genai
import os

app = Flask(__name__)

# Render'daki Environment Variables kısmından anahtarı çeker
api_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=api_key)

# Yeni projelerle en iyi çalışan güncel model
model = genai.GenerativeModel('gemini-1.5-flash')

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
        # Eğer yine hata verirse hatanın ne olduğunu ekrana yazar
        return jsonify({"cevap": f"Hocam hata devam ediyor: {str(e)}"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
