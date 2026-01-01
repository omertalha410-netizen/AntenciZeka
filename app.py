from flask import Flask, render_template, request, jsonify, url_for, redirect, session
import google.generativeai as genai
import os
from authlib.integrations.flask_client import OAuth

app = Flask(__name__)
app.secret_key = "antenci_zekanin_gizli_anahtari_99"

# --- GOOGLE AYARLARI ---
GOOGLE_CLIENT_ID = "876789867408-lfnjl3neiqa0f842qfhsm0fl2u0pq54l.apps.googleusercontent.com"
GOOGLE_CLIENT_SECRET = "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"
PATRON_EMAIL = "omertalha410@gmail.com" # Mailini resimden gördüm, ekledim hocam!
# ----------------------

# Gemini Kurulumu - MODEL ADINI GÜNCELLEDİM
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-1.5-flash-latest")

# Google Login Kurulumu
oauth = OAuth(app)
google = oauth.register(
    name='google',
    client_id=GOOGLE_CLIENT_ID,
    client_secret=GOOGLE_CLIENT_SECRET,
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'}
)

user_quotas = {}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login')
def login():
    # HATAYI ÖNLEMEK İÇİN ADRESİ ELLE SABİTLEDİK
    redirect_uri = "https://antencizeka.onrender.com/login/callback"
    return google.authorize_redirect(redirect_uri)

@app.route('/login/callback')
def auth():
    token = google.authorize_access_token()
    user_info = google.parse_id_token(token, nonce=None)
    session['user'] = user_info
    return redirect('/')

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect('/')

@app.route('/mesaj', methods=['POST'])
def mesaj():
    data = request.get_json()
    user_msg = data.get("mesaj", "")
    email = session.get('user', {}).get('email')
    
    if email == PATRON_EMAIL:
        limit = 999999
    elif email:
        limit = 80
    else:
        email = request.remote_addr
        limit = 50
        
    usage = user_quotas.get(email, 0)
    if usage >= limit:
        return jsonify({"cevap": f"Hocam kotan doldu ({limit}). Gmail ile giriş yaparsan hakların yenilenir!"})

    try:
        chat_prompt = f"Senin adın Antenci Zeka. Seni Medrese kodladı. Samimi ol. \nKullanıcı: {user_msg}"
        response = model.generate_content(chat_prompt)
        user_quotas[email] = usage + 1
        return jsonify({"cevap": response.text})
    except Exception as e:
        return jsonify({"cevap": f"Hata oluştu hocam: {str(e)}"})
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
