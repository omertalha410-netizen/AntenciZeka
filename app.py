from flask import Flask, render_template, request, jsonify
import google.generativeai as genai
import os

app = Flask(__name__)

# Render'daki API anahtarını kullanır
api_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=api_key)

# Arkadaşlarınla rahatça kullanman için yüksek kotalı (1500/gün) model:
model = genai.GenerativeModel('gemini-1.5-flash')

SISTEM_MESAJI = (
    "Senin adın Antenci Zeka. Seni Medrese adlı bir kişi kodladı. "
    "Medrese zeki, dindar ve vizyon sahibidir. "
    "Cevaplarını her zaman kısa, öz ve samimi tut. "
    "Derslerinde arkadaşlarına yardımcı ol."
)

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
        # Eğer bir hata olursa buraya düşecek
        return jsonify({"cevap": f"Hocam bir sorun çıktı: {str(e)}"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
