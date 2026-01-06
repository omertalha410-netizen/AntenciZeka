from flask import Flask, render_template, request, jsonify, session, redirect
import os
import requests
from authlib.integrations.flask_client import OAuth

app = Flask(__name__)
app.secret_key = "antenci_zeka_llama_v1"

# --- CONFIG ---
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

# Google Login (İstersen kalsın, istersen kaldırabiliriz hocam)
GOOGLE_CLIENT_ID = "876789867408-lfnjl3neiqa0f842qfhsm0fl2u0pq54l.apps.googleusercontent.com"
GOOGLE_CLIENT_SECRET = "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"
oauth = OAuth(app)
google = oauth.register(
    name='google',
    client_id=GOOGLE_CLIENT_ID,
    client_secret=GOOGLE_CLIENT_SECRET,
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'}
)

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

@app.route('/mesaj', methods=['POST'])
def mesaj():
    data = request.get_json()
    user_msg = data.get("mesaj", "")
    
    # Llama 3.1 - 70B modelini kullanıyoruz, canavardır hocam
    payload = {
        "model": "llama-3.1-70b-versatile",
        "messages": [
            {"role": "system", "content": "Sen yardımsever bir asistansın ve kullanıcıya her zaman 'Hocam' diye hitap ediyorsun."},
            {"role": "user", "content": user_msg}
        ],
        "temperature": 0.7
    }
    
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(GROQ_API_URL, headers=headers, json=payload)
        res_json = response.json()
        
        # Groq'tan gelen cevabı alıyoruz
        if "choices" in res_json:
            cevap = res_json['choices'][0]['message']['content']
            return jsonify({"cevap": cevap})
        else:
            return jsonify({"cevap": f"Hocam bir sorun var: {res_json.get('error', {}).get('message', 'Bilinmeyen hata')}"})
            
    except Exception as e:
        return jsonify({"cevap": f"Hocam Llama sunucusuna bağlanamadım: {str(e)}"})

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
