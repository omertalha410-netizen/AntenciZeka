from flask import Flask, render_template, request, jsonify, session, url_for, redirect
from werkzeug.middleware.proxy_fix import ProxyFix
import os
import requests
import io
import pypdf
import google.generativeai as genai
from authlib.integrations.flask_client import OAuth

app = Flask(__name__)

# Vercel HTTPS ve Proxy ayarları 
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
app.secret_key = os.getenv("SECRET_KEY", "antenci_gizli_anahtar_99")

# API Anahtarları
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

# Gemini Konfigürasyonu
genai.configure(api_key=GEMINI_API_KEY)

# --- GOOGLE OAUTH AYARLARI ---
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
            
            session['pdf_context'] = text[:15000] 
            return jsonify({"durum": "basarili", "mesaj": "PDF okundu, kral!"})
        except Exception as e:
            return jsonify({"hata": "PDF okunurken hata oluştu"}), 500
    
    return jsonify({"hata": "Sadece PDF yükleyebilirsin kral"}), 400

@app.route('/mesaj', methods=['POST'])
def mesaj():
    data = request.get_json()
    user_msg = data.get("mesaj", "")
    secili_model = data.get("model", "llama")
    history = session.get('history', [])
    pdf_context = session.get('pdf_context', None)

    # --- ANTENCİ ZEKA SİSTEM TALİMATLARI ---
    base_instructions = (
        "Sen 'Antenci Zeka'sın. Medrese Ekibi tarafından geliştirilen samimi bir yapay zekasın.\n"
        "KURALLAR:\n"
        "1. KESİNLİKLE 'Hocam' kelimesini kullanma. Hitapların: 'Kral', 'Reis', 'Usta', 'Hacı', 'Kanka', 'Abi'.\n"
        "2. Üslubun çok samimi, içten ve mahalle arkadaşı gibi olsun. Robotik konuşma.\n"
        "3. Eğer aşağıda bir döküman içeriği varsa ve soru dökümanla ilgiliyse dökümanı kullan. Yoksa normal sohbete devam et.\n"
        "4. Döküman yoksa durduk yere dökümandan bahsetme.\n"
    )

    if pdf_context:
        system_instructions = base_instructions + f"\nKAYNAK DOKÜMAN:\n{pdf_context}"
    else:
        system_instructions = base_instructions

    # --- GEMINI 1.5 FLASH ---
    if secili_model == "gemini":
        try:
            model = genai.GenerativeModel('gemini-1.5-flash')
            full_prompt = f"Sistem Talimatı: {system_instructions}\n\nKullanıcı: {user_msg}"
            response = model.generate_content(full_prompt)
            cevap = response.text
        except Exception:
            cevap = "Gemini hattında bir parazit var kral, tekrar dener misin?"

    # --- LLAMA 3.3 (GROQ) ---
    else:
        messages = [{"role": "system", "content": system_instructions}]
        for msg in history:
            messages.append(msg)
        messages.append({"role": "user", "content": user_msg})

        try:
            response = requests.post(GROQ_API_URL, headers={"Authorization": f"Bearer {GROQ_API_KEY}"}, json={
                "model": "llama-3.3-70b-versatile",
                "messages": messages,
                "temperature": 0.7 
            }, timeout=15)
            
            if response.status_code == 200:
                cevap = response.json()['choices'][0]['message']['content']
            else:
                cevap = "Llama şu an uykuda herhalde kral, tekrar dener misin?"
        except Exception:
            cevap = "Bağlantı koptu kral, Groq hattı meşgul herhalde."

    # Kayıt
    history.append({"role": "user", "content": user_msg})
    history.append({"role": "assistant", "content": cevap})
    session['history'] = history[-10:] 
    
    return jsonify({"cevap": cevap})

if __name__ == "__main__":
    app.run()
