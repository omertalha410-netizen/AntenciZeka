from flask import Flask, render_template, request, jsonify
import google.generativeai as genai
import os

app = Flask(__name__)

# API anahtarı
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# HOCAM: İsmi en yalın haliyle yazıyoruz.
SECILEN_MODEL = "gemini-1.5-flash"
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
        # Deneme yapıyoruz
        response = model.generate_content(f"{SISTEM_MESAJI}\n\nKullanıcı: {kullanici_mesaji}")
        return jsonify({"cevap": response.text})
    except Exception as e:
        # HATA ALIRSAK: Google'ın senin için izin verdiği tüm isimleri buraya yazdıracak
        try:
            mevcut_modeller = [m.name for m in genai.list_models()]
            return jsonify({"cevap": f"Hocam bu model olmadı. Ama senin anahtarınla şu modelleri kullanabiliriz: {mevcut_modeller}. Hata mesajı ise: {str(e)}"})
        except:
            return jsonify({"cevap": f"Hocam tamamen kilitlendik: {str(e)}"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
