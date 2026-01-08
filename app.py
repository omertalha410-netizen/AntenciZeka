from flask import Flask, render_template, request, jsonify, session, url_for, redirect
import os
import requests
from authlib.integrations.flask_client import OAuth

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "antenci_gizli_anahtar_99")

# --- GOOGLE OAUTH AYARLARI ---
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

@app.route('/mesaj', methods=['POST'])
def mesaj():
    data = request.get_json()
    user_msg = data.get("mesaj", "")
    history = session.get('history', [])

    # DİL VE HİTAP FİLTRESİ
    system_instructions = (
        "Sen 'Antenci Zeka'sın. Medrese Ekibi tarafından geliştirildim. "
        "Sadece TÜRKÇE cevap ver. Asla yabancı karakter veya Çince kullanma. "
        "Kullanıcıya sürekli 'Hocam' deme, sadece doğal akışta nadiren kullan. "
        "Derslerde ciddi (MEB/EBA), sohbette samimi ol."
    )

    messages = [{"role": "system", "content": system_instructions}]
    for msg in history:
        messages.append(msg)
    messages.append({"role": "user", "content": user_msg})

    try:
        response = requests.post(GROQ_API_URL, headers={"Authorization": f"Bearer {GROQ_API_KEY}"}, json={
            "model": "llama-3.3-70b-versatile",
            "messages": messages,
            "temperature": 0.5
        }, timeout=10)
        cevap = response.json()['choices'][0]['message']['content']
        
        history.append({"role": "user", "content": user_msg})
        history.append({"role": "assistant", "content": cevap})
        session['history'] = history[-10:]
        
        return jsonify({"cevap": cevap})
    except Exception:
        return jsonify({"cevap": "Hocam bir hata oluştu."})

if __name__ == "__main__":
    app.run()
