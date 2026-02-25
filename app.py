from flask import Flask, render_template, request, jsonify, session, url_for, redirect
from werkzeug.middleware.proxy_fix import ProxyFix
import os
import requests
import io
import pypdf
from authlib.integrations.flask_client import OAuth

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
app.secret_key = os.getenv("SECRET_KEY", "antenci_gizli_anahtar_99")

# API Ayarları
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

# --- GOOGLE OAUTH ---
oauth = OAuth(app)
google = oauth.register(
    name='google',
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'}
)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return jsonify({"hata": "Dosya seçilmedi"}), 400
    file = request.files['file']
    if file and file.filename.endswith('.pdf'):
        try:
            pdf_reader = pypdf.PdfReader(file)
            text = "".join([page.extract_text() or "" for page in pdf_reader.pages])
            session['pdf_context'] = text[:15000]
            return jsonify({"durum": "basarili", "mesaj": "PDF hazır."})
        except Exception:
            return jsonify({"hata": "Okuma hatası"}), 500
    return jsonify({"hata": "Geçersiz dosya"}), 400

@app.route('/mesaj', methods=['POST'])
def mesaj():
    data = request.get_json()
    user_msg = data.get("mesaj", "")
    secili_model = data.get("model", "llama")
    pdf_context = session.get('pdf_context', None)
    history = session.get('history', [])

    # Sistem Talimatı (Hitapsız)
    system_instructions = (
        "Sen 'Antenci Zeka'sın. Medrese Ekibi tarafından geliştirildin.\n"
        "Kurallar: Hitap kullanma (Hocam, Kral vb. yasak). Belge yoksa belgeden bahsetme. "
        "Sadece soruyu cevapla."
    )

    # --- MODEL SEÇİMİ VE API ÇAĞRISI ---
    if secili_model == "openrouter":
        # Ücretsiz bir model örneği: Gemma 2 9B
        payload = {
            "model": "google/gemma-2-9b-it:free",
            "messages": [{"role": "system", "content": system_instructions}]
        }
        if pdf_context:
            payload["messages"].append({"role": "system", "content": f"Belge: {pdf_context}"})
        payload["messages"].append({"role": "user", "content": user_msg})
        
        headers = {"Authorization": f"Bearer {OPENROUTER_API_KEY}"}
        try:
            res = requests.post(OPENROUTER_URL, headers=headers, json=payload, timeout=15)
            cevap = res.json()['choices'][0]['message']['content']
        except Exception:
            cevap = "OpenRouter servisinde bir sorun oluştu."

    else: # Varsayılan: Llama (Groq)
        messages = [{"role": "system", "content": system_instructions}]
        if pdf_context:
            messages.append({"role": "system", "content": f"Belge: {pdf_context}"})
        messages.append({"role": "user", "content": user_msg})
        
        try:
            res = requests.post(GROQ_API_URL, headers={"Authorization": f"Bearer {GROQ_API_KEY}"}, json={
                "model": "llama-3.3-70b-versatile", "messages": messages
            }, timeout=15)
            cevap = res.json()['choices'][0]['message']['content']
        except Exception:
            cevap = "Sistem şu an yanıt veremiyor."

    history.append({"role": "user", "content": user_msg})
    history.append({"role": "assistant", "content": cevap})
    session['history'] = history[-10:]
    return jsonify({"cevap": cevap})

if __name__ == "__main__":
    app.run()
