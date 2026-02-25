from flask import Flask, render_template, request, jsonify, session, url_for, redirect
from werkzeug.middleware.proxy_fix import ProxyFix
import os
import requests
import io
import pypdf
from google import genai  # Yeni SDK
from authlib.integrations.flask_client import OAuth

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
app.secret_key = os.getenv("SECRET_KEY", "antenci_gizli_anahtar_99")

# API Ayarları
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

# Yeni Gemini Client yapısı
client_gemini = genai.Client(api_key=GEMINI_API_KEY)

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
            return jsonify({"hata": "PDF okunurken sorun oluştu"}), 500
    return jsonify({"hata": "Sadece PDF kabul edilir"}), 400

@app.route('/mesaj', methods=['POST'])
def mesaj():
    data = request.get_json()
    user_msg = data.get("mesaj", "")
    secili_model = data.get("model", "llama")
    history = session.get('history', [])
    pdf_context = session.get('pdf_context', None)

    # --- SİSTEM TALİMATI (Hitapsız ve Akıllı) ---
    system_instructions = (
        "Sen 'Antenci Zeka'sın. Medrese Ekibi tarafından geliştirildin.\n"
        "KESİN KURALLAR:\n"
        "1. Kullanıcıya ASLA 'Hocam', 'Kral', 'Reis', 'Usta', 'Abi' gibi hitaplar kullanma. Direkt konuya gir.\n"
        "2. Eğer yüklü bir belge/PDF yoksa, belgeden veya dökümandan asla bahsetme. Sadece sorulan soruya odaklan.\n"
        "3. Eğer bir belge yüklüyse, cevaplarını o belgedeki bilgilere dayandır.\n"
        "4. Sade ve net bir Türkçe kullan."
    )

    # --- GEMINI 1.5 FLASH (404 Hatası Çözümü İçin Güncellendi) ---
    if secili_model == "gemini":
        try:
            # Not: 404 alıyorsan model ismini 'gemini-1.5-flash' veya videodaki gibi 'gemini-2.0-flash-preview' olarak deneyebilirsin.
            response = client_gemini.models.generate_content(
                model="gemini-1.5-flash", 
                contents=f"{system_instructions}\n\nBelge İçeriği: {pdf_context if pdf_context else 'Yok'}\n\nKullanıcı: {user_msg}"
            )
            cevap = response.text
        except Exception as e:
            print(f"Gemini Hatası: {e}")
            cevap = "Gemini şu an yanıt veremiyor, model ismi veya API anahtarı geçersiz olabilir."

    # --- LLAMA 3.3 (GROQ) ---
    else:
        messages = [{"role": "system", "content": system_instructions}]
        if pdf_context:
            messages.append({"role": "system", "content": f"Belge içeriği: {pdf_context}"})
        for msg in history:
            messages.append(msg)
        messages.append({"role": "user", "content": user_msg})
        
        try:
            res = requests.post(GROQ_API_URL, headers={"Authorization": f"Bearer {GROQ_API_KEY}"}, json={
                "model": "llama-3.3-70b-versatile",
                "messages": messages,
                "temperature": 0.7
            }, timeout=15)
            cevap = res.json()['choices'][0]['message']['content']
        except Exception:
            cevap = "Sistem şu an meşgul, lütfen tekrar deneyin."

    history.append({"role": "user", "content": user_msg})
    history.append({"role": "assistant", "content": cevap})
    session['history'] = history[-10:]
    
    return jsonify({"cevap": cevap})

if __name__ == "__main__":
    app.run()
