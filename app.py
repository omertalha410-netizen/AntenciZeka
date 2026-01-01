from flask import Flask, render_template, request, jsonify, url_for, redirect, session
import google.generativeai as genai
import os
from authlib.integrations.flask_client import OAuth

app = Flask(__name__)
app.secret_key = "antenci_zekanin_gizli_anahtari"

# --- HOCAM GOOGLE'DAN ALDIĞIN KODLARI BURAYA YAPIŞTIR ---
GOOGLE_CLIENT_ID = "876789867408-lfnjl3neiqa0f842qfhsm0fl2u0pq54l.apps.googleusercontent.com" # Resimdeki kimlik
GOOGLE_CLIENT_SECRET = "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" # Resimdeki sır
PATRON_EMAIL = "senin-mail-adresin@gmail.com" # Kendi mailini buraya yaz hocam!
# -------------------------------------------------------

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("models/gemini-2.5-flash-lite")

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
    redirect_uri = url_for('auth', _external=True)
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
    msg = data.get("mesaj", "")
    email = session.get('user', {}).get('email')
    
    if email == PATRON_EMAIL:"omertalha410@gmail.com"
        limit = 9999
    elif email:
        limit = 80
    else:
        email = request.remote_addr
        limit = 50
        
    usage = user_quotas.get(email, 0)
    if usage >= limit:
        return jsonify({"cevap": "Hocam kotan doldu! Gmail ile girersen 80 hak alırsın."})

    try:
        response = model.generate_content(f"Sen Antenci Zeka'sın. Samimi bir üslupla cevap ver. \n\nKullanıcı: {msg}")
        user_quotas[email] = usage + 1
        return jsonify({"cevap": response.text})
    except Exception as e:
        return jsonify({"cevap": f"Hata: {str(e)}"})

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
