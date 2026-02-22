from flask import Flask, render_template, request, jsonify, session, url_for, redirect
from werkzeug.middleware.proxy_fix import ProxyFix
import os
import requests
import io
import pypdf
from authlib.integrations.flask_client import OAuth

app = Flask(__name__)

# Vercel HTTPS ve Proxy ayarları 
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
app.secret_key = os.getenv("SECRET_KEY", "antenci_gizli_anahtar_99")

# --- GOOGLE OAUTH AYARLARI  ---
oauth = OAuth(app)
google = oauth.register(
    name='google',
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'}
)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login')
def login():
    redirect_uri = url_for('auth', _external=True)
    return google.authorize_redirect(redirect_uri)

@app.route('/auth')
def auth():
    token = google.authorize_access_token()
    user = google.get('https://openidconnect.googleapis.com/v1/userinfo').json()
    session['user'] = user
    return redirect('/')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

# --- PDF YÜKLEME VE OKUMA ---
@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return jsonify({"hata": "Dosya seçilmedi kral"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"hata": "Dosya ismi boş"}), 400

    if file and file.filename.endswith('.pdf'):
        try:
            pdf_reader = pypdf.PdfReader(file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() or ""
            
            # PDF içeriğini oturuma kaydet (Not: Çok büyük PDF'lerde session limiti aşılabilir)
            session['pdf_context'] = text[:15000] # Şimdilik ilk 15 bin karakter
            return jsonify({"durum": "basarili", "mesaj": "PDF okundu, sorunu bekliyorum!"})
        except Exception as e:
            return jsonify({"hata": f"PDF okunurken hata oluştu: {str(e)}"}), 500
    
    return jsonify({"hata": "Sadece PDF yükleyebilirsin hocam"}), 400

@app.route('/mesaj', methods=['POST'])
def mesaj():
    data = request.get_json()
    user_msg = data.get("mesaj", "")
    history = session.get('history', [])
    pdf_context = session.get('pdf_context', None)

    # --- ANTENCİ ZEKA v2.6: DOKÜMAN ANALİZ MODU ---
    context_prompt = ""
    if pdf_context:
        context_prompt = f"\n\nKULLANICININ YÜKLEDİĞİ DOKÜMAN İÇERİĞİ:\n{pdf_context}\n\nLütfen soruları bu dokümana göre cevapla."

    system_instructions = (
        "Sen 'Antenci Zeka'sın. Bir doküman analiz asistanısın. \n"
        "GÖREVLERİN:\n"
        "1. Eğer aşağıda bir doküman içeriği varsa, kullanıcı sorularını BU DOKÜMANA GÖRE cevapla.\n"
        "2. Dokümanda olmayan bilgi için 'Bu bilgi dokümanda yer almıyor kral' de.\n"
        "3. Üslubun samimi olsun; 'Kral', 'Hocam', 'Reis' hitaplarını kullan. \n"
        "4. Net ve Türkçe cevap ver. "
    ) + context_prompt

    messages = [{"role": "system", "content": system_instructions}]
    for msg in history:
        messages.append(msg)
    messages.append({"role": "user", "content": user_msg})

    try:
        response = requests.post(GROQ_API_URL, headers={"Authorization": f"Bearer {GROQ_API_KEY}"}, json={
            "model": "llama-3.3-70b-versatile",
            "messages": messages,
            "temperature": 0.5 
        }, timeout=15)
        
        if response.status_code == 200:
            cevap = response.json()['choices'][0]['message']['content']
            history.append({"role": "user", "content": user_msg})
            history.append({"role": "assistant", "content": cevap})
            session['history'] = history[-6:] # Hafızayı taze tut
            return jsonify({"cevap": cevap})
        return jsonify({"cevap": "Hocam Groq hattında bir parazit var, tekrar dene."})
            
    except Exception as e:
        return jsonify({"cevap": "Bağlantı koptu kral, PDF çok büyük olabilir mi?"})

if __name__ == "__main__":
    app.run()
