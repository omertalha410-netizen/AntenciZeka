from flask import Flask, render_template, request, jsonify, session, url_for, redirect
from werkzeug.middleware.proxy_fix import ProxyFix
import os
import requests
import io
import pypdf
from google import genai # Yeni google-genai SDK'sı
from authlib.integrations.flask_client import OAuth

app = Flask(__name__)

# Vercel HTTPS ve Proxy ayarları 
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
app.secret_key = os.getenv("SECRET_KEY", "antenci_gizli_anahtar_99")

# API Anahtarları
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

# Videoda gördüğün yeni nesil Gemini Client yapılandırması
client_gemini = genai.Client(api_key=GEMINI_API_KEY)

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
        return jsonify({"hata": "Dosya seçilmedi"}), 400
    
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
            return jsonify({"durum": "basarili", "mesaj": "PDF analize hazır."})
        except Exception:
            return jsonify({"hata": "PDF okunurken bir sorun oluştu"}), 500
    
    return jsonify({"hata": "Lütfen bir PDF dosyası yükleyin"}), 400

@app.route('/mesaj', methods=['POST'])
def mesaj():
    data = request.get_json()
    user_msg = data.get("mesaj", "")
    secili_model = data.get("model", "llama")
    history = session.get('history', [])
    pdf_context = session.get('pdf_context', None)

    # --- ANTENCİ ZEKA GÜNCEL SİSTEM TALİMATLARI ---
    # Hocam, Kral, Reis vb. hitaplar tamamen kaldırıldı.
    # Belge yoksa belgeden bahsedilmeyecek.
    base_instructions = (
        "Sen 'Antenci Zeka'sın. Medrese Ekibi tarafından geliştirildin.\n"
        "KURALLAR:\n"
        "1. Kullanıcıya hitap ederken KESİNLİKLE 'Hocam', 'Kral', 'Reis', 'Usta', 'Abi' gibi kelimeler kullanma. Direkt konuya gir.\n"
        "2. Eğer yüklü bir belge/PDF yoksa, belgeden veya dökümandan asla bahsetme.\n"
        "3. Eğer bir belge yüklüyse, soruları o belgedeki bilgilere dayanarak cevapla.\n"
        "4. Sade, samimi ve net bir Türkçe kullan."
    )

    if pdf_context:
        full_context_prompt = f"{base_instructions}\n\nKAYNAK DOKÜMAN:\n{pdf_context}\n\nKullanıcı: {user_msg}"
    else:
        full_context_prompt = f"{base_instructions}\n\nKullanıcı: {user_msg}"

    # --- GEMINI 1.5 FLASH (YENİ SDK) ---
    if secili_model == "gemini":
        try:
            response = client_gemini.models.generate_content(
                model="gemini-1.5-flash",
                contents=full_context_prompt
            )
            cevap = response.text
        except Exception:
            cevap = "Şu an Gemini modeline ulaşılamıyor, lütfen tekrar deneyin."

    # --- LLAMA 3.3 (GROQ) ---
    else:
        messages = [{"role": "system", "content": base_instructions}]
        if pdf_context:
            messages.append({"role": "system", "content": f"Belge İçeriği: {pdf_context}"})
        
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
                cevap = "Sistem şu an yanıt veremiyor, lütfen birazdan tekrar deneyin."
        except Exception:
            cevap = "Bağlantı hatası oluştu, lütfen internetinizi kontrol edin."

    # Kayıt
    history.append({"role": "user", "content": user_msg})
    history.append({"role": "assistant", "content": cevap})
    session['history'] = history[-10:] 
    
    return jsonify({"cevap": cevap})

if __name__ == "__main__":
    app.run()
