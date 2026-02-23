from flask import Flask, render_template, request, jsonify, session, url_for, redirect
from werkzeug.middleware.proxy_fix import ProxyFix
import os
import requests
import io
import pypdf
try:
    from google import genai
except ImportError:
    print("HATA: google-genai kütüphanesi bulunamadı. requirements.txt dosyasını kontrol et.")
from authlib.integrations.flask_client import OAuth

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
app.secret_key = os.getenv("SECRET_KEY", "antenci_gizli_anahtar_99")

# API Anahtarları
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

# Gemini Client Başlatma (Hata kontrolü ile)
client_gemini = None
if GEMINI_API_KEY:
    try:
        client_gemini = genai.Client(api_key=GEMINI_API_KEY)
    except Exception as e:
        print(f"Gemini Client başlatılamadı: {e}")

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
            return jsonify({"durum": "basarili", "mesaj": "PDF analize hazır."})
        except Exception:
            return jsonify({"hata": "PDF okunamadı"}), 500
    return jsonify({"hata": "Sadece PDF yükleyin"}), 400

@app.route('/mesaj', methods=['POST'])
def mesaj():
    data = request.get_json()
    user_msg = data.get("mesaj", "")
    secili_model = data.get("model", "llama")
    history = session.get('history', [])
    pdf_context = session.get('pdf_context', None)

    # --- SİSTEM TALİMATI (Hitapsız) ---
    base_instructions = (
        "Sen 'Antenci Zeka'sın. Medrese Ekibi tarafından geliştirildin.\n"
        "KURALLAR:\n"
        "1. ASLA 'Hocam', 'Kral', 'Reis' gibi hitaplar kullanma. Direkt cevap ver.\n"
        "2. PDF yüklü değilse belgeden bahsetme.\n"
        "3. Belge varsa bilgiyi oradan al.\n"
    )

    full_prompt = base_instructions
    if pdf_context:
        full_prompt += f"\nKAYNAK DOKÜMAN:\n{pdf_context}"
    full_prompt += f"\nKullanıcı Mesajı: {user_msg}"

    # --- GEMINI 1.5 FLASH ---
    if secili_model == "gemini":
        if not client_gemini:
            return jsonify({"cevap": "HATA: Gemini API anahtarı eksik veya geçersiz."})
        try:
            response = client_gemini.models.generate_content(
                model="gemini-1.5-flash",
                contents=full_prompt
            )
            cevap = response.text
        except Exception as e:
            print(f"Gemini API Hatası: {e}")
            cevap = f"Gemini şu an yanıt veremiyor. (Hata: {str(e)[:50]}...)"

    # --- LLAMA 3.3 (GROQ) ---
    else:
        messages = [{"role": "system", "content": base_instructions}]
        if pdf_context:
            messages.append({"role": "system", "content": f"Belge: {pdf_context}"})
        for msg in history:
            messages.append(msg)
        messages.append({"role": "user", "content": user_msg})

        try:
            res = requests.post(GROQ_API_URL, headers={"Authorization": f"Bearer {GROQ_API_KEY}"}, json={
                "model": "llama-3.3-70b-versatile", "messages": messages, "temperature": 0.7
            }, timeout=15)
            cevap = res.json()['choices'][0]['message']['content']
        except Exception:
            cevap = "Llama şu an uykuda, tekrar dener misin?"

    history.append({"role": "user", "content": user_msg})
    history.append({"role": "assistant", "content": cevap})
    session['history'] = history[-10:]
    return jsonify({"cevap": cevap})

if __name__ == "__main__":
    app.run()
