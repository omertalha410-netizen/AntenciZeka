from flask import Flask, render_template, request, jsonify, url_for, redirect, session
import google.generativeai as genai
import os
from authlib.integrations.flask_client import OAuth

app = Flask(__name__)
app.secret_key = "antenci_v2026_final"

# --- AYARLAR ---
# Render Environment sekmesinden gelen anahtar
API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=API_KEY)

GOOGLE_CLIENT_ID = "876789867408-lfnjl3neiqa0f842qfhsm0fl2u0pq54l.apps.googleusercontent.com"
GOOGLE_CLIENT_SECRET = "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"
PATRON_EMAIL = "omertalha410@gmail.com"

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
    
    # --- KOTA SİSTEMİ ---
    if email == PATRON_EMAIL:
        limit = 999999
    elif email:
        limit = 80
    else:
        email = request.remote_addr
        limit = 50
        
    usage = user_quotas.get(email, 0)
    if usage >= limit:
        return jsonify({"cevap": f"Hocam kotan doldu ({limit})."})

    try:
        # SENİN LİSTENDEN EN GÜNCEL MODELİ SEÇTİK: gemini-2.5-flash
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content(user_msg)
        
        user_quotas[email] = usage + 1
        return jsonify({"cevap": response.text})

    except Exception as e:
        # Eğer yine nazlanırsa listedeki 'gemini-flash-latest'ı deniyoruz
        try:
            model_alt = genai.GenerativeModel('gemini-flash-latest')
            response_alt = model_alt.generate_content(user_msg)
            return jsonify({"cevap": response_alt.text})
        except:
            return jsonify({"cevap": f"Hocam listedeki modelleri zorluyorum. Hata: {str(e)}"})

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
